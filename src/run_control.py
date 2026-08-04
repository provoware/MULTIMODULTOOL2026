"""Transactional cancellation and restart contract for long project operations.

The first supported long operation is a sequential project-trash batch. Each run
has an immutable plan, an atomically replaced checkpoint, a private advisory
lock and controlled cancellation points. Existing undo/redo and trash manifests
remain the authoritative record for individual file operations.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
from typing import Callable, Iterable
from uuid import uuid4

from .error_events import SafeOperationError
from .project_trash import (
    MANIFEST_NAME,
    PAYLOAD_NAME,
    PRIVATE_DIRECTORY_MODE,
    PRIVATE_FILE_MODE,
    TrashManifest,
    TrashPreview,
    TrashResult,
    _fsync_directory as _trash_fsync_directory,
    _manifest_for,
    _prepare_transaction,
    _project_metadata,
    _validate_payload,
    _validate_preview,
    _write_manifest_atomic,
    create_transaction_id,
    inspect_transaction,
    preview_trash_move,
    trash_paths,
)
from .undo_redo import ActionResult, UndoRedoJournal, create_action_id

RUNS_DIRECTORY_NAME = "runs"
PLAN_FILE_NAME = "plan.json"
CHECKPOINT_FILE_NAME = "checkpoint.json"
LOCK_FILE_NAME = "run.lock"
CANCEL_FILE_NAME = "cancel.request"
RUN_SCHEMA_VERSION = 1
MAXIMUM_PLAN_BYTES = 2 * 1024 * 1024
MAXIMUM_CHECKPOINT_BYTES = 512 * 1024
MAXIMUM_RUN_ITEMS = 1000
RUN_OPERATION = "project-trash-batch"

_RUN_ID_PATTERN = re.compile(r"^MMTRUN-[0-9]{8}T[0-9]{6}-[A-F0-9]{12}$")
_ALLOWED_RUN_STATES = {"prepared", "running", "cancelled", "completed", "blocked"}
Failpoint = Callable[[str], None]


@dataclass(frozen=True)
class RunPaths:
    project_root: Path
    control_directory: Path
    runs_directory: Path
    run_directory: Path
    plan_file: Path
    checkpoint_file: Path
    lock_file: Path
    cancel_file: Path


@dataclass(frozen=True)
class RunItem:
    index: int
    source_relative_path: str

    def as_dict(self) -> dict[str, object]:
        return {"index": self.index, "sourceRelativePath": self.source_relative_path}


@dataclass(frozen=True)
class RunPlan:
    schema_version: int
    run_id: str
    operation: str
    created_utc: str
    items: tuple[RunItem, ...]
    plan_hash: str

    def as_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": self.schema_version,
            "runId": self.run_id,
            "operation": self.operation,
            "createdUtc": self.created_utc,
            "items": [item.as_dict() for item in self.items],
            "planHash": self.plan_hash,
        }


@dataclass(frozen=True)
class CurrentStep:
    index: int
    attempt: int
    action_id: str
    transaction_id: str
    source_relative_path: str

    def as_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "attempt": self.attempt,
            "actionId": self.action_id,
            "transactionId": self.transaction_id,
            "sourceRelativePath": self.source_relative_path,
        }


@dataclass(frozen=True)
class RunCheckpoint:
    schema_version: int
    run_id: str
    plan_hash: str
    state: str
    next_index: int
    completed_indices: tuple[int, ...]
    attempt_counts: tuple[int, ...]
    current_step: CurrentStep | None
    generation: int
    created_utc: str
    updated_utc: str
    cancel_requested: bool
    message: str

    def as_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": self.schema_version,
            "runId": self.run_id,
            "planHash": self.plan_hash,
            "state": self.state,
            "nextIndex": self.next_index,
            "completedIndices": list(self.completed_indices),
            "attemptCounts": list(self.attempt_counts),
            "currentStep": self.current_step.as_dict() if self.current_step else None,
            "generation": self.generation,
            "createdUtc": self.created_utc,
            "updatedUtc": self.updated_utc,
            "cancelRequested": self.cancel_requested,
            "message": self.message,
        }


@dataclass(frozen=True)
class RunSnapshot:
    plan: RunPlan
    checkpoint: RunCheckpoint
    paths: RunPaths


@dataclass(frozen=True)
class RunResult:
    run_id: str
    state: str
    completed_count: int
    total_count: int
    changed: bool
    recovered: bool = False
    message: str = ""


def _fail(
    cause: str,
    *,
    consequence: str = "Der lange Lauf wurde kontrolliert angehalten oder blockiert.",
    data_state: str = "Projektdateien, Papierkorbmanifeste, Aktionsjournal und Laufcheckpoint blieben nachvollziehbar.",
    solution: str = "Laufplan, Checkpoint, Journal, Manifest und Dateizustand gemeinsam prüfen.",
    next_step: str = "Diagnosekennung sichern und den Lauf erst nach grüner Zustandsprüfung fortsetzen.",
    technical_detail: str = "",
) -> SafeOperationError:
    return SafeOperationError(
        category="run-control",
        cause=cause,
        consequence=consequence,
        data_state=data_state,
        solution=solution,
        next_step=next_step,
        technical_detail=technical_detail,
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def create_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"MMTRUN-{stamp}-{uuid4().hex[:12].upper()}"


def _hit(failpoint: Failpoint | None, stage: str) -> None:
    if failpoint is not None:
        failpoint(stage)


def _safe_relative(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _fail("Laufplan enthält keinen gültigen relativen Projektpfad.")
    path = Path(value)
    if path.is_absolute() or path == Path(".") or ".." in path.parts:
        raise _fail("Laufplanpfad überschreitet die Projektgrenze.")
    return path.as_posix()


def run_paths(project_root: Path, run_id: str) -> RunPaths:
    root = UndoRedoJournal(project_root).paths.project_root
    normalized = run_id.strip().upper()
    if not _RUN_ID_PATTERN.fullmatch(normalized):
        raise _fail("Lauf-ID besitzt ein ungültiges Format.")
    control = trash_paths(root).control_directory
    runs = control / RUNS_DIRECTORY_NAME
    directory = runs / normalized
    return RunPaths(
        project_root=root,
        control_directory=control,
        runs_directory=runs,
        run_directory=directory,
        plan_file=directory / PLAN_FILE_NAME,
        checkpoint_file=directory / CHECKPOINT_FILE_NAME,
        lock_file=directory / LOCK_FILE_NAME,
        cancel_file=directory / CANCEL_FILE_NAME,
    )


def _private_directory(path: Path, *, create: bool) -> None:
    if path.is_symlink():
        raise _fail(f"Privater Laufpfad darf kein Symlink sein: {path.name}")
    try:
        if create:
            path.mkdir(mode=PRIVATE_DIRECTORY_MODE, exist_ok=True)
            os.chmod(path, PRIVATE_DIRECTORY_MODE)
        metadata = path.lstat()
    except FileNotFoundError as exc:
        raise _fail(f"Privater Laufpfad fehlt: {path.name}") from exc
    except OSError as exc:
        raise _fail(f"Privater Laufpfad konnte nicht geprüft werden: {exc}") from exc
    if not stat.S_ISDIR(metadata.st_mode):
        raise _fail(f"Privater Laufpfad ist kein Verzeichnis: {path.name}")
    if hasattr(os, "getuid") and metadata.st_uid != os.getuid():
        raise _fail(f"Privater Laufpfad gehört nicht dem aktuellen Nutzer: {path.name}")
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise _fail(f"Privater Laufpfad ist zu offen; erforderlich ist 0700: {path.name}")


def _validate_private_file(path: Path, *, maximum_bytes: int) -> os.stat_result:
    if path.is_symlink():
        raise _fail(f"Private Laufdatei darf kein Symlink sein: {path.name}")
    try:
        metadata = path.lstat()
    except FileNotFoundError as exc:
        raise _fail(f"Private Laufdatei fehlt: {path.name}") from exc
    except OSError as exc:
        raise _fail(f"Private Laufdatei konnte nicht geprüft werden: {exc}") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise _fail(f"Private Laufdatei ist keine reguläre Datei: {path.name}")
    if metadata.st_nlink != 1:
        raise _fail(f"Private Laufdatei besitzt zusätzliche Hardlinks: {path.name}")
    if hasattr(os, "getuid") and metadata.st_uid != os.getuid():
        raise _fail(f"Private Laufdatei gehört nicht dem aktuellen Nutzer: {path.name}")
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise _fail(f"Private Laufdatei ist zu offen; erforderlich ist 0600: {path.name}")
    if metadata.st_size > maximum_bytes:
        raise _fail(f"Private Laufdatei überschreitet das Größenlimit: {path.name}")
    return metadata


def _canonical_hash(value: dict[str, object], *, excluded: str) -> str:
    payload = dict(value)
    payload.pop(excluded, None)
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _read_json(path: Path, *, maximum_bytes: int) -> object:
    _validate_private_file(path, maximum_bytes=maximum_bytes)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise _fail(f"Laufdatei konnte nicht sicher geöffnet werden: {path.name}: {exc}") from exc
    try:
        chunks: list[bytes] = []
        total = 0
        while True:
            block = os.read(descriptor, 65536)
            if not block:
                break
            total += len(block)
            if total > maximum_bytes:
                raise _fail(f"Laufdatei überschreitet das Größenlimit: {path.name}")
            chunks.append(block)
    finally:
        os.close(descriptor)
    try:
        return json.loads(b"".join(chunks).decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise _fail(f"Laufdatei ist beschädigt: {path.name}: {exc}") from exc


def _atomic_write_json(path: Path, value: dict[str, object], *, maximum_bytes: int) -> None:
    encoded = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    if len(encoded) > maximum_bytes:
        raise _fail(f"Laufdatei würde das Größenlimit überschreiten: {path.name}")
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
                raise OSError("Laufdatei wurde nicht vollständig geschrieben.")
            view = view[written:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        os.replace(temporary, path)
        os.chmod(path, PRIVATE_FILE_MODE)
        _trash_fsync_directory(path.parent)
        if _read_json(path, maximum_bytes=maximum_bytes) != value:
            raise OSError("Nachvalidierung der Laufdatei stimmt nicht überein.")
    except SafeOperationError:
        raise
    except OSError as exc:
        raise _fail(
            f"Laufdatei konnte nicht atomar gespeichert werden: {path.name}: {exc}",
            technical_detail=repr(exc),
        ) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)


def _parse_plan(value: object) -> RunPlan:
    keys = {"schemaVersion", "runId", "operation", "createdUtc", "items", "planHash"}
    if not isinstance(value, dict) or set(value) != keys:
        raise _fail("Laufplan besitzt einen unbekannten Aufbau.")
    if value["schemaVersion"] != RUN_SCHEMA_VERSION:
        raise _fail("Laufplan verwendet eine unbekannte Schemaversion.")
    run_id = value["runId"]
    if not isinstance(run_id, str) or not _RUN_ID_PATTERN.fullmatch(run_id):
        raise _fail("Laufplan enthält keine gültige Lauf-ID.")
    if value["operation"] != RUN_OPERATION:
        raise _fail("Laufplan enthält eine nicht freigegebene Operation.")
    if not isinstance(value["createdUtc"], str) or not value["createdUtc"]:
        raise _fail("Laufplan enthält keinen Erstellungszeitpunkt.")
    raw_items = value["items"]
    if not isinstance(raw_items, list) or not 1 <= len(raw_items) <= MAXIMUM_RUN_ITEMS:
        raise _fail("Laufplan enthält keine zulässige Anzahl von Arbeitsschritten.")
    items: list[RunItem] = []
    seen: set[str] = set()
    for expected, raw in enumerate(raw_items):
        if not isinstance(raw, dict) or set(raw) != {"index", "sourceRelativePath"}:
            raise _fail("Laufplan enthält einen unbekannten Arbeitsschritt.")
        if raw["index"] != expected:
            raise _fail("Laufplanindizes müssen lückenlos bei null beginnen.")
        relative = _safe_relative(raw["sourceRelativePath"])
        if relative in seen:
            raise _fail("Laufplan enthält denselben Projektpfad mehrfach.")
        seen.add(relative)
        items.append(RunItem(expected, relative))
    plan_hash = value["planHash"]
    if not isinstance(plan_hash, str) or not re.fullmatch(r"[a-f0-9]{64}", plan_hash):
        raise _fail("Laufplan enthält keinen gültigen Planhash.")
    if _canonical_hash(value, excluded="planHash") != plan_hash:
        raise _fail("Laufplan wurde nach seiner Erstellung verändert.")
    return RunPlan(
        RUN_SCHEMA_VERSION,
        run_id,
        RUN_OPERATION,
        value["createdUtc"],
        tuple(items),
        plan_hash,
    )


def _parse_current_step(value: object, plan: RunPlan) -> CurrentStep | None:
    if value is None:
        return None
    keys = {"index", "attempt", "actionId", "transactionId", "sourceRelativePath"}
    if not isinstance(value, dict) or set(value) != keys:
        raise _fail("Checkpoint enthält einen unbekannten aktuellen Arbeitsschritt.")
    index = value["index"]
    attempt = value["attempt"]
    if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(plan.items):
        raise _fail("Checkpoint enthält einen ungültigen Schrittindex.")
    if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt < 1:
        raise _fail("Checkpoint enthält keinen gültigen Versuchszähler.")
    action_id = value["actionId"]
    transaction_id = value["transactionId"]
    if not isinstance(action_id, str) or not re.fullmatch(
        r"MMTACTION-[0-9]{8}T[0-9]{6}-[A-F0-9]{12}", action_id
    ):
        raise _fail("Checkpoint enthält keine gültige Aktions-ID.")
    if not isinstance(transaction_id, str) or not re.fullmatch(
        r"MMTTRASH-[0-9]{8}T[0-9]{6}-[A-F0-9]{12}", transaction_id
    ):
        raise _fail("Checkpoint enthält keine gültige Transaktions-ID.")
    relative = _safe_relative(value["sourceRelativePath"])
    if relative != plan.items[index].source_relative_path:
        raise _fail("Checkpoint und Laufplan verweisen auf unterschiedliche Projektpfade.")
    return CurrentStep(index, attempt, action_id, transaction_id, relative)


def _parse_checkpoint(value: object, plan: RunPlan) -> RunCheckpoint:
    keys = {
        "schemaVersion", "runId", "planHash", "state", "nextIndex",
        "completedIndices", "attemptCounts", "currentStep", "generation",
        "createdUtc", "updatedUtc", "cancelRequested", "message",
    }
    if not isinstance(value, dict) or set(value) != keys:
        raise _fail("Laufcheckpoint besitzt einen unbekannten Aufbau.")
    if value["schemaVersion"] != RUN_SCHEMA_VERSION:
        raise _fail("Laufcheckpoint verwendet eine unbekannte Schemaversion.")
    if value["runId"] != plan.run_id or value["planHash"] != plan.plan_hash:
        raise _fail("Laufcheckpoint gehört nicht zum unveränderten Laufplan.")
    state = value["state"]
    if not isinstance(state, str) or state not in _ALLOWED_RUN_STATES:
        raise _fail("Laufcheckpoint enthält einen unbekannten Zustand.")
    next_index = value["nextIndex"]
    if not isinstance(next_index, int) or isinstance(next_index, bool) or not 0 <= next_index <= len(plan.items):
        raise _fail("Laufcheckpoint enthält keinen gültigen nächsten Schritt.")
    completed = value["completedIndices"]
    if not isinstance(completed, list) or any(
        not isinstance(item, int) or isinstance(item, bool) for item in completed
    ):
        raise _fail("Laufcheckpoint enthält ungültige Abschlussindizes.")
    expected_completed = list(range(next_index))
    if completed != expected_completed:
        raise _fail("Laufcheckpoint besitzt keine lückenlose abgeschlossene Schrittfolge.")
    attempts = value["attemptCounts"]
    if (
        not isinstance(attempts, list)
        or len(attempts) != len(plan.items)
        or any(not isinstance(item, int) or isinstance(item, bool) or item < 0 for item in attempts)
    ):
        raise _fail("Laufcheckpoint enthält ungültige Versuchszähler.")
    current = _parse_current_step(value["currentStep"], plan)
    if current is not None:
        if current.index != next_index or attempts[current.index] != current.attempt:
            raise _fail("Aktueller Schritt und Versuchszähler des Checkpoints widersprechen sich.")
    generation = value["generation"]
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 1:
        raise _fail("Laufcheckpoint enthält keine gültige Generation.")
    for field in ("createdUtc", "updatedUtc", "message"):
        if not isinstance(value[field], str):
            raise _fail("Laufcheckpoint enthält ungültige Textfelder.")
    if not isinstance(value["cancelRequested"], bool):
        raise _fail("Laufcheckpoint enthält kein gültiges Abbruchkennzeichen.")
    if state == "completed" and next_index != len(plan.items):
        raise _fail("Abgeschlossener Lauf enthält noch offene Schritte.")
    return RunCheckpoint(
        RUN_SCHEMA_VERSION,
        plan.run_id,
        plan.plan_hash,
        state,
        next_index,
        tuple(completed),
        tuple(attempts),
        current,
        generation,
        value["createdUtc"],
        value["updatedUtc"],
        value["cancelRequested"],
        value["message"],
    )


def _load_snapshot(paths: RunPaths) -> RunSnapshot:
    for directory in (paths.control_directory, paths.runs_directory, paths.run_directory):
        _private_directory(directory, create=False)
    plan = _parse_plan(_read_json(paths.plan_file, maximum_bytes=MAXIMUM_PLAN_BYTES))
    if plan.run_id != paths.run_directory.name:
        raise _fail("Lauf-ID und Laufverzeichnis stimmen nicht überein.")
    checkpoint = _parse_checkpoint(
        _read_json(paths.checkpoint_file, maximum_bytes=MAXIMUM_CHECKPOINT_BYTES),
        plan,
    )
    return RunSnapshot(plan, checkpoint, paths)


def inspect_run(project_root: Path, run_id: str) -> RunSnapshot:
    """Read-only inspection of an existing run."""

    return _load_snapshot(run_paths(project_root, run_id))


class _RunLock:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.descriptor: int | None = None

    def __enter__(self) -> "_RunLock":
        flags = os.O_RDWR | os.O_CREAT
        flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(self.path, flags, PRIVATE_FILE_MODE)
            os.fchmod(descriptor, PRIVATE_FILE_MODE)
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                raise _fail("Laufsperre besitzt einen unsicheren Dateityp.")
            if hasattr(os, "getuid") and metadata.st_uid != os.getuid():
                raise _fail("Laufsperre gehört nicht dem aktuellen Nutzer.")
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise _fail(
                    "Der Lauf wird bereits von einem anderen Prozess bearbeitet.",
                    data_state="Checkpoint, Journal und Nutzdaten blieben unverändert.",
                    next_step="Den aktiven Lauf beenden oder dessen Status erneut prüfen.",
                ) from exc
            self.descriptor = descriptor
            return self
        except SafeOperationError:
            if "descriptor" in locals():
                os.close(descriptor)
            raise
        except OSError as exc:
            if "descriptor" in locals():
                os.close(descriptor)
            raise _fail(f"Laufsperre konnte nicht sicher geöffnet werden: {exc}") from exc

    def __exit__(self, *_exc: object) -> None:
        if self.descriptor is not None:
            try:
                fcntl.flock(self.descriptor, fcntl.LOCK_UN)
            finally:
                os.close(self.descriptor)
                self.descriptor = None


def _write_checkpoint(paths: RunPaths, checkpoint: RunCheckpoint) -> RunCheckpoint:
    updated = replace(
        checkpoint,
        generation=checkpoint.generation + 1,
        updated_utc=_utc_now(),
    )
    _atomic_write_json(
        paths.checkpoint_file,
        updated.as_dict(),
        maximum_bytes=MAXIMUM_CHECKPOINT_BYTES,
    )
    return updated


def _new_checkpoint(plan: RunPlan) -> RunCheckpoint:
    now = _utc_now()
    return RunCheckpoint(
        RUN_SCHEMA_VERSION,
        plan.run_id,
        plan.plan_hash,
        "prepared",
        0,
        (),
        tuple(0 for _ in plan.items),
        None,
        1,
        now,
        now,
        False,
        "Laufplan wurde sicher vorbereitet.",
    )


def _build_plan(run_id: str, items: Iterable[RunItem]) -> RunPlan:
    raw: dict[str, object] = {
        "schemaVersion": RUN_SCHEMA_VERSION,
        "runId": run_id,
        "operation": RUN_OPERATION,
        "createdUtc": _utc_now(),
        "items": [item.as_dict() for item in items],
        "planHash": "",
    }
    raw["planHash"] = _canonical_hash(raw, excluded="planHash")
    return _parse_plan(raw)


def create_run(
    project_root: Path,
    source_paths: Iterable[Path],
    *,
    run_id: str | None = None,
) -> RunSnapshot:
    """Create an immutable long-run plan and initial checkpoint."""

    root = UndoRedoJournal(project_root).paths.project_root
    relative_paths: list[str] = []
    for source in source_paths:
        preview = preview_trash_move(root, source)
        relative_paths.append(preview.original_relative_path)
    if not relative_paths:
        raise _fail("Ein langer Lauf benötigt mindestens einen Arbeitsschritt.")
    if len(relative_paths) > MAXIMUM_RUN_ITEMS:
        raise _fail("Der Lauf überschreitet die maximale Anzahl von Arbeitsschritten.")
    if len(set(relative_paths)) != len(relative_paths):
        raise _fail("Der Lauf enthält denselben Projektpfad mehrfach.")
    normalized = (run_id or create_run_id()).strip().upper()
    paths = run_paths(root, normalized)
    for directory in (paths.control_directory, paths.runs_directory):
        _private_directory(directory, create=True)
    if paths.run_directory.exists() or paths.run_directory.is_symlink():
        raise _fail("Lauf-ID ist bereits belegt; Überschreiben wurde verhindert.")
    created = False
    try:
        paths.run_directory.mkdir(mode=PRIVATE_DIRECTORY_MODE, exist_ok=False)
        os.chmod(paths.run_directory, PRIVATE_DIRECTORY_MODE)
        created = True
        _private_directory(paths.run_directory, create=False)
        plan = _build_plan(
            normalized,
            (RunItem(index, relative) for index, relative in enumerate(relative_paths)),
        )
        checkpoint = _new_checkpoint(plan)
        _atomic_write_json(paths.plan_file, plan.as_dict(), maximum_bytes=MAXIMUM_PLAN_BYTES)
        _atomic_write_json(
            paths.checkpoint_file,
            checkpoint.as_dict(),
            maximum_bytes=MAXIMUM_CHECKPOINT_BYTES,
        )
        _trash_fsync_directory(paths.runs_directory)
        return _load_snapshot(paths)
    except BaseException:
        if created:
            try:
                for item in paths.run_directory.iterdir():
                    if item.is_file() and not item.is_symlink():
                        item.unlink()
                paths.run_directory.rmdir()
            except OSError:
                pass
        raise


def _read_cancel_request(paths: RunPaths) -> bool:
    if not paths.cancel_file.exists():
        return False
    value = _read_json(paths.cancel_file, maximum_bytes=4096)
    if not isinstance(value, dict) or set(value) != {"schemaVersion", "runId", "requestedUtc"}:
        raise _fail("Abbruchanforderung besitzt einen unbekannten Aufbau.")
    if value["schemaVersion"] != RUN_SCHEMA_VERSION or value["runId"] != paths.run_directory.name:
        raise _fail("Abbruchanforderung gehört nicht zu diesem Lauf.")
    if not isinstance(value["requestedUtc"], str) or not value["requestedUtc"]:
        raise _fail("Abbruchanforderung enthält keinen gültigen Zeitpunkt.")
    return True


def request_cancel(project_root: Path, run_id: str) -> RunSnapshot:
    """Persist a cancellation request without competing for the execution lock.

    The request file is the only cross-process write. The active executor remains
    the sole writer of the checkpoint and acknowledges the request at a safe point.
    """

    paths = run_paths(project_root, run_id)
    snapshot = _load_snapshot(paths)
    if snapshot.checkpoint.state in {"completed", "cancelled"}:
        return snapshot
    value = {
        "schemaVersion": RUN_SCHEMA_VERSION,
        "runId": snapshot.plan.run_id,
        "requestedUtc": _utc_now(),
    }
    _atomic_write_json(paths.cancel_file, value, maximum_bytes=4096)
    latest = _load_snapshot(paths)
    if latest.checkpoint.state in {"completed", "cancelled"}:
        _clear_cancel_file(paths)
        return latest
    visible = replace(
        latest.checkpoint,
        cancel_requested=True,
        message="Abbruch wurde angefordert und wird am nächsten sicheren Punkt bestätigt.",
    )
    return RunSnapshot(latest.plan, visible, paths)


def _clear_cancel_file(paths: RunPaths) -> None:
    try:
        if not paths.cancel_file.exists():
            return
        _validate_private_file(paths.cancel_file, maximum_bytes=4096)
        paths.cancel_file.unlink()
        _trash_fsync_directory(paths.run_directory)
    except FileNotFoundError:
        return


def _allocate_step(plan: RunPlan, checkpoint: RunCheckpoint) -> RunCheckpoint:
    index = checkpoint.next_index
    if index >= len(plan.items):
        return checkpoint
    attempts = list(checkpoint.attempt_counts)
    attempts[index] += 1
    item = plan.items[index]
    current = CurrentStep(
        index=index,
        attempt=attempts[index],
        action_id=create_action_id(),
        transaction_id=create_transaction_id(),
        source_relative_path=item.source_relative_path,
    )
    return replace(
        checkpoint,
        state="running",
        attempt_counts=tuple(attempts),
        current_step=current,
        cancel_requested=False,
        message=f"Schritt {index + 1} von {len(plan.items)} ist vorbereitet.",
    )


def _mark_step_completed(checkpoint: RunCheckpoint) -> RunCheckpoint:
    if checkpoint.current_step is None:
        raise _fail("Checkpoint besitzt keinen abschließbaren aktuellen Schritt.")
    index = checkpoint.current_step.index
    if index != checkpoint.next_index:
        raise _fail("Checkpointreihenfolge ist beim Abschluss widersprüchlich.")
    completed = (*checkpoint.completed_indices, index)
    return replace(
        checkpoint,
        state="running",
        next_index=index + 1,
        completed_indices=completed,
        current_step=None,
        message=f"Schritt {index + 1} wurde vollständig abgeschlossen.",
    )


def _preview_from_manifest(root: Path, step: CurrentStep, manifest: TrashManifest) -> TrashPreview:
    if manifest.transaction_id != step.transaction_id:
        raise _fail("Aktueller Laufstep und Transaktionsmanifest besitzen unterschiedliche IDs.")
    if manifest.original_relative_path != step.source_relative_path:
        raise _fail("Aktueller Laufstep und Transaktionsmanifest besitzen unterschiedliche Pfade.")
    transaction = trash_paths(root).transactions_root / step.transaction_id
    return TrashPreview(
        transaction_id=step.transaction_id,
        project_root=root,
        source_path=root / step.source_relative_path,
        original_relative_path=step.source_relative_path,
        transaction_directory=transaction,
        payload_path=transaction / PAYLOAD_NAME,
        manifest_path=transaction / MANIFEST_NAME,
        source_type=manifest.source_type,
        source_device=manifest.source_device,
        source_inode=manifest.source_inode,
        source_mode=manifest.source_mode,
        source_size=manifest.source_size,
        source_mtime_ns=manifest.source_mtime_ns,
        available_bytes=shutil.disk_usage(root).free,
    )


def _execute_checkpointed_trash(
    preview: TrashPreview,
    *,
    prepared_manifest: TrashManifest | None,
    failpoint: Failpoint | None,
) -> TrashResult:
    if prepared_manifest is None:
        _validate_preview(preview)
        if preview.transaction_directory.exists() or preview.transaction_directory.is_symlink():
            raise _fail("Transaktionsziel ist bereits belegt.")
        _prepare_transaction(preview)
        manifest = _manifest_for(preview)
        _write_manifest_atomic(preview.manifest_path, manifest)
    else:
        manifest = prepared_manifest
        if manifest.state != "prepared":
            raise _fail("Nur ein vorbereitetes Manifest darf vor der Dateioperation fortgesetzt werden.")
        if preview.payload_path.exists() or preview.payload_path.is_symlink():
            raise _fail("Vorbereitete Transaktion besitzt bereits einen unerwarteten Payload.")
        _validate_preview(preview)

    _hit(failpoint, "before-file-operation")
    try:
        os.replace(preview.source_path, preview.payload_path)
    except OSError as exc:
        raise _fail(
            f"Atomare Dateioperation des Laufs ist fehlgeschlagen: {exc}",
            data_state="Die Quelle blieb am ursprünglichen Ort; Intent, Plan und Checkpoint bleiben erhalten.",
            technical_detail=repr(exc),
        ) from exc
    _hit(failpoint, "after-file-operation")
    _hit(failpoint, "before-fsync")
    _trash_fsync_directory(preview.source_path.parent)
    _trash_fsync_directory(preview.transaction_directory)
    _hit(failpoint, "after-fsync")
    _hit(failpoint, "before-manifest-completion")
    completed = replace(manifest, state="trashed", completed_utc=_utc_now())
    _write_manifest_atomic(preview.manifest_path, completed)
    _hit(failpoint, "after-manifest-completion")
    return TrashResult(
        preview.transaction_id,
        "trashed",
        preview.manifest_path,
        preview.source_path,
        preview.payload_path,
    )


def _append_apply_recovered(journal: UndoRedoJournal, step: CurrentStep) -> ActionResult:
    journal._append(  # package-internal completion of an already proven transaction
        kind="apply",
        action_id=step.action_id,
        transaction_id=step.transaction_id,
        original_relative_path=step.source_relative_path,
        recovered=True,
    )
    return ActionResult(step.action_id, step.transaction_id, "trashed", False, recovered=True)


def _reconcile_current_step(
    journal: UndoRedoJournal,
    checkpoint: RunCheckpoint,
) -> tuple[RunCheckpoint, bool]:
    step = checkpoint.current_step
    if step is None:
        return checkpoint, False
    snapshot = journal.inspect()
    action = next((item for item in snapshot.actions if item.action_id == step.action_id), None)
    source = journal.paths.project_root / step.source_relative_path
    transaction = trash_paths(journal.paths.project_root).transactions_root / step.transaction_id
    payload = transaction / PAYLOAD_NAME

    if action is None:
        if source.exists() and not source.is_symlink() and not transaction.exists():
            return checkpoint, False
        raise _fail("Checkpoint besitzt einen Arbeitsschritt ohne eindeutigen Journal- und Dateizustand.")

    if action.current_transaction_id != step.transaction_id or action.original_relative_path != step.source_relative_path:
        raise _fail("Checkpoint und Aktionsjournal verweisen auf unterschiedliche Transaktionsdaten.")
    if action.status == "trashed" and not action.pending_kind:
        manifest = inspect_transaction(journal.paths.project_root, step.transaction_id)
        if manifest.state != "trashed" or source.exists() or source.is_symlink():
            raise _fail("Abgeschlossene Journalaktion besitzt keinen eindeutigen Papierkorbzustand.")
        _validate_payload(
            payload,
            manifest,
            _project_metadata(journal.paths.project_root),
        )
        return _mark_step_completed(checkpoint), True
    if action.status in {"restored", "cancelled"} and not action.pending_kind:
        raise _fail("Ein Batch-Laufstep befindet sich in einem unerwarteten Endzustand.")
    if action.pending_kind != "prepare":
        raise _fail("Ein Batch-Laufstep besitzt einen nicht fortsetzbaren Journal-Intent.")

    try:
        manifest = inspect_transaction(journal.paths.project_root, step.transaction_id)
    except SafeOperationError:
        if source.exists() and not source.is_symlink() and not transaction.exists():
            return checkpoint, False
        raise

    if manifest.state == "prepared" and source.exists() and not payload.exists():
        return checkpoint, False
    if (
        manifest.state in {"prepared", "trashed"}
        and payload.exists()
        and not payload.is_symlink()
        and not source.exists()
        and not source.is_symlink()
    ):
        _validate_payload(
            payload,
            manifest,
            _project_metadata(journal.paths.project_root),
        )
        if manifest.state == "prepared":
            _trash_fsync_directory(source.parent)
            _trash_fsync_directory(transaction)
            _write_manifest_atomic(
                transaction / MANIFEST_NAME,
                replace(manifest, state="trashed", completed_utc=_utc_now()),
            )
        _append_apply_recovered(journal, step)
        return _mark_step_completed(checkpoint), True
    raise _fail("Unvollständiger Laufstep besitzt einen widersprüchlichen Datei- und Manifestzustand.")


def _perform_current_step(
    journal: UndoRedoJournal,
    checkpoint: RunCheckpoint,
    *,
    failpoint: Failpoint | None,
) -> ActionResult:
    step = checkpoint.current_step
    if step is None:
        raise _fail("Es ist kein aktueller Laufstep vorbereitet.")
    snapshot = journal.inspect()
    action = next((item for item in snapshot.actions if item.action_id == step.action_id), None)
    source = journal.paths.project_root / step.source_relative_path
    transaction = trash_paths(journal.paths.project_root).transactions_root / step.transaction_id

    prepared_manifest: TrashManifest | None = None
    if action is None:
        if transaction.exists() or not source.exists() or source.is_symlink():
            raise _fail("Neuer Laufstep besitzt vor dem Intent keinen sicheren Ausgangszustand.")
        _hit(failpoint, "before-intent")
        journal._append(
            kind="prepare",
            action_id=step.action_id,
            transaction_id=step.transaction_id,
            original_relative_path=step.source_relative_path,
        )
        _hit(failpoint, "after-intent")
        preview = preview_trash_move(
            journal.paths.project_root,
            source,
            transaction_id=step.transaction_id,
        )
    else:
        if action.pending_kind != "prepare":
            raise _fail("Fortzusetzender Laufstep besitzt keinen vorbereiteten Intent.")
        if transaction.exists():
            prepared_manifest = inspect_transaction(
                journal.paths.project_root,
                step.transaction_id,
            )
            preview = _preview_from_manifest(
                journal.paths.project_root,
                step,
                prepared_manifest,
            )
        else:
            if not source.exists() or source.is_symlink():
                raise _fail("Vorbereiteter Laufstep besitzt keine sichere Quelle.")
            preview = preview_trash_move(
                journal.paths.project_root,
                source,
                transaction_id=step.transaction_id,
            )

    result = _execute_checkpointed_trash(
        preview,
        prepared_manifest=prepared_manifest,
        failpoint=failpoint,
    )
    _hit(failpoint, "before-journal-completion")
    journal._append(
        kind="apply",
        action_id=step.action_id,
        transaction_id=result.transaction_id,
        original_relative_path=step.source_relative_path,
    )
    _hit(failpoint, "after-journal-completion")
    return ActionResult(step.action_id, result.transaction_id, "trashed", True)


def resume_run(
    project_root: Path,
    run_id: str,
    *,
    allow_cancelled: bool = False,
    max_steps: int | None = None,
    failpoint: Failpoint | None = None,
) -> RunResult:
    """Resume a run idempotently from its persisted checkpoint and journals."""

    paths = run_paths(project_root, run_id)
    changed = False
    recovered = False
    with _RunLock(paths.lock_file):
        snapshot = _load_snapshot(paths)
        plan = snapshot.plan
        checkpoint = snapshot.checkpoint
        if checkpoint.state == "completed":
            return RunResult(plan.run_id, "completed", checkpoint.next_index, len(plan.items), False, message="Lauf war bereits abgeschlossen.")
        if checkpoint.state == "blocked":
            raise _fail("Der Lauf ist als blockiert markiert und darf nicht automatisch fortgesetzt werden.")
        if checkpoint.state == "cancelled" and not allow_cancelled:
            return RunResult(plan.run_id, "cancelled", checkpoint.next_index, len(plan.items), False, message="Lauf bleibt kontrolliert abgebrochen.")
        if checkpoint.state == "cancelled" and allow_cancelled:
            _clear_cancel_file(paths)
            checkpoint = _write_checkpoint(
                paths,
                replace(
                    checkpoint,
                    state="running",
                    cancel_requested=False,
                    message="Kontrolliert abgebrochener Lauf wird ausdrücklich fortgesetzt.",
                ),
            )
            changed = True

        journal = UndoRedoJournal(paths.project_root)
        processed = 0
        try:
            while checkpoint.next_index < len(plan.items):
                checkpoint, reconciled = _reconcile_current_step(journal, checkpoint)
                if reconciled:
                    checkpoint = _write_checkpoint(paths, checkpoint)
                    changed = True
                    recovered = True
                    continue

                if checkpoint.current_step is None:
                    if _read_cancel_request(paths):
                        checkpoint = _write_checkpoint(
                            paths,
                            replace(
                                checkpoint,
                                state="cancelled",
                                cancel_requested=True,
                                message="Abbruch wurde an einem sicheren Punkt bestätigt.",
                            ),
                        )
                        _clear_cancel_file(paths)
                        return RunResult(plan.run_id, "cancelled", checkpoint.next_index, len(plan.items), True, recovered, checkpoint.message)
                    checkpoint = _write_checkpoint(paths, _allocate_step(plan, checkpoint))
                    changed = True

                # Cancellation is intentionally not honored after an intent exists. The
                # current atomic step is completed first, then the next safe point checks it.
                _perform_current_step(journal, checkpoint, failpoint=failpoint)
                checkpoint = _write_checkpoint(paths, _mark_step_completed(checkpoint))
                changed = True
                processed += 1
                if max_steps is not None and processed >= max(0, max_steps):
                    return RunResult(plan.run_id, "running", checkpoint.next_index, len(plan.items), changed, recovered, "Schrittlimit erreicht; Lauf kann idempotent fortgesetzt werden.")
        except SafeOperationError as exc:
            if checkpoint.state not in {"completed", "cancelled", "blocked"}:
                try:
                    checkpoint = _write_checkpoint(
                        paths,
                        replace(
                            checkpoint,
                            state="blocked",
                            message=f"Lauf wurde wegen eines widersprüchlichen Sicherheitszustands blockiert: {exc}",
                        ),
                    )
                except SafeOperationError:
                    pass
            raise

        checkpoint = _write_checkpoint(
            paths,
            replace(
                checkpoint,
                state="completed",
                current_step=None,
                cancel_requested=False,
                message="Alle Laufsteps und Journalabschlüsse sind vollständig bestätigt.",
            ),
        )
        _clear_cancel_file(paths)
        return RunResult(plan.run_id, "completed", checkpoint.next_index, len(plan.items), True, recovered, checkpoint.message)
