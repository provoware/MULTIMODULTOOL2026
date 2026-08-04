"""Append-only, crash-safe undo/redo journal for project file operations.

The journal is Linux-only, private, hash chained and append-only. It never stores
absolute paths. The initial supported operation is the project trash transaction.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Iterable
from uuid import uuid4

from .error_events import SafeOperationError
from .project_trash import (
    TrashPreview,
    execute_trash_move,
    inspect_transaction,
    preview_trash_move,
    restore_transaction,
    trash_paths,
)

HISTORY_DIRECTORY_NAME = "history"
JOURNAL_FILE_NAME = "actions.jsonl"
JOURNAL_SCHEMA_VERSION = 1
PRIVATE_DIRECTORY_MODE = 0o700
PRIVATE_FILE_MODE = 0o600
MAXIMUM_JOURNAL_BYTES = 8 * 1024 * 1024
MAXIMUM_EVENTS = 20000
ZERO_HASH = "0" * 64

_ACTION_ID_PATTERN = re.compile(r"^MMTACTION-[0-9]{8}T[0-9]{6}-[A-F0-9]{12}$")
_TRANSACTION_ID_PATTERN = re.compile(r"^MMTTRASH-[0-9]{8}T[0-9]{6}-[A-F0-9]{12}$")
_EVENT_ID_PATTERN = re.compile(r"^MMTEVENT-[A-F0-9]{24}$")
_ALLOWED_KINDS = {
    "prepare",
    "apply",
    "cancel",
    "undo-intent",
    "undo",
    "redo-intent",
    "redo",
}
_ALLOWED_STATES = {"pending", "trashed", "restored", "cancelled"}
_EVENT_KEYS = {
    "schemaVersion",
    "sequence",
    "eventId",
    "eventKind",
    "actionId",
    "transactionId",
    "operation",
    "createdUtc",
    "originalRelativePath",
    "stateAfter",
    "recovered",
    "previousHash",
    "eventHash",
}


@dataclass(frozen=True)
class JournalPaths:
    project_root: Path
    control_directory: Path
    history_directory: Path
    journal_file: Path


@dataclass(frozen=True)
class ActionEvent:
    schema_version: int
    sequence: int
    event_id: str
    event_kind: str
    action_id: str
    transaction_id: str
    operation: str
    created_utc: str
    original_relative_path: str
    state_after: str
    recovered: bool
    previous_hash: str
    event_hash: str

    def as_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": self.schema_version,
            "sequence": self.sequence,
            "eventId": self.event_id,
            "eventKind": self.event_kind,
            "actionId": self.action_id,
            "transactionId": self.transaction_id,
            "operation": self.operation,
            "createdUtc": self.created_utc,
            "originalRelativePath": self.original_relative_path,
            "stateAfter": self.state_after,
            "recovered": self.recovered,
            "previousHash": self.previous_hash,
            "eventHash": self.event_hash,
        }


@dataclass(frozen=True)
class ActionState:
    action_id: str
    order: int
    original_relative_path: str
    status: str
    current_transaction_id: str
    transaction_ids: tuple[str, ...]
    pending_kind: str = ""


@dataclass(frozen=True)
class JournalSnapshot:
    events: tuple[ActionEvent, ...]
    actions: tuple[ActionState, ...]
    warnings: tuple[str, ...] = ()

    @property
    def applied_count(self) -> int:
        return sum(action.status == "trashed" for action in self.actions)

    @property
    def undone_count(self) -> int:
        return sum(action.status == "restored" for action in self.actions)


@dataclass(frozen=True)
class ActionResult:
    action_id: str
    transaction_id: str
    state: str
    changed: bool
    recovered: bool = False
    message: str = ""


def _fail(
    cause: str,
    *,
    consequence: str = "Die Undo-/Redo-Operation wurde kontrolliert blockiert.",
    data_state: str = "Projektdateien, Papierkorbtransaktionen und Journal blieben unverändert.",
    solution: str = "Journal, Transaktionsmanifest und aktuellen Dateizustand prüfen.",
    next_step: str = "Diagnosekennung sichern und die Aktion erst nach grüner Prüfung wiederholen.",
    technical_detail: str = "",
) -> SafeOperationError:
    return SafeOperationError(
        category="undo-redo-journal",
        cause=cause,
        consequence=consequence,
        data_state=data_state,
        solution=solution,
        next_step=next_step,
        technical_detail=technical_detail,
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def create_action_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"MMTACTION-{stamp}-{uuid4().hex[:12].upper()}"


def _create_event_id() -> str:
    return f"MMTEVENT-{uuid4().hex[:24].upper()}"


def _absolute_project(path: Path) -> Path:
    expanded = path.expanduser()
    if not expanded.is_absolute():
        raise _fail("Projektpfad ist nicht absolut.")
    root = Path(os.path.abspath(os.fspath(expanded)))
    if root.is_symlink():
        raise _fail("Projektstamm darf kein Symlink sein.")
    try:
        metadata = root.lstat()
    except FileNotFoundError as exc:
        raise _fail("Projektstamm existiert nicht.") from exc
    except OSError as exc:
        raise _fail(f"Projektstamm konnte nicht geprüft werden: {exc}") from exc
    if not stat.S_ISDIR(metadata.st_mode):
        raise _fail("Projektstamm ist kein Verzeichnis.")
    if hasattr(os, "getuid") and metadata.st_uid != os.getuid():
        raise _fail("Projektstamm gehört nicht dem aktuellen Linux-Nutzer.")
    if not os.access(root, os.W_OK | os.X_OK):
        raise _fail("Projektstamm ist nicht sicher beschreibbar.")
    return root


def journal_paths(project_root: Path) -> JournalPaths:
    root = _absolute_project(project_root)
    control = trash_paths(root).control_directory
    history = control / HISTORY_DIRECTORY_NAME
    return JournalPaths(root, control, history, history / JOURNAL_FILE_NAME)


def _safe_relative(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _fail("Journal enthält keinen gültigen relativen Originalpfad.")
    path = Path(value)
    if path.is_absolute() or path == Path(".") or ".." in path.parts:
        raise _fail("Journalpfad überschreitet die Projektgrenze.")
    return path.as_posix()


def _private_directory(path: Path, *, create: bool) -> None:
    if path.is_symlink():
        raise _fail(f"Privater Journalpfad darf kein Symlink sein: {path.name}")
    try:
        if create:
            path.mkdir(mode=PRIVATE_DIRECTORY_MODE, exist_ok=True)
            os.chmod(path, PRIVATE_DIRECTORY_MODE)
        metadata = path.lstat()
    except FileNotFoundError as exc:
        raise _fail(f"Privater Journalpfad fehlt: {path.name}") from exc
    except OSError as exc:
        raise _fail(f"Privater Journalpfad konnte nicht geprüft werden: {exc}") from exc
    if not stat.S_ISDIR(metadata.st_mode):
        raise _fail(f"Privater Journalpfad ist kein Verzeichnis: {path.name}")
    if hasattr(os, "getuid") and metadata.st_uid != os.getuid():
        raise _fail(f"Privater Journalpfad gehört nicht dem aktuellen Nutzer: {path.name}")
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise _fail(f"Privater Journalpfad ist zu offen; erforderlich ist 0700: {path.name}")


def _validate_journal_file(path: Path) -> os.stat_result:
    if path.is_symlink():
        raise _fail("Undo-/Redo-Journal darf kein Symlink sein.")
    try:
        metadata = path.lstat()
    except FileNotFoundError as exc:
        raise _fail("Undo-/Redo-Journal fehlt.") from exc
    except OSError as exc:
        raise _fail(f"Undo-/Redo-Journal konnte nicht geprüft werden: {exc}") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise _fail("Undo-/Redo-Journal ist keine reguläre Datei.")
    if metadata.st_nlink != 1:
        raise _fail("Undo-/Redo-Journal besitzt zusätzliche Hardlinks.")
    if hasattr(os, "getuid") and metadata.st_uid != os.getuid():
        raise _fail("Undo-/Redo-Journal gehört nicht dem aktuellen Nutzer.")
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise _fail("Undo-/Redo-Journal ist zu offen; erforderlich ist 0600.")
    if metadata.st_size > MAXIMUM_JOURNAL_BYTES:
        raise _fail("Undo-/Redo-Journal überschreitet das Größenlimit.")
    return metadata


def _canonical_hash(value: dict[str, object]) -> str:
    payload = dict(value)
    payload.pop("eventHash", None)
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _parse_event(value: object) -> ActionEvent:
    if not isinstance(value, dict) or set(value) != _EVENT_KEYS:
        raise _fail("Journalereignis besitzt einen unbekannten Aufbau.")
    event = ActionEvent(
        schema_version=value["schemaVersion"],
        sequence=value["sequence"],
        event_id=value["eventId"],
        event_kind=value["eventKind"],
        action_id=value["actionId"],
        transaction_id=value["transactionId"],
        operation=value["operation"],
        created_utc=value["createdUtc"],
        original_relative_path=value["originalRelativePath"],
        state_after=value["stateAfter"],
        recovered=value["recovered"],
        previous_hash=value["previousHash"],
        event_hash=value["eventHash"],
    )
    if event.schema_version != JOURNAL_SCHEMA_VERSION:
        raise _fail("Journalereignis verwendet eine unbekannte Schemaversion.")
    if not isinstance(event.sequence, int) or isinstance(event.sequence, bool) or event.sequence < 1:
        raise _fail("Journalereignis besitzt keine gültige Sequenznummer.")
    if not isinstance(event.event_id, str) or not _EVENT_ID_PATTERN.fullmatch(event.event_id):
        raise _fail("Journalereignis besitzt keine gültige Ereignis-ID.")
    if not isinstance(event.event_kind, str) or event.event_kind not in _ALLOWED_KINDS:
        raise _fail("Journalereignis besitzt einen unbekannten Ereignistyp.")
    if not isinstance(event.action_id, str) or not _ACTION_ID_PATTERN.fullmatch(event.action_id):
        raise _fail("Journalereignis besitzt keine gültige Aktions-ID.")
    if not isinstance(event.transaction_id, str) or not _TRANSACTION_ID_PATTERN.fullmatch(event.transaction_id):
        raise _fail("Journalereignis besitzt keine gültige Transaktions-ID.")
    if event.operation != "project-trash":
        raise _fail("Journalereignis verwendet eine nicht freigegebene Operation.")
    if not isinstance(event.created_utc, str) or not event.created_utc:
        raise _fail("Journalereignis besitzt keinen Zeitstempel.")
    _safe_relative(event.original_relative_path)
    if event.state_after not in _ALLOWED_STATES:
        raise _fail("Journalereignis besitzt einen unbekannten Folgezustand.")
    if not isinstance(event.recovered, bool):
        raise _fail("Journalereignis besitzt kein gültiges Recovery-Kennzeichen.")
    for label, digest in (("previousHash", event.previous_hash), ("eventHash", event.event_hash)):
        if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise _fail(f"Journalereignis enthält keinen gültigen {label}.")
    if _canonical_hash(event.as_dict()) != event.event_hash:
        raise _fail("Hash des Journalereignisses ist ungültig.")
    return event


def _validate_event_sequence(events: Iterable[ActionEvent]) -> tuple[ActionEvent, ...]:
    parsed = tuple(events)
    previous = ZERO_HASH
    event_ids: set[str] = set()
    for expected_sequence, event in enumerate(parsed, start=1):
        if event.sequence != expected_sequence:
            raise _fail("Journal besitzt eine Lücke oder doppelte Sequenznummer.")
        if event.previous_hash != previous:
            raise _fail("Hashkette des Undo-/Redo-Journals ist unterbrochen.")
        if event.event_id in event_ids:
            raise _fail("Journal enthält eine doppelte Ereignis-ID.")
        event_ids.add(event.event_id)
        previous = event.event_hash
    _derive_actions(parsed)
    return parsed


def _decode_events(data: bytes) -> tuple[ActionEvent, ...]:
    if len(data) > MAXIMUM_JOURNAL_BYTES:
        raise _fail("Undo-/Redo-Journal überschreitet das Größenlimit.")
    if not data:
        return ()
    try:
        text = data.decode("utf-8")
    except UnicodeError as exc:
        raise _fail("Undo-/Redo-Journal ist nicht als UTF-8 lesbar.") from exc
    raw_lines = text.splitlines()
    if len(raw_lines) > MAXIMUM_EVENTS:
        raise _fail("Undo-/Redo-Journal enthält zu viele Ereignisse.")
    events: list[ActionEvent] = []
    for index, line in enumerate(raw_lines, start=1):
        if not line.strip():
            raise _fail(f"Undo-/Redo-Journal enthält eine leere Zeile: {index}")
        try:
            events.append(_parse_event(json.loads(line)))
        except json.JSONDecodeError as exc:
            raise _fail(f"Undo-/Redo-Journal ist in Zeile {index} beschädigt: {exc}") from exc
    return _validate_event_sequence(events)


def _read_descriptor(descriptor: int) -> bytes:
    os.lseek(descriptor, 0, os.SEEK_SET)
    chunks: list[bytes] = []
    total = 0
    while True:
        block = os.read(descriptor, 65536)
        if not block:
            break
        total += len(block)
        if total > MAXIMUM_JOURNAL_BYTES:
            raise _fail("Undo-/Redo-Journal überschreitet das Größenlimit.")
        chunks.append(block)
    return b"".join(chunks)


def _read_events(path: Path) -> tuple[ActionEvent, ...]:
    if not path.exists():
        return ()
    _validate_journal_file(path)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise _fail(f"Undo-/Redo-Journal konnte nicht sicher geöffnet werden: {exc}") from exc
    try:
        return _decode_events(_read_descriptor(descriptor))
    finally:
        os.close(descriptor)


def _transition_state(last_kind: str, new_kind: str) -> bool:
    allowed = {
        "": {"prepare"},
        "prepare": {"apply", "cancel"},
        "apply": {"undo-intent"},
        "undo-intent": {"undo"},
        "undo": {"redo-intent"},
        "redo-intent": {"redo"},
        "redo": {"undo-intent"},
        "cancel": set(),
    }
    return new_kind in allowed.get(last_kind, set())


def _derive_actions(events: Iterable[ActionEvent]) -> tuple[ActionState, ...]:
    states: dict[str, ActionState] = {}
    last_kind: dict[str, str] = {}
    order: list[str] = []
    for event in events:
        current_kind = last_kind.get(event.action_id, "")
        if not _transition_state(current_kind, event.event_kind):
            raise _fail(
                f"Ungültige Journalzustandsfolge für {event.action_id}: "
                f"{current_kind or 'start'} → {event.event_kind}"
            )
        current = states.get(event.action_id)
        if current is None:
            order.append(event.action_id)
            current = ActionState(
                action_id=event.action_id,
                order=len(order),
                original_relative_path=event.original_relative_path,
                status="pending",
                current_transaction_id=event.transaction_id,
                transaction_ids=(event.transaction_id,),
                pending_kind="prepare",
            )
        elif current.original_relative_path != event.original_relative_path:
            raise _fail("Aktions-ID verweist auf unterschiedliche Originalpfade.")
        txids = current.transaction_ids
        if event.transaction_id not in txids:
            txids = (*txids, event.transaction_id)
        status = current.status
        pending = ""
        if event.event_kind in {"prepare", "undo-intent", "redo-intent"}:
            pending = event.event_kind
        elif event.event_kind in {"apply", "redo"}:
            status = "trashed"
        elif event.event_kind == "undo":
            status = "restored"
        elif event.event_kind == "cancel":
            status = "cancelled"
        states[event.action_id] = ActionState(
            action_id=current.action_id,
            order=current.order,
            original_relative_path=current.original_relative_path,
            status=status,
            current_transaction_id=event.transaction_id,
            transaction_ids=txids,
            pending_kind=pending,
        )
        last_kind[event.action_id] = event.event_kind
    result = tuple(states[action_id] for action_id in order)
    active = [item for item in result if item.status != "cancelled"]
    seen_restored = False
    for item in active:
        if item.pending_kind:
            continue
        if item.status == "restored":
            seen_restored = True
        elif item.status == "trashed" and seen_restored:
            raise _fail("Undo-/Redo-Stapel ist nicht mehr als angewendetes Präfix darstellbar.")
    return result


def _event_state(kind: str) -> str:
    return {
        "prepare": "pending",
        "apply": "trashed",
        "cancel": "cancelled",
        "undo-intent": "pending",
        "undo": "restored",
        "redo-intent": "pending",
        "redo": "trashed",
    }[kind]


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


class UndoRedoJournal:
    """Private append-only journal and stack coordinator."""

    def __init__(self, project_root: Path) -> None:
        self.paths = journal_paths(project_root)

    def inspect(self) -> JournalSnapshot:
        events = _read_events(self.paths.journal_file)
        return JournalSnapshot(events, _derive_actions(events))

    def _ensure_storage(self) -> None:
        for directory in (self.paths.control_directory, self.paths.history_directory):
            _private_directory(directory, create=True)

    def _append(
        self,
        *,
        kind: str,
        action_id: str,
        transaction_id: str,
        original_relative_path: str,
        recovered: bool = False,
    ) -> ActionEvent:
        if kind not in _ALLOWED_KINDS:
            raise _fail("Unbekannter Journalereignistyp.")
        if not _ACTION_ID_PATTERN.fullmatch(action_id):
            raise _fail("Aktions-ID besitzt ein ungültiges Format.")
        if not _TRANSACTION_ID_PATTERN.fullmatch(transaction_id):
            raise _fail("Transaktions-ID besitzt ein ungültiges Format.")
        relative = _safe_relative(original_relative_path)
        self._ensure_storage()
        flags = (
            os.O_RDWR
            | os.O_APPEND
            | os.O_CREAT
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        descriptor: int | None = None
        created = not self.paths.journal_file.exists()
        try:
            descriptor = os.open(self.paths.journal_file, flags, PRIVATE_FILE_MODE)
            os.fchmod(descriptor, PRIVATE_FILE_MODE)
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                raise _fail("Undo-/Redo-Journal besitzt einen unsicheren Dateityp.")
            if hasattr(os, "getuid") and metadata.st_uid != os.getuid():
                raise _fail("Undo-/Redo-Journal gehört nicht dem aktuellen Nutzer.")
            events = _decode_events(_read_descriptor(descriptor))
            previous_hash = events[-1].event_hash if events else ZERO_HASH
            sequence = len(events) + 1
            payload: dict[str, object] = {
                "schemaVersion": JOURNAL_SCHEMA_VERSION,
                "sequence": sequence,
                "eventId": _create_event_id(),
                "eventKind": kind,
                "actionId": action_id,
                "transactionId": transaction_id,
                "operation": "project-trash",
                "createdUtc": _utc_now(),
                "originalRelativePath": relative,
                "stateAfter": _event_state(kind),
                "recovered": bool(recovered),
                "previousHash": previous_hash,
                "eventHash": "",
            }
            payload["eventHash"] = _canonical_hash(payload)
            event = _parse_event(payload)
            _validate_event_sequence((*events, event))
            encoded = (
                json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                + "\n"
            ).encode("utf-8")
            if metadata.st_size + len(encoded) > MAXIMUM_JOURNAL_BYTES:
                raise _fail("Undo-/Redo-Journal würde das Größenlimit überschreiten.")
            os.lseek(descriptor, 0, os.SEEK_END)
            view = memoryview(encoded)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise OSError("Journalereignis wurde nicht vollständig geschrieben.")
                view = view[written:]
            os.fsync(descriptor)
            return event
        except SafeOperationError:
            raise
        except OSError as exc:
            raise _fail(
                f"Journalereignis konnte nicht absturzsicher angehängt werden: {exc}",
                data_state="Dateioperation und bestehende Journalzeilen bleiben vollständig; "
                "ein fehlender Abschluss wird beim nächsten Aufruf abgeglichen.",
                technical_detail=repr(exc),
            ) from exc
        finally:
            if descriptor is not None:
                try:
                    fcntl.flock(descriptor, fcntl.LOCK_UN)
                except OSError:
                    pass
                os.close(descriptor)
            if created and self.paths.journal_file.exists():
                try:
                    os.chmod(self.paths.journal_file, PRIVATE_FILE_MODE)
                    _fsync_directory(self.paths.history_directory)
                except OSError:
                    pass

    def reconcile(self) -> JournalSnapshot:
        snapshot = self.inspect()
        for action in snapshot.actions:
            if not action.pending_kind:
                continue
            if action.pending_kind == "prepare":
                try:
                    manifest = inspect_transaction(
                        self.paths.project_root, action.current_transaction_id
                    )
                except SafeOperationError:
                    tx_dir = (
                        trash_paths(self.paths.project_root).transactions_root
                        / action.current_transaction_id
                    )
                    original = self.paths.project_root / action.original_relative_path
                    if not tx_dir.exists() and original.exists() and not original.is_symlink():
                        self._append(
                            kind="cancel",
                            action_id=action.action_id,
                            transaction_id=action.current_transaction_id,
                            original_relative_path=action.original_relative_path,
                            recovered=True,
                        )
                        continue
                    raise
                transaction = (
                    trash_paths(self.paths.project_root).transactions_root
                    / action.current_transaction_id
                )
                payload = transaction / "payload"
                original = self.paths.project_root / action.original_relative_path
                if (
                    manifest.state in {"prepared", "trashed"}
                    and payload.exists()
                    and not payload.is_symlink()
                    and not original.exists()
                    and not original.is_symlink()
                ):
                    self._append(
                        kind="apply",
                        action_id=action.action_id,
                        transaction_id=action.current_transaction_id,
                        original_relative_path=action.original_relative_path,
                        recovered=True,
                    )
                elif original.exists() and not payload.exists():
                    self._append(
                        kind="cancel",
                        action_id=action.action_id,
                        transaction_id=action.current_transaction_id,
                        original_relative_path=action.original_relative_path,
                        recovered=True,
                    )
                else:
                    raise _fail(
                        "Vorbereitete Papierkorbaktion besitzt einen widersprüchlichen Datei- und Manifestzustand."
                    )
            elif action.pending_kind == "undo-intent":
                manifest = inspect_transaction(
                    self.paths.project_root, action.current_transaction_id
                )
                if manifest.state == "restored":
                    self._append(
                        kind="undo",
                        action_id=action.action_id,
                        transaction_id=action.current_transaction_id,
                        original_relative_path=action.original_relative_path,
                        recovered=True,
                    )
            elif action.pending_kind == "redo-intent":
                try:
                    manifest = inspect_transaction(
                        self.paths.project_root, action.current_transaction_id
                    )
                except SafeOperationError:
                    continue
                if manifest.state in {"prepared", "trashed"}:
                    self._append(
                        kind="redo",
                        action_id=action.action_id,
                        transaction_id=action.current_transaction_id,
                        original_relative_path=action.original_relative_path,
                        recovered=True,
                    )
        return self.inspect()

    def record_trash(
        self,
        preview: TrashPreview,
        *,
        action_id: str | None = None,
    ) -> ActionResult:
        snapshot = self.reconcile()
        if any(action.status == "restored" for action in snapshot.actions):
            raise _fail(
                "Neue Aktionen sind blockiert, solange eine Redo-Kette vorhanden ist.",
                solution="Ausstehende Redo-Schritte zuerst anwenden oder ein neues Projektjournal beginnen.",
            )
        action = (action_id or create_action_id()).strip().upper()
        for existing in snapshot.actions:
            if existing.action_id == action:
                if (
                    existing.original_relative_path == preview.original_relative_path
                    and existing.current_transaction_id == preview.transaction_id
                    and existing.status == "trashed"
                ):
                    return ActionResult(
                        action,
                        preview.transaction_id,
                        "trashed",
                        False,
                        message="Aktion war bereits vollständig erfasst.",
                    )
                raise _fail("Aktions-ID ist bereits mit einem anderen Zustand belegt.")
        self._append(
            kind="prepare",
            action_id=action,
            transaction_id=preview.transaction_id,
            original_relative_path=preview.original_relative_path,
        )
        try:
            result = execute_trash_move(preview)
        except SafeOperationError:
            return self._recover_or_cancel_apply(action, preview)
        self._append(
            kind="apply",
            action_id=action,
            transaction_id=result.transaction_id,
            original_relative_path=preview.original_relative_path,
        )
        return ActionResult(action, result.transaction_id, "trashed", True)

    def _recover_or_cancel_apply(
        self, action_id: str, preview: TrashPreview
    ) -> ActionResult:
        try:
            manifest = inspect_transaction(
                self.paths.project_root, preview.transaction_id
            )
        except SafeOperationError:
            if preview.source_path.exists() and not preview.transaction_directory.exists():
                self._append(
                    kind="cancel",
                    action_id=action_id,
                    transaction_id=preview.transaction_id,
                    original_relative_path=preview.original_relative_path,
                    recovered=True,
                )
            raise
        if (
            manifest.state in {"prepared", "trashed"}
            and preview.payload_path.exists()
            and not preview.payload_path.is_symlink()
            and not preview.source_path.exists()
            and not preview.source_path.is_symlink()
        ):
            self._append(
                kind="apply",
                action_id=action_id,
                transaction_id=preview.transaction_id,
                original_relative_path=preview.original_relative_path,
                recovered=True,
            )
            return ActionResult(
                action_id,
                preview.transaction_id,
                "trashed",
                True,
                recovered=True,
                message="Unterbrochene Papierkorbtransaktion wurde aus dem Manifest übernommen.",
            )
        raise _fail("Papierkorbmanifest besitzt nach fehlgeschlagener Aktion einen widersprüchlichen Zustand.")

    def undo_action(self, action_id: str) -> ActionResult:
        snapshot = self.reconcile()
        target = next((item for item in snapshot.actions if item.action_id == action_id), None)
        if target is None:
            raise _fail("Aktions-ID ist im Journal nicht vorhanden.")
        if target.status == "restored" and not target.pending_kind:
            return ActionResult(
                target.action_id,
                target.current_transaction_id,
                "restored",
                False,
                message="Aktion war bereits zurückgenommen.",
            )
        active = [item for item in snapshot.actions if item.status != "cancelled"]
        applied = [
            item
            for item in active
            if item.status == "trashed" and item.pending_kind in {"", "undo-intent"}
        ]
        if not applied or applied[-1].action_id != target.action_id:
            raise _fail("Undo verletzt die Stapelreihenfolge; nur die letzte aktive Aktion ist zulässig.")
        if target.pending_kind not in {"", "undo-intent"}:
            raise _fail("Aktion besitzt einen anderen unvollständigen Journalzustand.")
        if target.pending_kind != "undo-intent":
            self._append(
                kind="undo-intent",
                action_id=target.action_id,
                transaction_id=target.current_transaction_id,
                original_relative_path=target.original_relative_path,
            )
        manifest = inspect_transaction(self.paths.project_root, target.current_transaction_id)
        recovered = manifest.state == "restored"
        if not recovered:
            restore_transaction(self.paths.project_root, target.current_transaction_id)
        self._append(
            kind="undo",
            action_id=target.action_id,
            transaction_id=target.current_transaction_id,
            original_relative_path=target.original_relative_path,
            recovered=recovered,
        )
        return ActionResult(
            target.action_id,
            target.current_transaction_id,
            "restored",
            not recovered,
            recovered=recovered,
        )

    def undo_last(self) -> ActionResult:
        snapshot = self.reconcile()
        active = [
            item
            for item in snapshot.actions
            if item.status == "trashed" and not item.pending_kind
        ]
        if not active:
            return ActionResult("", "", "restored", False, message="Keine Aktion zum Zurücknehmen vorhanden.")
        return self.undo_action(active[-1].action_id)

    def redo_action(self, action_id: str) -> ActionResult:
        snapshot = self.reconcile()
        target = next((item for item in snapshot.actions if item.action_id == action_id), None)
        if target is None:
            raise _fail("Aktions-ID ist im Journal nicht vorhanden.")
        if target.status == "trashed" and not target.pending_kind:
            return ActionResult(
                target.action_id,
                target.current_transaction_id,
                "trashed",
                False,
                message="Aktion war bereits erneut angewendet.",
            )
        active = [item for item in snapshot.actions if item.status != "cancelled"]
        undone = [
            item
            for item in active
            if item.status == "restored" and item.pending_kind in {"", "redo-intent"}
        ]
        if not undone or undone[0].action_id != target.action_id:
            raise _fail("Redo verletzt die Stapelreihenfolge; nur die nächste zurückgenommene Aktion ist zulässig.")
        if target.pending_kind not in {"", "redo-intent"}:
            raise _fail("Aktion besitzt einen anderen unvollständigen Journalzustand.")
        source = self.paths.project_root / target.original_relative_path
        if target.pending_kind == "redo-intent":
            preview = preview_trash_move(
                self.paths.project_root,
                source,
                transaction_id=target.current_transaction_id,
            )
        else:
            preview = preview_trash_move(self.paths.project_root, source)
            self._append(
                kind="redo-intent",
                action_id=target.action_id,
                transaction_id=preview.transaction_id,
                original_relative_path=target.original_relative_path,
            )
        try:
            execute_trash_move(preview)
        except SafeOperationError:
            try:
                manifest = inspect_transaction(
                    self.paths.project_root, preview.transaction_id
                )
            except SafeOperationError:
                raise
            if manifest.state not in {"prepared", "trashed"}:
                raise
            recovered = True
        else:
            recovered = False
        self._append(
            kind="redo",
            action_id=target.action_id,
            transaction_id=preview.transaction_id,
            original_relative_path=target.original_relative_path,
            recovered=recovered,
        )
        return ActionResult(
            target.action_id,
            preview.transaction_id,
            "trashed",
            True,
            recovered=recovered,
        )

    def redo_next(self) -> ActionResult:
        snapshot = self.reconcile()
        undone = [
            item
            for item in snapshot.actions
            if item.status == "restored" and not item.pending_kind
        ]
        if not undone:
            return ActionResult("", "", "trashed", False, message="Keine Aktion zum Wiederholen vorhanden.")
        return self.redo_action(undone[0].action_id)
