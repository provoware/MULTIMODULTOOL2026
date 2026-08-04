"""Sicherer Linux-Single-Instance-Schutz für MULTIMODULTOOL2026.

Die Koordination verwendet ausschließlich einen privaten Unix-Domain-Socket im
XDG-Laufzeitverzeichnis. Es werden nur streng validierte Aktivierungsnachrichten
übertragen; Dateipfade, freie Argumentlisten und private Inhalte sind verboten.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import errno
import json
import os
from pathlib import Path
import queue
import re
import socket
import stat
import struct
import threading
from typing import Mapping

APP_RUNTIME_NAME = "multimodultool2026"
SOCKET_FILE_NAME = "instance.sock"
METADATA_FILE_NAME = "instance.json"
RUNTIME_DIRECTORY_MODE = 0o700
METADATA_FILE_MODE = 0o600
MAX_MESSAGE_BYTES = 4096
MESSAGE_SCHEMA_VERSION = 1
_ALLOWED_ACTIONS = frozenset({"activate", "show-diagnostics"})
_ALLOWED_MESSAGE_KEYS = frozenset({"schemaVersion", "action", "diagnosticId"})
_DIAGNOSTIC_ID_PATTERN = re.compile(r"^MMT-[A-Z0-9-]{3,80}$")


@dataclass(frozen=True)
class LaunchRequest:
    """Einzige zulässige Nachricht zwischen zwei lokalen App-Starts."""

    action: str = "activate"
    diagnostic_id: str = ""

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schemaVersion": MESSAGE_SCHEMA_VERSION,
            "action": self.action,
        }
        if self.diagnostic_id:
            payload["diagnosticId"] = self.diagnostic_id
        return payload


@dataclass(frozen=True)
class InstancePaths:
    runtime_root: Path
    app_directory: Path
    socket_path: Path
    metadata_path: Path


@dataclass(frozen=True)
class InstanceResult:
    role: str
    message: str
    paths: InstancePaths | None = None
    recovered_stale: bool = False
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_primary(self) -> bool:
        return self.role == "primary"

    @property
    def is_secondary(self) -> bool:
        return self.role == "secondary"

    @property
    def is_blocked(self) -> bool:
        return self.role == "blocked"


class InstanceSecurityError(RuntimeError):
    """Sicherheitsrelevanter Laufzeit-, Sperr- oder Nachrichtenfehler."""


def _current_uid() -> int:
    if not hasattr(os, "getuid"):
        raise InstanceSecurityError("Linux-Benutzerkennung ist nicht verfügbar.")
    return os.getuid()


def _boot_id() -> str:
    try:
        value = Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip()
    except (OSError, UnicodeError):
        return "unavailable"
    return value[:80] or "unavailable"


def _pid_is_alive(pid: int) -> bool:
    if pid <= 1:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def resolve_runtime_root(
    environ: Mapping[str, str] | None = None,
    *,
    uid: int | None = None,
) -> Path:
    """Sicheres XDG-Laufzeitverzeichnis bestimmen, ohne etwas anzulegen."""

    environment = os.environ if environ is None else environ
    current_uid = _current_uid() if uid is None else uid
    configured = (environment.get("XDG_RUNTIME_DIR") or "").strip()
    candidates: list[Path] = []
    if configured:
        candidates.append(Path(configured).expanduser())
    candidates.append(Path("/run/user") / str(current_uid))

    problems: list[str] = []
    for candidate in candidates:
        try:
            validate_runtime_root(candidate, uid=current_uid)
        except InstanceSecurityError as exc:
            problems.append(str(exc))
            continue
        return candidate
    detail = "; ".join(dict.fromkeys(problems)) or "kein Laufzeitpfad vorhanden"
    raise InstanceSecurityError(
        "Kein sicheres XDG-Laufzeitverzeichnis verfügbar. " + detail
    )


def validate_runtime_root(path: Path, *, uid: int | None = None) -> None:
    current_uid = _current_uid() if uid is None else uid
    candidate = path.expanduser()
    if not candidate.is_absolute():
        raise InstanceSecurityError(f"Laufzeitpfad ist nicht absolut: {candidate}")
    if candidate.is_symlink():
        raise InstanceSecurityError(f"Laufzeitpfad darf kein Symlink sein: {candidate}")
    try:
        metadata = candidate.lstat()
    except FileNotFoundError as exc:
        raise InstanceSecurityError(f"Laufzeitpfad fehlt: {candidate}") from exc
    except OSError as exc:
        raise InstanceSecurityError(f"Laufzeitpfad kann nicht geprüft werden: {exc}") from exc
    if not stat.S_ISDIR(metadata.st_mode):
        raise InstanceSecurityError(f"Laufzeitpfad ist kein Verzeichnis: {candidate}")
    if metadata.st_uid != current_uid:
        raise InstanceSecurityError("Laufzeitpfad gehört nicht dem aktuellen Linux-Nutzer.")
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise InstanceSecurityError("Laufzeitpfad ist zu offen; erforderlich ist 0700.")
    if not os.access(candidate, os.W_OK | os.X_OK):
        raise InstanceSecurityError("Laufzeitpfad ist nicht beschreibbar.")


def instance_paths(runtime_root: Path) -> InstancePaths:
    root = runtime_root.expanduser()
    app_directory = root / APP_RUNTIME_NAME
    return InstancePaths(
        runtime_root=root,
        app_directory=app_directory,
        socket_path=app_directory / SOCKET_FILE_NAME,
        metadata_path=app_directory / METADATA_FILE_NAME,
    )


def validate_launch_request(value: object) -> LaunchRequest:
    if not isinstance(value, dict):
        raise InstanceSecurityError("Startnachricht muss ein JSON-Objekt sein.")
    unknown = sorted(set(value) - _ALLOWED_MESSAGE_KEYS)
    if unknown:
        raise InstanceSecurityError(
            "Startnachricht enthält unzulässige Felder: " + ", ".join(unknown)
        )
    if value.get("schemaVersion") != MESSAGE_SCHEMA_VERSION:
        raise InstanceSecurityError("Startnachricht verwendet eine unbekannte Version.")
    action = value.get("action")
    if not isinstance(action, str) or action not in _ALLOWED_ACTIONS:
        raise InstanceSecurityError("Startnachricht enthält keine erlaubte Aktion.")
    diagnostic_id = value.get("diagnosticId", "")
    if not isinstance(diagnostic_id, str):
        raise InstanceSecurityError("Diagnosekennung muss Text sein.")
    diagnostic_id = diagnostic_id.strip().upper()
    if diagnostic_id and not _DIAGNOSTIC_ID_PATTERN.fullmatch(diagnostic_id):
        raise InstanceSecurityError("Diagnosekennung besitzt ein ungültiges Format.")
    if action == "activate" and diagnostic_id:
        raise InstanceSecurityError(
            "Eine reine Aktivierungsnachricht darf keine Diagnosekennung enthalten."
        )
    return LaunchRequest(action=action, diagnostic_id=diagnostic_id)


def _safe_lstat_regular(path: Path, *, mode: int, label: str, uid: int) -> os.stat_result:
    if path.is_symlink():
        raise InstanceSecurityError(f"{label} darf kein Symlink sein.")
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise InstanceSecurityError(f"{label} kann nicht geprüft werden: {exc}") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise InstanceSecurityError(f"{label} ist keine reguläre Datei.")
    if metadata.st_uid != uid:
        raise InstanceSecurityError(f"{label} gehört nicht dem aktuellen Linux-Nutzer.")
    if metadata.st_nlink != 1:
        raise InstanceSecurityError(f"{label} besitzt zusätzliche Hardlinks.")
    if stat.S_IMODE(metadata.st_mode) & ~mode:
        raise InstanceSecurityError(f"{label} ist zu offen; erforderlich ist {mode:04o}.")
    return metadata


def _validate_app_directory(path: Path, *, uid: int) -> None:
    if path.is_symlink():
        raise InstanceSecurityError("App-Laufzeitverzeichnis darf kein Symlink sein.")
    metadata = path.lstat()
    if not stat.S_ISDIR(metadata.st_mode):
        raise InstanceSecurityError("App-Laufzeitziel ist kein Verzeichnis.")
    if metadata.st_uid != uid:
        raise InstanceSecurityError("App-Laufzeitverzeichnis gehört nicht dem aktuellen Nutzer.")
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise InstanceSecurityError("App-Laufzeitverzeichnis ist zu offen; erforderlich ist 0700.")


def _prepare_app_directory(paths: InstancePaths, *, uid: int) -> None:
    validate_runtime_root(paths.runtime_root, uid=uid)
    try:
        paths.app_directory.mkdir(mode=RUNTIME_DIRECTORY_MODE, exist_ok=True)
        os.chmod(paths.app_directory, RUNTIME_DIRECTORY_MODE)
        _validate_app_directory(paths.app_directory, uid=uid)
    except (OSError, InstanceSecurityError) as exc:
        raise InstanceSecurityError(
            f"App-Laufzeitverzeichnis konnte nicht sicher vorbereitet werden: {exc}"
        ) from exc


def _write_metadata(paths: InstancePaths, *, uid: int) -> None:
    payload = {
        "schemaVersion": 1,
        "pid": os.getpid(),
        "uid": uid,
        "bootId": _boot_id(),
        "startedUtc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    temporary = paths.metadata_path.with_name(
        f".{paths.metadata_path.name}.{os.getpid()}.tmp"
    )
    descriptor: int | None = None
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        flags |= getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(temporary, flags, METADATA_FILE_MODE)
        os.fchmod(descriptor, METADATA_FILE_MODE)
        data = (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8")
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("Metadaten konnten nicht vollständig geschrieben werden.")
            view = view[written:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        os.replace(temporary, paths.metadata_path)
        os.chmod(paths.metadata_path, METADATA_FILE_MODE)
        directory_fd = os.open(
            paths.app_directory,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
        )
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)


def _read_metadata(paths: InstancePaths, *, uid: int) -> dict[str, object]:
    _safe_lstat_regular(
        paths.metadata_path,
        mode=METADATA_FILE_MODE,
        label="Instanzmetadaten",
        uid=uid,
    )
    try:
        value = json.loads(paths.metadata_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InstanceSecurityError(f"Instanzmetadaten sind beschädigt: {exc}") from exc
    if not isinstance(value, dict):
        raise InstanceSecurityError("Instanzmetadaten sind kein JSON-Objekt.")
    required = {"schemaVersion", "pid", "uid", "bootId", "startedUtc"}
    if set(value) != required or value.get("schemaVersion") != 1:
        raise InstanceSecurityError("Instanzmetadaten besitzen einen unbekannten Aufbau.")
    if value.get("uid") != uid:
        raise InstanceSecurityError("Instanzmetadaten gehören nicht zum aktuellen Nutzer.")
    pid = value.get("pid")
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 1:
        raise InstanceSecurityError("Instanzmetadaten enthalten keine gültige Prozesskennung.")
    if not isinstance(value.get("bootId"), str):
        raise InstanceSecurityError("Instanzmetadaten enthalten keine gültige Boot-Kennung.")
    return value


def _validate_socket_path(path: Path, *, uid: int) -> None:
    if path.is_symlink():
        raise InstanceSecurityError("Instanzsocket darf kein Symlink sein.")
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise InstanceSecurityError(f"Instanzsocket kann nicht geprüft werden: {exc}") from exc
    if not stat.S_ISSOCK(metadata.st_mode):
        raise InstanceSecurityError("Instanzsocket-Pfad ist kein Unix-Socket.")
    if metadata.st_uid != uid:
        raise InstanceSecurityError("Instanzsocket gehört nicht dem aktuellen Nutzer.")
    if metadata.st_nlink != 1:
        raise InstanceSecurityError("Instanzsocket besitzt zusätzliche Hardlinks.")
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise InstanceSecurityError("Instanzsocket ist zu offen; erforderlich ist 0600.")


def _encode_request(request: LaunchRequest) -> bytes:
    validated = validate_launch_request(request.as_dict())
    payload = (json.dumps(validated.as_dict(), sort_keys=True) + "\n").encode("utf-8")
    if len(payload) > MAX_MESSAGE_BYTES:
        raise InstanceSecurityError("Startnachricht überschreitet das Größenlimit.")
    return payload


def _read_message(connection: socket.socket) -> LaunchRequest:
    chunks = bytearray()
    while len(chunks) <= MAX_MESSAGE_BYTES:
        block = connection.recv(min(1024, MAX_MESSAGE_BYTES + 1 - len(chunks)))
        if not block:
            break
        chunks.extend(block)
        if b"\n" in block:
            break
    if len(chunks) > MAX_MESSAGE_BYTES:
        raise InstanceSecurityError("Startnachricht überschreitet das Größenlimit.")
    raw = bytes(chunks).split(b"\n", 1)[0]
    try:
        decoded = raw.decode("utf-8")
        value = json.loads(decoded)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise InstanceSecurityError(f"Startnachricht ist ungültig: {exc}") from exc
    return validate_launch_request(value)


def _peer_uid(connection: socket.socket) -> int:
    if not hasattr(socket, "SO_PEERCRED"):
        raise InstanceSecurityError("Linux-Peer-Credentials sind nicht verfügbar.")
    size = struct.calcsize("3i")
    credentials = connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, size)
    _pid, uid, _gid = struct.unpack("3i", credentials)
    return uid


class SingleInstanceCoordinator:
    """Bindet die primäre Instanz oder leitet eine sichere Aktivierung weiter."""

    def __init__(
        self,
        runtime_root: Path,
        *,
        uid: int | None = None,
        connect_timeout: float = 1.0,
    ) -> None:
        self.uid = _current_uid() if uid is None else uid
        self.paths = instance_paths(runtime_root)
        self.connect_timeout = max(0.1, min(connect_timeout, 5.0))
        self._server: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._messages: queue.Queue[LaunchRequest] = queue.Queue()
        self._owns_files = False
        self._recovered_stale = False

    def acquire(self, request: LaunchRequest | None = None) -> InstanceResult:
        try:
            requested = validate_launch_request((request or LaunchRequest()).as_dict())
            _prepare_app_directory(self.paths, uid=self.uid)
            _validate_socket_path(self.paths.socket_path, uid=self.uid)
        except (OSError, InstanceSecurityError) as exc:
            return InstanceResult("blocked", str(exc), self.paths)

        if self.paths.socket_path.exists():
            delivered = self._deliver_to_primary(requested)
            if delivered:
                return InstanceResult(
                    "secondary",
                    "Bestehende Instanz wurde sicher aktiviert.",
                    self.paths,
                )
            stale_result = self._recover_stale_socket()
            if stale_result.is_blocked:
                return stale_result

        try:
            self._bind_primary()
        except OSError as exc:
            if exc.errno in {errno.EADDRINUSE, errno.EACCES}:
                if self._deliver_to_primary(requested):
                    return InstanceResult(
                        "secondary",
                        "Bestehende Instanz wurde nach einer Startkollision aktiviert.",
                        self.paths,
                    )
            return InstanceResult(
                "blocked",
                f"Instanzsocket konnte nicht sicher gebunden werden: {exc}",
                self.paths,
            )
        except InstanceSecurityError as exc:
            return InstanceResult("blocked", str(exc), self.paths)

        self._start_server()
        return InstanceResult(
            "primary",
            "Primäre Linux-Instanz ist aktiv.",
            self.paths,
            recovered_stale=self._recovered_stale,
            warnings=("Eine veraltete Instanzsperre wurde sicher entfernt.",)
            if self._recovered_stale
            else (),
        )

    def _deliver_to_primary(self, request: LaunchRequest) -> bool:
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        connection.settimeout(self.connect_timeout)
        try:
            connection.connect(str(self.paths.socket_path))
            connection.sendall(_encode_request(request))
            response = connection.recv(256)
            value = json.loads(response.decode("utf-8"))
            return isinstance(value, dict) and value.get("ok") is True
        except (OSError, UnicodeError, json.JSONDecodeError, InstanceSecurityError):
            return False
        finally:
            connection.close()

    def _recover_stale_socket(self) -> InstanceResult:
        try:
            _validate_socket_path(self.paths.socket_path, uid=self.uid)
            if not self.paths.metadata_path.exists():
                raise InstanceSecurityError(
                    "Instanzsocket antwortet nicht und besitzt keine prüfbaren Metadaten."
                )
            metadata = _read_metadata(self.paths, uid=self.uid)
            pid = int(metadata["pid"])
            same_boot = metadata.get("bootId") == _boot_id()
            if same_boot and _pid_is_alive(pid):
                raise InstanceSecurityError(
                    "Die registrierte Instanz läuft noch, antwortet aber nicht. "
                    "Die Sperre wurde aus Sicherheitsgründen nicht verändert."
                )
            self.paths.socket_path.unlink()
            self.paths.metadata_path.unlink(missing_ok=True)
            self._recovered_stale = True
            return InstanceResult(
                "primary-pending",
                "Veraltete Instanzsperre wurde sicher entfernt.",
                self.paths,
                recovered_stale=True,
            )
        except (OSError, InstanceSecurityError) as exc:
            return InstanceResult(
                "blocked",
                "Instanzsperre ist beschädigt oder nicht sicher wiederherstellbar: " + str(exc),
                self.paths,
            )

    def _bind_primary(self) -> None:
        self._server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._server.settimeout(0.25)
        try:
            self._server.bind(str(self.paths.socket_path))
            os.chmod(self.paths.socket_path, 0o600)
            _validate_socket_path(self.paths.socket_path, uid=self.uid)
            self._server.listen(8)
            _write_metadata(self.paths, uid=self.uid)
            self._owns_files = True
        except BaseException:
            self._server.close()
            self._server = None
            if self.paths.socket_path.exists():
                try:
                    _validate_socket_path(self.paths.socket_path, uid=self.uid)
                    self.paths.socket_path.unlink()
                except (OSError, InstanceSecurityError):
                    pass
            raise

    def _start_server(self) -> None:
        if self._server is None:
            raise InstanceSecurityError("Primärer Instanzsocket ist nicht gebunden.")
        self._thread = threading.Thread(
            target=self._serve,
            name="mmt-single-instance",
            daemon=True,
        )
        self._thread.start()

    def _serve(self) -> None:
        assert self._server is not None
        while not self._stop.is_set():
            try:
                connection, _address = self._server.accept()
            except socket.timeout:
                continue
            except OSError:
                if self._stop.is_set():
                    return
                continue
            with connection:
                connection.settimeout(self.connect_timeout)
                try:
                    if _peer_uid(connection) != self.uid:
                        raise InstanceSecurityError(
                            "Startnachricht stammt nicht vom aktuellen Linux-Nutzer."
                        )
                    request = _read_message(connection)
                    self._messages.put(request)
                    response = {"ok": True}
                except (OSError, InstanceSecurityError) as exc:
                    response = {"ok": False, "error": str(exc)[:240]}
                try:
                    connection.sendall(json.dumps(response).encode("utf-8"))
                except OSError:
                    pass

    def drain_messages(self, *, limit: int = 20) -> tuple[LaunchRequest, ...]:
        messages: list[LaunchRequest] = []
        for _ in range(max(1, min(limit, 100))):
            try:
                messages.append(self._messages.get_nowait())
            except queue.Empty:
                break
        return tuple(messages)

    def close(self) -> None:
        self._stop.set()
        if self._server is not None:
            try:
                self._server.close()
            except OSError:
                pass
            self._server = None
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None
        if not self._owns_files:
            return
        try:
            metadata = _read_metadata(self.paths, uid=self.uid)
            owns_metadata = int(metadata["pid"]) == os.getpid()
        except (OSError, InstanceSecurityError, KeyError, ValueError):
            owns_metadata = False
        if owns_metadata:
            try:
                _validate_socket_path(self.paths.socket_path, uid=self.uid)
                self.paths.socket_path.unlink(missing_ok=True)
                self.paths.metadata_path.unlink(missing_ok=True)
            except (OSError, InstanceSecurityError):
                pass
        self._owns_files = False

    def __enter__(self) -> "SingleInstanceCoordinator":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
