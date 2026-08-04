"""Projektbezogener, atomarer und wiederherstellbarer Linux-Papierkorb.

Reguläre Dateien und Verzeichnisse werden ausschließlich per ``os.replace``
innerhalb desselben Dateisystems verschoben. Vorschau, Fingerabdruck,
Transaktions-ID und privates Manifest verhindern stilles Löschen und
unkontrolliertes Wiederherstellen.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import stat
from uuid import uuid4

from .error_events import SafeOperationError

TRASH_CONTAINER_NAME = ".multimodultool2026"
TRASH_DIRECTORY_NAME = "trash"
TRANSACTIONS_DIRECTORY_NAME = "transactions"
PAYLOAD_NAME = "payload"
MANIFEST_NAME = "manifest.json"
MANIFEST_SCHEMA_VERSION = 1
PRIVATE_DIRECTORY_MODE = 0o700
PRIVATE_FILE_MODE = 0o600
MINIMUM_METADATA_FREE_BYTES = 1024 * 1024
MAXIMUM_MANIFEST_BYTES = 256 * 1024
_TRANSACTION_ID_PATTERN = re.compile(r"^MMTTRASH-[0-9]{8}T[0-9]{6}-[A-F0-9]{12}$")
_ALLOWED_STATES = {"prepared", "trashed", "restored"}
_MANIFEST_KEYS = {
    "schemaVersion", "transactionId", "state", "createdUtc", "completedUtc",
    "restoredUtc", "originalRelativePath", "payloadRelativePath", "sourceType",
    "sourceDevice", "sourceInode", "sourceMode", "sourceSize", "sourceMtimeNs",
}


@dataclass(frozen=True)
class TrashPaths:
    project_root: Path
    control_directory: Path
    trash_root: Path
    transactions_root: Path


@dataclass(frozen=True)
class TrashPreview:
    transaction_id: str
    project_root: Path
    source_path: Path
    original_relative_path: str
    transaction_directory: Path
    payload_path: Path
    manifest_path: Path
    source_type: str
    source_device: int
    source_inode: int
    source_mode: int
    source_size: int
    source_mtime_ns: int
    available_bytes: int
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class TrashResult:
    transaction_id: str
    state: str
    manifest_path: Path
    original_path: Path
    payload_path: Path
    recovered_prepared_state: bool = False


@dataclass(frozen=True)
class TrashManifest:
    schema_version: int
    transaction_id: str
    state: str
    created_utc: str
    completed_utc: str
    restored_utc: str
    original_relative_path: str
    payload_relative_path: str
    source_type: str
    source_device: int
    source_inode: int
    source_mode: int
    source_size: int
    source_mtime_ns: int

    def as_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": self.schema_version,
            "transactionId": self.transaction_id,
            "state": self.state,
            "createdUtc": self.created_utc,
            "completedUtc": self.completed_utc,
            "restoredUtc": self.restored_utc,
            "originalRelativePath": self.original_relative_path,
            "payloadRelativePath": self.payload_relative_path,
            "sourceType": self.source_type,
            "sourceDevice": self.source_device,
            "sourceInode": self.source_inode,
            "sourceMode": self.source_mode,
            "sourceSize": self.source_size,
            "sourceMtimeNs": self.source_mtime_ns,
        }


def _fail(
    cause: str,
    *,
    consequence: str = "Die Papierkorbtransaktion wurde kontrolliert blockiert.",
    data_state: str = "Quelle, Projekt und Papierkorb blieben unverändert.",
    solution: str = "Pfad, Rechte, Mountstatus und Transaktionsdaten prüfen.",
    next_step: str = "Eine neue Vorschau erzeugen und erst nach grüner Prüfung fortfahren.",
    technical_detail: str = "",
) -> SafeOperationError:
    return SafeOperationError(
        category="project-trash",
        cause=cause,
        consequence=consequence,
        data_state=data_state,
        solution=solution,
        next_step=next_step,
        technical_detail=technical_detail,
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def create_transaction_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"MMTTRASH-{stamp}-{uuid4().hex[:12].upper()}"


def _absolute(path: Path) -> Path:
    expanded = path.expanduser()
    if not expanded.is_absolute():
        raise _fail(f"Pfad ist nicht absolut: {expanded}")
    return Path(os.path.abspath(os.fspath(expanded)))


def trash_paths(project_root: Path) -> TrashPaths:
    root = _absolute(project_root)
    control = root / TRASH_CONTAINER_NAME
    trash = control / TRASH_DIRECTORY_NAME
    return TrashPaths(root, control, trash, trash / TRANSACTIONS_DIRECTORY_NAME)


def _relative(path: Path, root: Path, *, label: str, allow_root: bool = False) -> str:
    try:
        value = path.relative_to(root)
    except ValueError as exc:
        raise _fail(f"{label} liegt außerhalb des gewählten Projekts.") from exc
    if value == Path(".") and not allow_root:
        raise _fail(
            f"{label} darf nicht der Projektstamm selbst sein.",
            data_state="Das gesamte Projekt blieb unverändert.",
        )
    return value.as_posix()


def _no_symlink_components(path: Path, root: Path, *, label: str) -> None:
    if root.is_symlink():
        raise _fail("Projektstamm darf kein Symlink sein.")
    if path == root:
        return
    relative = Path(_relative(path, root, label=label))
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise _fail(
                f"{label} enthält eine symbolische Pfadkomponente: {current.name}",
                data_state="Symlink und Linkziel blieben unverändert.",
            )


def _project_metadata(root: Path) -> os.stat_result:
    if root.is_symlink():
        raise _fail("Projektstamm darf kein Symlink sein.")
    try:
        meta = root.lstat()
    except FileNotFoundError as exc:
        raise _fail("Der gewählte Projektordner existiert nicht.") from exc
    except OSError as exc:
        raise _fail(f"Projektordner konnte nicht geprüft werden: {exc}", technical_detail=repr(exc)) from exc
    if not stat.S_ISDIR(meta.st_mode):
        raise _fail("Der Projektpfad ist kein Verzeichnis.")
    if hasattr(os, "getuid") and meta.st_uid != os.getuid():
        raise _fail("Der Projektordner gehört nicht dem aktuellen Linux-Nutzer.")
    if not os.access(root, os.W_OK | os.X_OK):
        raise _fail("Der Projektordner ist nicht sicher beschreibbar.")
    return meta


def _source_metadata(source: Path, root: Path, root_meta: os.stat_result) -> tuple[os.stat_result, str]:
    _relative(source, root, label="Quelle")
    control = root / TRASH_CONTAINER_NAME
    try:
        source.relative_to(control)
    except ValueError:
        pass
    else:
        raise _fail(
            "Objekte innerhalb des internen Papierkorbs dürfen nicht erneut verschoben werden.",
            next_step="Für diese Transaktion ausschließlich die Wiederherstellung verwenden.",
        )
    _no_symlink_components(source, root, label="Quelle")
    try:
        meta = source.lstat()
    except FileNotFoundError as exc:
        raise _fail("Die ausgewählte Quelle existiert nicht mehr.") from exc
    except OSError as exc:
        raise _fail(f"Quelle konnte nicht geprüft werden: {exc}", technical_detail=repr(exc)) from exc
    if stat.S_ISLNK(meta.st_mode):
        raise _fail("Symbolische Links sind als Papierkorbquelle nicht freigegeben.")
    if not (stat.S_ISREG(meta.st_mode) or stat.S_ISDIR(meta.st_mode)):
        raise _fail("Nur reguläre Dateien und Verzeichnisse sind freigegeben.")
    if stat.S_ISREG(meta.st_mode) and meta.st_nlink != 1:
        raise _fail("Die Datei besitzt zusätzliche Hardlinks und ist nicht eindeutig wiederherstellbar.")
    if os.path.ismount(source) or meta.st_dev != root_meta.st_dev:
        raise _fail(
            "Quelle überschreitet eine Mount- oder Dateisystemgrenze.",
            consequence="Kopieren und anschließendes Löschen wurden ausdrücklich nicht gestartet.",
        )
    if not os.access(source.parent, os.W_OK | os.X_OK):
        raise _fail("Der Quellordner erlaubt kein sicheres atomisches Umbenennen.")
    return meta, "file" if stat.S_ISREG(meta.st_mode) else "directory"


def preview_trash_move(
    project_root: Path,
    source_path: Path,
    *,
    transaction_id: str | None = None,
    minimum_free_bytes: int = MINIMUM_METADATA_FREE_BYTES,
) -> TrashPreview:
    root = _absolute(project_root)
    source = _absolute(source_path)
    root_meta = _project_metadata(root)
    meta, source_type = _source_metadata(source, root, root_meta)
    txid = (transaction_id or create_transaction_id()).strip().upper()
    if not _TRANSACTION_ID_PATTERN.fullmatch(txid):
        raise _fail("Transaktions-ID besitzt ein ungültiges Format.")
    paths = trash_paths(root)
    transaction = paths.transactions_root / txid
    if transaction.exists() or transaction.is_symlink():
        raise _fail("Die Transaktions-ID ist bereits belegt; Überschreiben wurde verhindert.")
    free = shutil.disk_usage(root).free
    if free < max(0, int(minimum_free_bytes)):
        raise _fail(f"Freier Speicher reicht nicht für sichere Metadaten aus: {free} Bytes.")
    relative = _relative(source, root, label="Quelle")
    return TrashPreview(
        transaction_id=txid,
        project_root=root,
        source_path=source,
        original_relative_path=relative,
        transaction_directory=transaction,
        payload_path=transaction / PAYLOAD_NAME,
        manifest_path=transaction / MANIFEST_NAME,
        source_type=source_type,
        source_device=meta.st_dev,
        source_inode=meta.st_ino,
        source_mode=stat.S_IMODE(meta.st_mode),
        source_size=meta.st_size,
        source_mtime_ns=meta.st_mtime_ns,
        available_bytes=free,
        warnings=("Verzeichnis wird atomar als Ganzes verschoben; Inhalte werden nicht durchlaufen.",)
        if source_type == "directory" else (),
    )


def _fingerprint(meta: os.stat_result, source_type: str) -> tuple[object, ...]:
    return (
        meta.st_dev, meta.st_ino, stat.S_IMODE(meta.st_mode), meta.st_size,
        meta.st_mtime_ns, source_type,
    )


def _validate_preview(preview: TrashPreview) -> None:
    root_meta = _project_metadata(preview.project_root)
    meta, source_type = _source_metadata(preview.source_path, preview.project_root, root_meta)
    expected = (
        preview.source_device, preview.source_inode, preview.source_mode,
        preview.source_size, preview.source_mtime_ns, preview.source_type,
    )
    if _fingerprint(meta, source_type) != expected:
        raise _fail("Die Quelle wurde seit der Vorschau verändert oder ersetzt.")
    if preview.source_device != root_meta.st_dev:
        raise _fail("Projekt und Quelle liegen nicht mehr auf demselben Dateisystem.")


def _private_directory(path: Path, *, create: bool) -> None:
    if path.is_symlink():
        raise _fail(f"Privater Papierkorbpfad darf kein Symlink sein: {path.name}")
    try:
        if create:
            path.mkdir(mode=PRIVATE_DIRECTORY_MODE, exist_ok=True)
            os.chmod(path, PRIVATE_DIRECTORY_MODE)
        meta = path.lstat()
    except FileNotFoundError as exc:
        raise _fail(f"Erwarteter Papierkorbpfad fehlt: {path.name}") from exc
    except OSError as exc:
        raise _fail(f"Papierkorbpfad konnte nicht geprüft werden: {exc}", technical_detail=repr(exc)) from exc
    if not stat.S_ISDIR(meta.st_mode):
        raise _fail(f"Papierkorbpfad ist kein Verzeichnis: {path.name}")
    if hasattr(os, "getuid") and meta.st_uid != os.getuid():
        raise _fail(f"Papierkorbpfad gehört nicht dem aktuellen Nutzer: {path.name}")
    if stat.S_IMODE(meta.st_mode) & 0o077:
        raise _fail(f"Papierkorbpfad ist zu offen; erforderlich ist 0700: {path.name}")


def _prepare_transaction(preview: TrashPreview) -> None:
    paths = trash_paths(preview.project_root)
    for directory in (paths.control_directory, paths.trash_root, paths.transactions_root):
        _private_directory(directory, create=True)
    preview.transaction_directory.mkdir(mode=PRIVATE_DIRECTORY_MODE, exist_ok=False)
    os.chmod(preview.transaction_directory, PRIVATE_DIRECTORY_MODE)
    _private_directory(preview.transaction_directory, create=False)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _safe_manifest_file(path: Path) -> os.stat_result:
    if path.is_symlink():
        raise _fail("Transaktionsmanifest darf kein Symlink sein.")
    try:
        meta = path.lstat()
    except FileNotFoundError as exc:
        raise _fail("Transaktionsmanifest fehlt.") from exc
    except OSError as exc:
        raise _fail(f"Transaktionsmanifest konnte nicht geprüft werden: {exc}", technical_detail=repr(exc)) from exc
    if not stat.S_ISREG(meta.st_mode):
        raise _fail("Transaktionsmanifest ist keine reguläre Datei.")
    if meta.st_nlink != 1:
        raise _fail("Transaktionsmanifest besitzt zusätzliche Hardlinks.")
    if hasattr(os, "getuid") and meta.st_uid != os.getuid():
        raise _fail("Transaktionsmanifest gehört nicht dem aktuellen Nutzer.")
    if stat.S_IMODE(meta.st_mode) & 0o077:
        raise _fail("Transaktionsmanifest ist zu offen; erforderlich ist 0600.")
    if meta.st_size > MAXIMUM_MANIFEST_BYTES:
        raise _fail("Transaktionsmanifest überschreitet das Größenlimit.")
    return meta


def _parse_manifest(value: object) -> TrashManifest:
    if not isinstance(value, dict) or set(value) != _MANIFEST_KEYS:
        raise _fail("Transaktionsmanifest besitzt einen unbekannten Aufbau.")
    manifest = TrashManifest(
        schema_version=value["schemaVersion"],
        transaction_id=value["transactionId"],
        state=value["state"],
        created_utc=value["createdUtc"],
        completed_utc=value["completedUtc"],
        restored_utc=value["restoredUtc"],
        original_relative_path=value["originalRelativePath"],
        payload_relative_path=value["payloadRelativePath"],
        source_type=value["sourceType"],
        source_device=value["sourceDevice"],
        source_inode=value["sourceInode"],
        source_mode=value["sourceMode"],
        source_size=value["sourceSize"],
        source_mtime_ns=value["sourceMtimeNs"],
    )
    if (
        not isinstance(manifest.schema_version, int)
        or isinstance(manifest.schema_version, bool)
        or manifest.schema_version != MANIFEST_SCHEMA_VERSION
    ):
        raise _fail("Transaktionsmanifest verwendet eine unbekannte Schemaversion.")
    if not isinstance(manifest.transaction_id, str) or not _TRANSACTION_ID_PATTERN.fullmatch(manifest.transaction_id):
        raise _fail("Transaktionsmanifest enthält eine ungültige Transaktions-ID.")
    if not isinstance(manifest.state, str) or manifest.state not in _ALLOWED_STATES:
        raise _fail("Transaktionsmanifest enthält einen unbekannten Zustand.")
    if manifest.source_type not in {"file", "directory"}:
        raise _fail("Transaktionsmanifest enthält einen unbekannten Quelltyp.")
    for item in (
        manifest.created_utc, manifest.completed_utc, manifest.restored_utc,
        manifest.original_relative_path, manifest.payload_relative_path,
    ):
        if not isinstance(item, str):
            raise _fail("Transaktionsmanifest enthält ungültige Textfelder.")
    for item in (
        manifest.source_device, manifest.source_inode, manifest.source_mode,
        manifest.source_size, manifest.source_mtime_ns,
    ):
        if not isinstance(item, int) or isinstance(item, bool) or item < 0:
            raise _fail("Transaktionsmanifest enthält ungültige Zahlenwerte.")
    return manifest


def read_manifest(path: Path) -> TrashManifest:
    _safe_manifest_file(path)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _fail(f"Transaktionsmanifest ist beschädigt: {exc}", technical_detail=repr(exc)) from exc
    return _parse_manifest(value)


def _write_manifest_atomic(path: Path, manifest: TrashManifest) -> None:
    encoded = (json.dumps(manifest.as_dict(), ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    if len(encoded) > MAXIMUM_MANIFEST_BYTES:
        raise _fail("Transaktionsmanifest überschreitet das Sicherheitslimit.")
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    descriptor: int | None = None
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(temporary, flags, PRIVATE_FILE_MODE)
        os.fchmod(descriptor, PRIVATE_FILE_MODE)
        view = memoryview(encoded)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("Manifest wurde nicht vollständig geschrieben.")
            view = view[written:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        os.replace(temporary, path)
        os.chmod(path, PRIVATE_FILE_MODE)
        _fsync_directory(path.parent)
        if read_manifest(path) != manifest:
            raise OSError("Manifest-Nachvalidierung stimmt nicht überein.")
    except SafeOperationError:
        raise
    except OSError as exc:
        raise _fail(
            f"Transaktionsmanifest konnte nicht atomar gespeichert werden: {exc}",
            data_state="Bereits verschobene Daten bleiben im privaten Transaktionsordner wiederherstellbar.",
            next_step="Diagnose sichern und keine manuelle Löschung durchführen.",
            technical_detail=repr(exc),
        ) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)


def _manifest_for(preview: TrashPreview) -> TrashManifest:
    return TrashManifest(
        schema_version=MANIFEST_SCHEMA_VERSION,
        transaction_id=preview.transaction_id,
        state="prepared",
        created_utc=_utc_now(),
        completed_utc="",
        restored_utc="",
        original_relative_path=preview.original_relative_path,
        payload_relative_path=preview.payload_path.relative_to(preview.project_root).as_posix(),
        source_type=preview.source_type,
        source_device=preview.source_device,
        source_inode=preview.source_inode,
        source_mode=preview.source_mode,
        source_size=preview.source_size,
        source_mtime_ns=preview.source_mtime_ns,
    )


def execute_trash_move(preview: TrashPreview) -> TrashResult:
    _validate_preview(preview)
    if preview.transaction_directory.exists() or preview.transaction_directory.is_symlink():
        raise _fail("Transaktionsziel ist inzwischen belegt; Überschreiben wurde verhindert.")
    moved = False
    manifest = _manifest_for(preview)
    try:
        _prepare_transaction(preview)
        if preview.payload_path.exists() or preview.payload_path.is_symlink():
            raise _fail("Payload-Ziel ist bereits belegt.")
        _write_manifest_atomic(preview.manifest_path, manifest)
        os.replace(preview.source_path, preview.payload_path)
        moved = True
        _fsync_directory(preview.source_path.parent)
        _fsync_directory(preview.transaction_directory)
        manifest = replace(manifest, state="trashed", completed_utc=_utc_now())
        _write_manifest_atomic(preview.manifest_path, manifest)
        return TrashResult(preview.transaction_id, "trashed", preview.manifest_path, preview.source_path, preview.payload_path)
    except SafeOperationError:
        raise
    except OSError as exc:
        raise _fail(
            f"Atomare Papierkorbverschiebung ist fehlgeschlagen: {exc}",
            data_state=(
                "Die Quelle liegt vollständig im privaten Transaktionsordner; das vorbereitete Manifest bleibt erhalten."
                if moved else "Die Quelle blieb am ursprünglichen Ort."
            ),
            next_step="Diagnose sichern und keine manuelle Löschung durchführen.",
            technical_detail=repr(exc),
        ) from exc
    finally:
        if not moved and preview.transaction_directory.exists():
            try:
                for item in preview.transaction_directory.iterdir():
                    if item.is_file() and not item.is_symlink():
                        item.unlink()
                preview.transaction_directory.rmdir()
            except OSError:
                pass


def _manifest_path(root: Path, transaction_id: str) -> Path:
    txid = transaction_id.strip().upper()
    if not _TRANSACTION_ID_PATTERN.fullmatch(txid):
        raise _fail("Transaktions-ID besitzt ein ungültiges Format.")
    return trash_paths(root).transactions_root / txid / MANIFEST_NAME


def _from_relative(root: Path, value: str, *, label: str) -> Path:
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts or relative == Path("."):
        raise _fail(f"{label} im Manifest überschreitet die Projektgrenze.")
    result = root / relative
    _relative(result, root, label=label)
    return result


def _validate_payload(payload: Path, manifest: TrashManifest, root_meta: os.stat_result) -> os.stat_result:
    if not payload.exists() or payload.is_symlink():
        raise _fail("Der erwartete Payload fehlt oder ist ein Symlink.")
    meta = payload.lstat()
    expected_file = manifest.source_type == "file"
    if expected_file != stat.S_ISREG(meta.st_mode):
        if not (not expected_file and stat.S_ISDIR(meta.st_mode)):
            raise _fail("Payloadtyp stimmt nicht mit dem Manifest überein.")
    if expected_file and meta.st_nlink != 1:
        raise _fail("Payload besitzt zusätzliche Hardlinks.")
    current = (meta.st_dev, meta.st_ino, stat.S_IMODE(meta.st_mode), meta.st_size, meta.st_mtime_ns)
    expected = (
        manifest.source_device, manifest.source_inode, manifest.source_mode,
        manifest.source_size, manifest.source_mtime_ns,
    )
    if current != expected:
        raise _fail(
            "Payload wurde seit der Papierkorbtransaktion verändert oder ersetzt.",
            data_state="Payload blieb am aktuellen Ort; der Originalpfad blieb frei.",
        )
    if meta.st_dev != root_meta.st_dev:
        raise _fail("Payload und Projekt liegen nicht mehr auf demselben Dateisystem.")
    return meta


def restore_transaction(project_root: Path, transaction_id: str) -> TrashResult:
    root = _absolute(project_root)
    root_meta = _project_metadata(root)
    manifest_path = _manifest_path(root, transaction_id)
    paths = trash_paths(root)
    transaction = manifest_path.parent
    for directory in (paths.control_directory, paths.trash_root, paths.transactions_root, transaction):
        _private_directory(directory, create=False)
    manifest = read_manifest(manifest_path)
    if manifest.transaction_id != transaction.name:
        raise _fail("Transaktions-ID und Manifest stimmen nicht überein.")
    if manifest.state == "restored":
        raise _fail("Die Transaktion wurde bereits wiederhergestellt.")
    original = _from_relative(root, manifest.original_relative_path, label="Originalpfad")
    payload = _from_relative(root, manifest.payload_relative_path, label="Payloadpfad")
    if payload != transaction / PAYLOAD_NAME:
        raise _fail("Payloadpfad entspricht nicht dem Transaktionsordner.")
    if original.exists() or original.is_symlink():
        raise _fail(
            "Am ursprünglichen Pfad existiert bereits ein Objekt; Überschreiben wurde verhindert.",
            data_state="Bestehendes Objekt und Payload blieben unverändert.",
        )
    if not original.parent.exists() or original.parent.is_symlink() or not original.parent.is_dir():
        raise _fail("Der ursprüngliche Elternordner fehlt oder ist unsicher.")
    _no_symlink_components(original.parent, root, label="Originalordner")
    if not os.access(original.parent, os.W_OK | os.X_OK):
        raise _fail("Der ursprüngliche Elternordner ist nicht beschreibbar.")
    _validate_payload(payload, manifest, root_meta)
    recovered_prepared = manifest.state == "prepared"
    try:
        os.replace(payload, original)
        _fsync_directory(original.parent)
        _fsync_directory(transaction)
        _write_manifest_atomic(manifest_path, replace(manifest, state="restored", restored_utc=_utc_now()))
    except SafeOperationError:
        raise
    except OSError as exc:
        raise _fail(
            f"Atomare Wiederherstellung ist fehlgeschlagen: {exc}",
            data_state=(
                "Das Objekt liegt vollständig am Originalpfad; das Manifest benötigt Nachprüfung."
                if original.exists() and not payload.exists() else "Payload blieb im Papierkorb."
            ),
            next_step="Diagnose sichern und keine manuelle Löschung durchführen.",
            technical_detail=repr(exc),
        ) from exc
    return TrashResult(
        manifest.transaction_id, "restored", manifest_path, original, payload,
        recovered_prepared_state=recovered_prepared,
    )


def inspect_transaction(project_root: Path, transaction_id: str) -> TrashManifest:
    root = _absolute(project_root)
    _project_metadata(root)
    return read_manifest(_manifest_path(root, transaction_id))


def format_trash_preview(preview: TrashPreview) -> str:
    lines = [
        "PAPIERKORB-VORSCHAU",
        f"Transaktions-ID: {preview.transaction_id}",
        f"Quelle: {preview.original_relative_path}",
        f"Typ: {preview.source_type}",
        "Methode: atomare Umbenennung innerhalb desselben Dateisystems",
        f"Manifest: {preview.manifest_path.relative_to(preview.project_root).as_posix()}",
        f"Payload: {preview.payload_path.relative_to(preview.project_root).as_posix()}",
        f"Freier Speicher: {preview.available_bytes} Bytes",
        "Wiederherstellbar: JA, sofern am Originalpfad kein Konflikt besteht",
        "Dauerhafte Löschung: NEIN",
    ]
    lines.extend(f"WARNUNG: {warning}" for warning in preview.warnings)
    return "\n".join(lines)
