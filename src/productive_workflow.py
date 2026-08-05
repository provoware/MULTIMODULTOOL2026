"""Preview-first productive project analysis and atomic file operations."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import fcntl, hashlib, json, mimetypes, os, re, shutil, stat
from pathlib import Path
from typing import Callable, Sequence
from uuid import uuid4

from .error_events import SafeOperationError

CONTROL = ".multimodultool2026"
OPS = "operations"
REPORTS = "reports"
SCHEMA = 1
DIR_MODE, FILE_MODE = 0o700, 0o600
MAX_ENTRIES, MAX_ITEMS = 100_000, 10_000
HASH_LIMIT = 64 * 1024**3
OP_RE = re.compile(r"^MMTOP-[0-9]{8}T[0-9]{6}-[A-F0-9]{12}$")
BAD_ROOTS = tuple(Path(p) for p in ("/", "/boot", "/dev", "/etc", "/proc", "/run", "/sys", "/usr", "/var"))
Progress = Callable[[int, int, str], None]
Cancel = Callable[[], bool]
Failpoint = Callable[[str, "OperationItem"], None]


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _fail(cause: str, *, state: str = "Projektdateien und private Steuerdaten blieben nachvollziehbar.") -> SafeOperationError:
    return SafeOperationError(
        category="productive-workflow", cause=cause,
        consequence="Der produktive Schritt wurde kontrolliert blockiert.", data_state=state,
        solution="Projektgrenze, Rechte, Vorschau, Konflikte und Dateifingerabdrücke prüfen.",
        next_step="Eine neue Vorschau erzeugen oder den gespeicherten Operationszustand abgleichen.",
    )


def _abs(path: Path) -> Path:
    path = path.expanduser()
    if not path.is_absolute():
        raise _fail("Projektpfad muss absolut sein.")
    return Path(os.path.abspath(os.fspath(path)))


def _relative(path: Path, root: Path, label: str) -> str:
    try:
        value = path.relative_to(root)
    except ValueError as exc:
        raise _fail(f"{label} liegt außerhalb des Projekts.") from exc
    if value == Path(".") or value.is_absolute() or ".." in value.parts or CONTROL in value.parts:
        raise _fail(f"{label} überschreitet die freigegebene Projektgrenze.")
    return value.as_posix()


def _rel(value: str, label: str) -> str:
    p = Path(value)
    if not value or p.is_absolute() or p == Path(".") or ".." in p.parts or CONTROL in p.parts:
        raise _fail(f"{label} ist kein sicherer relativer Projektpfad.")
    return p.as_posix()


def _no_links(path: Path, root: Path) -> None:
    current = root
    if root.is_symlink():
        raise _fail("Projektstamm darf kein Symlink sein.")
    for part in path.relative_to(root).parts:
        current /= part
        if current.is_symlink():
            raise _fail(f"Symbolische Pfadkomponente ist gesperrt: {current.name}")


def _finger(meta: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return meta.st_dev, meta.st_ino, stat.S_IMODE(meta.st_mode), meta.st_size, meta.st_mtime_ns, meta.st_nlink


def _private_dir(path: Path) -> None:
    if path.is_symlink():
        raise _fail(f"Privater Pfad ist ein Symlink: {path.name}")
    path.mkdir(mode=DIR_MODE, exist_ok=True)
    os.chmod(path, DIR_MODE)
    meta = path.lstat()
    if not stat.S_ISDIR(meta.st_mode) or stat.S_IMODE(meta.st_mode) & 0o077:
        raise _fail(f"Privater Ordner benötigt 0700: {path.name}")


def _atomic(path: Path, data: bytes, limit: int = 16 * 1024**2) -> None:
    if len(data) > limit or path.is_symlink():
        raise _fail(f"Private Datei ist zu groß oder ein Symlink: {path.name}")
    tmp = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    fd = None
    try:
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), FILE_MODE)
        os.fchmod(fd, FILE_MODE)
        os.write(fd, data)
        os.fsync(fd)
        os.close(fd)
        fd = None
        os.replace(tmp, path)
        os.chmod(path, FILE_MODE)
    finally:
        if fd is not None:
            os.close(fd)
        tmp.unlink(missing_ok=True)


def _json(path: Path, value: dict) -> None:
    _atomic(path, (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode())


def _read(path: Path) -> dict:
    if path.is_symlink() or not path.is_file() or stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise _fail(f"Private Operationsdatei ist unsicher: {path.name}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise _fail(f"Private Operationsdatei ist beschädigt: {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise _fail(f"Private Operationsdatei hat falschen Aufbau: {path.name}")
    return value


@dataclass(frozen=True)
class ProjectSafety:
    root: Path
    device: int
    owner_uid: int
    free_bytes: int
    total_bytes: int
    is_mount_root: bool
    readable: bool
    writable: bool
    control_directory: Path


@dataclass(frozen=True)
class InventoryEntry:
    relative_path: str
    entry_type: str
    size: int
    mtime_ns: int
    mode: int
    device: int
    inode: int
    link_count: int
    extension: str
    category: str
    mime_type: str
    flags: tuple[str, ...] = ()

    @property
    def fingerprint(self):
        return self.device, self.inode, self.mode, self.size, self.mtime_ns, self.link_count


@dataclass(frozen=True)
class InventorySnapshot:
    project: ProjectSafety
    created_utc: str
    entries: tuple[InventoryEntry, ...]
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    @property
    def files(self):
        return tuple(e for e in self.entries if e.entry_type == "file")

    @property
    def directories(self):
        return tuple(e for e in self.entries if e.entry_type == "directory")

    @property
    def total_file_bytes(self):
        return sum(e.size for e in self.files)

    @property
    def symlink_count(self):
        return sum(e.entry_type == "symlink" for e in self.entries)


@dataclass(frozen=True)
class DuplicateGroup:
    sha256: str
    size: int
    relative_paths: tuple[str, ...]

    @property
    def reclaimable_bytes(self):
        return self.size * (len(self.relative_paths) - 1)


@dataclass(frozen=True)
class DuplicateResult:
    created_utc: str
    groups: tuple[DuplicateGroup, ...]
    hashed_files: int
    hashed_bytes: int
    skipped: tuple[str, ...] = ()

    @property
    def duplicate_files(self):
        return sum(len(g.relative_paths) for g in self.groups)

    @property
    def reclaimable_bytes(self):
        return sum(g.reclaimable_bytes for g in self.groups)


@dataclass(frozen=True)
class RenameRule:
    prefix: str = ""
    suffix: str = ""
    search: str = ""
    replacement: str = ""
    case_mode: str = "keep"
    add_number: bool = False
    number_start: int = 1
    number_padding: int = 3


@dataclass(frozen=True)
class OperationItem:
    index: int
    source_relative_path: str
    target_relative_path: str
    source_device: int
    source_inode: int
    source_mode: int
    source_size: int
    source_mtime_ns: int
    source_link_count: int

    @property
    def fingerprint(self):
        return self.source_device, self.source_inode, self.source_mode, self.source_size, self.source_mtime_ns, self.source_link_count

    def as_dict(self):
        return {"index": self.index, "source": self.source_relative_path, "target": self.target_relative_path, "fingerprint": list(self.fingerprint)}


@dataclass(frozen=True)
class OperationPlan:
    schema_version: int
    operation_id: str
    operation: str
    created_utc: str
    project_device: int
    items: tuple[OperationItem, ...]
    destination_directories: tuple[str, ...]
    plan_hash: str

    def as_dict(self):
        return {"schemaVersion": self.schema_version, "operationId": self.operation_id, "operation": self.operation, "createdUtc": self.created_utc, "projectDevice": self.project_device, "items": [i.as_dict() for i in self.items], "destinationDirectories": list(self.destination_directories), "planHash": self.plan_hash}


@dataclass(frozen=True)
class OperationCheckpoint:
    state: str
    completed_indices: tuple[int, ...]
    undone_indices: tuple[int, ...]
    created_directories: tuple[str, ...]
    message: str

    def as_dict(self, plan: OperationPlan):
        return {"schemaVersion": SCHEMA, "operationId": plan.operation_id, "planHash": plan.plan_hash, "state": self.state, "completedIndices": list(self.completed_indices), "undoneIndices": list(self.undone_indices), "createdDirectories": list(self.created_directories), "updatedUtc": _utc(), "message": self.message}


@dataclass(frozen=True)
class OperationResult:
    operation_id: str
    operation: str
    state: str
    completed_count: int
    total_count: int
    changed: bool
    report_json: Path | None = None
    report_markdown: Path | None = None
    message: str = ""


def validate_project_root(path: Path, *, require_writable: bool = True, minimum_free_bytes: int = 16 * 1024**2) -> ProjectSafety:
    root = _abs(path)
    if root == Path.home() or any(root == p or (p != Path("/") and root.is_relative_to(p)) for p in BAD_ROOTS):
        raise _fail("System-, Home-Stamm oder besonders sensibler Pfad ist als Projekt gesperrt.")
    _no_links(root, Path("/"))
    try:
        meta = root.lstat()
    except OSError as exc:
        raise _fail(f"Projektordner ist nicht lesbar: {exc}") from exc
    if not stat.S_ISDIR(meta.st_mode) or (hasattr(os, "getuid") and meta.st_uid != os.getuid()):
        raise _fail("Projekt muss ein eigener regulärer Linux-Ordner sein.")
    readable = os.access(root, os.R_OK | os.X_OK)
    writable = os.access(root, os.W_OK | os.X_OK)
    if not readable or (require_writable and not writable):
        raise _fail("Projekt besitzt nicht die erforderlichen Rechte.")
    usage = shutil.disk_usage(root)
    if require_writable and usage.free < minimum_free_bytes:
        raise _fail("Freier Speicher reicht für sichere Metadaten nicht aus.")
    return ProjectSafety(root, meta.st_dev, getattr(meta, "st_uid", -1), usage.free, usage.total, os.path.ismount(root), readable, writable, root / CONTROL)


def _category(ext: str) -> str:
    if ext in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}:
        return "Bilder"
    if ext in {".mp3", ".wav", ".flac", ".ogg", ".m4a"}:
        return "Audio"
    if ext in {".mp4", ".mkv", ".mov", ".avi", ".webm"}:
        return "Video"
    if ext in {".txt", ".md", ".pdf", ".doc", ".docx", ".odt", ".csv", ".xlsx", ".ods"}:
        return "Dokumente"
    if ext in {".zip", ".tar", ".gz", ".xz", ".7z", ".rar"}:
        return "Archive"
    return "Sonstige"


def analyze_project(project_root: Path, *, maximum_entries: int = MAX_ENTRIES, progress: Progress | None = None, should_cancel: Cancel | None = None) -> InventorySnapshot:
    project = validate_project_root(project_root, require_writable=False)
    entries, warnings, errors = [], [], []
    stack = [project.root]
    while stack:
        directory = stack.pop()
        try:
            children = sorted(os.scandir(directory), key=lambda e: (e.name.casefold(), e.name))
        except OSError as exc:
            errors.append(f"{_relative(directory, project.root, 'Ordner')}: {exc}")
            continue
        for child in children:
            if should_cancel and should_cancel():
                return InventorySnapshot(project, _utc(), tuple(entries), tuple(warnings + ["Analyse kontrolliert abgebrochen."]), tuple(errors))
            if len(entries) >= maximum_entries:
                raise _fail("Bestandsanalyse überschreitet das Eintragslimit.")
            path = Path(child.path)
            rel = _relative(path, project.root, "Eintrag")
            if rel.split("/")[0] == CONTROL:
                continue
            try:
                meta = child.stat(follow_symlinks=False)
            except OSError as exc:
                errors.append(f"{rel}: {exc}")
                continue
            if stat.S_ISLNK(meta.st_mode):
                typ = "symlink"
                warnings.append(f"Symlink ausgeschlossen: {rel}")
            elif stat.S_ISDIR(meta.st_mode):
                typ = "directory"
                if meta.st_dev == project.device and not os.path.ismount(path):
                    stack.append(path)
                elif path != project.root:
                    warnings.append(f"Mountgrenze nicht betreten: {rel}")
            elif stat.S_ISREG(meta.st_mode):
                typ = "file"
            else:
                typ = "other"
            ext = path.suffix.lower() if typ == "file" else ""
            mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            flags = []
            if typ == "file" and meta.st_nlink != 1:
                flags.append("hardlink-ausgeschlossen")
            if path.name.startswith("."):
                flags.append("versteckt")
            entries.append(InventoryEntry(rel, typ, meta.st_size, meta.st_mtime_ns, stat.S_IMODE(meta.st_mode), meta.st_dev, meta.st_ino, meta.st_nlink, ext, _category(ext), mime, tuple(flags)))
            if progress:
                progress(len(entries), maximum_entries, rel)
    entries.sort(key=lambda e: (e.relative_path.casefold(), e.relative_path))
    return InventorySnapshot(project, _utc(), tuple(entries), tuple(dict.fromkeys(warnings)), tuple(errors))


def _unchanged(root: Path, entry: InventoryEntry) -> Path:
    path = root / _rel(entry.relative_path, "Dateipfad")
    _no_links(path, root)
    if path.is_symlink() or not path.is_file() or _finger(path.lstat()) != entry.fingerprint:
        raise _fail(f"Datei wurde seit der Analyse verändert: {entry.relative_path}")
    return path


def find_duplicates(snapshot: InventorySnapshot, *, maximum_hash_bytes: int = HASH_LIMIT, progress: Progress | None = None, should_cancel: Cancel | None = None) -> DuplicateResult:
    by_size = {}
    for entry in snapshot.files:
        if entry.link_count == 1 and entry.device == snapshot.project.device:
            by_size.setdefault(entry.size, []).append(entry)
    candidates = [entry for size, group in by_size.items() if size > 0 and len(group) > 1 for entry in group]
    hashes, total, skipped = {}, 0, []
    for index, entry in enumerate(candidates, 1):
        if should_cancel and should_cancel():
            skipped.append("Duplikatsuche kontrolliert abgebrochen.")
            break
        path = _unchanged(snapshot.project.root, entry)
        before = path.lstat()
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            while block := handle.read(1024**2):
                total += len(block)
                if total > maximum_hash_bytes:
                    raise _fail("Duplikatsuche überschreitet das Leselimit.")
                digest.update(block)
        if _finger(path.lstat()) != _finger(before):
            raise _fail(f"Datei änderte sich während des Hashens: {entry.relative_path}")
        hashes.setdefault((entry.size, digest.hexdigest()), []).append(entry.relative_path)
        if progress:
            progress(index, len(candidates), entry.relative_path)
    groups = tuple(DuplicateGroup(sha, size, tuple(sorted(paths, key=str.casefold))) for (size, sha), paths in sorted(hashes.items()) if len(paths) > 1)
    return DuplicateResult(_utc(), groups, len(candidates) - len(skipped), total, tuple(skipped))


def _name(value: str) -> str:
    value = value.strip()
    if not value or value in {".", ".."} or "/" in value or "\\" in value or "\0" in value or len(value.encode()) > 240:
        raise _fail("Zielname ist leer, unsicher oder zu lang.")
    return value


def _plan_hash(value: dict) -> str:
    value = dict(value)
    value.pop("planHash", None)
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _make_plan(snapshot: InventorySnapshot, operation: str, pairs: Sequence[tuple[InventoryEntry, str]], directories: Sequence[str]) -> OperationPlan:
    if not 1 <= len(pairs) <= MAX_ITEMS:
        raise _fail("Operationsplan enthält keine zulässige Dateianzahl.")
    sources = {entry.relative_path for entry, _ in pairs}
    targets, items = set(), []
    for index, (entry, target) in enumerate(pairs):
        target = _rel(target, "Zielpfad")
        if target in sources or target.casefold() in {value.casefold() for value in targets}:
            raise _fail(f"Ziel ist zyklisch oder doppelt: {target}")
        destination = snapshot.project.root / target
        if destination.exists() or destination.is_symlink():
            raise _fail(f"Ziel ist bereits belegt: {target}")
        _unchanged(snapshot.project.root, entry)
        targets.add(target)
        items.append(OperationItem(index, entry.relative_path, target, *entry.fingerprint))
    operation_id = f"MMTOP-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}-{uuid4().hex[:12].upper()}"
    raw = {"schemaVersion": SCHEMA, "operationId": operation_id, "operation": operation, "createdUtc": _utc(), "projectDevice": snapshot.project.device, "items": [item.as_dict() for item in items], "destinationDirectories": sorted(set(directories)), "planHash": ""}
    return OperationPlan(SCHEMA, operation_id, operation, raw["createdUtc"], snapshot.project.device, tuple(items), tuple(raw["destinationDirectories"]), _plan_hash(raw))


def plan_mass_rename(snapshot: InventorySnapshot, relative_paths: Sequence[str], rule: RenameRule) -> OperationPlan:
    chosen = set(relative_paths)
    known = {entry.relative_path: entry for entry in snapshot.files}
    pairs = []
    for offset, path in enumerate(sorted(chosen, key=str.casefold)):
        if path not in known:
            raise _fail(f"Ausgewählte Datei fehlt im Analysebestand: {path}")
        entry = known[path]
        source = Path(path)
        extension = "".join(source.suffixes[-2:]) if len(source.suffixes) >= 2 and source.suffixes[-2] == ".tar" else source.suffix
        base = source.name[:-len(extension)] if extension else source.name
        if rule.search:
            base = base.replace(rule.search, rule.replacement)
        if rule.case_mode == "lower":
            base = base.lower()
        elif rule.case_mode == "upper":
            base = base.upper()
        new_name = f"{rule.prefix}{base}{rule.suffix}"
        if rule.add_number:
            new_name += f"_{rule.number_start + offset:0{rule.number_padding}d}"
        target = (source.parent / _name(new_name + extension)).as_posix()
        if target != path:
            pairs.append((entry, target))
    if not pairs:
        raise _fail("Umbenennungsregel erzeugt keine Änderung.")
    return _make_plan(snapshot, "rename", pairs, ())


def plan_organization(snapshot: InventorySnapshot, *, rule: str = "category", destination_root: str = "Sortiert") -> OperationPlan:
    root = _name(destination_root)
    pairs, directories = [], []
    for entry in snapshot.files:
        if entry.link_count != 1 or Path(entry.relative_path).parts[0].casefold() == root.casefold():
            continue
        if rule == "category":
            bucket = entry.category
        elif rule == "extension":
            bucket = entry.extension[1:].upper() if entry.extension else "OHNE_ENDUNG"
        elif rule == "year":
            bucket = datetime.fromtimestamp(entry.mtime_ns / 1e9).strftime("%Y")
        else:
            raise _fail("Organisationsregel ist unbekannt.")
        directory = (Path(root) / _name(bucket)).as_posix()
        directories.append(directory)
        pairs.append((entry, (Path(directory) / Path(entry.relative_path).name).as_posix()))
    if not pairs:
        raise _fail("Keine organisierbaren Dateien gefunden.")
    return _make_plan(snapshot, "organize", pairs, directories)


def _paths(root: Path, operation_id: str):
    if not OP_RE.fullmatch(operation_id):
        raise _fail("Operations-ID ist ungültig.")
    base = root / CONTROL / OPS / operation_id
    return base, base / "plan.json", base / "checkpoint.json", base / "operation.lock"


def _store_plan(root: Path, plan: OperationPlan):
    base, plan_file, checkpoint_file, lock_file = _paths(root, plan.operation_id)
    if base.exists() or base.is_symlink():
        raise _fail("Operations-ID ist bereits belegt.")
    _private_dir(root / CONTROL)
    _private_dir(root / CONTROL / OPS)
    _private_dir(base)
    _json(plan_file, plan.as_dict())
    _json(checkpoint_file, OperationCheckpoint("prepared", (), (), (), "Vorschau gespeichert.").as_dict(plan))
    _atomic(lock_file, b"lock\n")
    return base, plan_file, checkpoint_file, lock_file


def _load(root: Path, operation_id: str):
    paths = _paths(root, operation_id)
    plan_raw = _read(paths[1])
    checkpoint_raw = _read(paths[2])
    items = []
    for raw in plan_raw.get("items", []):
        items.append(OperationItem(raw["index"], _rel(raw["source"], "Quelle"), _rel(raw["target"], "Ziel"), *raw["fingerprint"]))
    plan = OperationPlan(plan_raw["schemaVersion"], plan_raw["operationId"], plan_raw["operation"], plan_raw["createdUtc"], plan_raw["projectDevice"], tuple(items), tuple(plan_raw["destinationDirectories"]), plan_raw["planHash"])
    if _plan_hash(plan.as_dict()) != plan.plan_hash:
        raise _fail("Operationsplanhash ist ungültig.")
    checkpoint = OperationCheckpoint(checkpoint_raw["state"], tuple(checkpoint_raw["completedIndices"]), tuple(checkpoint_raw["undoneIndices"]), tuple(checkpoint_raw["createdDirectories"]), checkpoint_raw["message"])
    return paths, plan, checkpoint


def _write_checkpoint(path: Path, plan: OperationPlan, checkpoint: OperationCheckpoint):
    _json(path, checkpoint.as_dict(plan))


def _location(project: ProjectSafety, item: OperationItem) -> str:
    source = project.root / item.source_relative_path
    target = project.root / item.target_relative_path
    source_exists = source.exists() or source.is_symlink()
    target_exists = target.exists() or target.is_symlink()
    if source_exists == target_exists:
        raise _fail(f"Quelle/Ziel-Zustand ist nicht eindeutig: {item.source_relative_path}")
    current = source if source_exists else target
    if current.is_symlink() or not current.is_file() or _finger(current.lstat()) != item.fingerprint:
        raise _fail(f"Fingerabdruck stimmt nicht: {_relative(current, project.root, 'Operationspfad')}")
    return "source" if source_exists else "target"


def reconcile_operation(project_root: Path, operation_id: str) -> OperationCheckpoint:
    project = validate_project_root(project_root)
    paths, plan, checkpoint = _load(project.root, operation_id)
    completed = tuple(item.index for item in plan.items if _location(project, item) == "target")
    state = "completed" if len(completed) == len(plan.items) else "prepared" if not completed else "blocked"
    result = OperationCheckpoint(state, completed, tuple(index for index in checkpoint.undone_indices if index not in completed), checkpoint.created_directories, "Dateipfade und Fingerabdrücke wurden mit dem Plan abgeglichen.")
    _write_checkpoint(paths[2], plan, result)
    return result


def _mkdirs(project: ProjectSafety, values: Sequence[str]) -> tuple[str, ...]:
    created = []
    for relative in sorted(set(values), key=lambda value: (len(Path(value).parts), value.casefold())):
        current = project.root
        for part in Path(_rel(relative, "Zielordner")).parts:
            current /= part
            if current.exists():
                if current.is_symlink() or not current.is_dir() or current.stat().st_dev != project.device:
                    raise _fail(f"Zielordner ist unsicher: {relative}")
            else:
                current.mkdir(mode=0o750)
                created.append(_relative(current, project.root, "Zielordner"))
    return tuple(created)


def _continue(project, paths, plan, checkpoint, progress, should_cancel, failpoint):
    completed = list(checkpoint.completed_indices)
    for item in plan.items:
        if item.index in completed:
            continue
        if should_cancel and should_cancel():
            checkpoint = replace(checkpoint, state="cancelled", completed_indices=tuple(completed), message="Vor dem nächsten Datei-Intent abgebrochen.")
            _write_checkpoint(paths[2], plan, checkpoint)
            return checkpoint
        if _location(project, item) == "source":
            source = project.root / item.source_relative_path
            target = project.root / item.target_relative_path
            if target.exists() or target.is_symlink() or not target.parent.is_dir() or target.parent.is_symlink():
                raise _fail(f"Ziel ist belegt oder unsicher: {item.target_relative_path}")
            if failpoint:
                failpoint("before-file-operation", item)
            os.replace(source, target)
            if failpoint:
                failpoint("after-file-operation", item)
            if _location(project, item) != "target":
                raise _fail(f"Nachprüfung fehlgeschlagen: {item.target_relative_path}")
        completed.append(item.index)
        checkpoint = replace(checkpoint, state="running", completed_indices=tuple(completed), message=f"{len(completed)} von {len(plan.items)} bestätigt.")
        _write_checkpoint(paths[2], plan, checkpoint)
        if progress:
            progress(len(completed), len(plan.items), item.target_relative_path)
    checkpoint = replace(checkpoint, state="completed", completed_indices=tuple(completed), message="Alle Dateioperationen ausgeführt und nachvalidiert.")
    _write_checkpoint(paths[2], plan, checkpoint)
    return checkpoint


def execute_operation(project_root: Path, plan: OperationPlan, *, progress: Progress | None = None, should_cancel: Cancel | None = None, write_result_report: bool = True, failpoint: Failpoint | None = None) -> OperationResult:
    project = validate_project_root(project_root)
    if project.device != plan.project_device or _plan_hash(plan.as_dict()) != plan.plan_hash:
        raise _fail("Plan passt nicht mehr zum Projekt.")
    for item in plan.items:
        if _location(project, item) != "source":
            raise _fail(f"Quelle ist nicht mehr am Vorschaupfad: {item.source_relative_path}")
    paths = _store_plan(project.root, plan)
    created = _mkdirs(project, plan.destination_directories)
    checkpoint = OperationCheckpoint("running", (), (), created, "Produktiver Lauf gestartet.")
    _write_checkpoint(paths[2], plan, checkpoint)
    descriptor = os.open(paths[3], os.O_RDWR | getattr(os, "O_NOFOLLOW", 0))
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        checkpoint = _continue(project, paths, plan, checkpoint, progress, should_cancel, failpoint)
    except BaseException:
        try:
            checkpoint = reconcile_operation(project.root, plan.operation_id)
            _write_checkpoint(paths[2], plan, replace(checkpoint, state="blocked", message="Unterbrechung abgeglichen; kontrollierte Fortsetzung oder Undo erforderlich."))
        except SafeOperationError:
            pass
        raise
    finally:
        os.close(descriptor)
    reports = write_operation_report(project.root, plan.operation_id) if write_result_report else (None, None)
    return OperationResult(plan.operation_id, plan.operation, checkpoint.state, len(checkpoint.completed_indices), len(plan.items), bool(checkpoint.completed_indices), *reports, checkpoint.message)


def resume_operation(project_root: Path, operation_id: str, *, progress: Progress | None = None, should_cancel: Cancel | None = None, failpoint: Failpoint | None = None) -> OperationResult:
    project = validate_project_root(project_root)
    paths, plan, checkpoint = _load(project.root, operation_id)
    checkpoint = reconcile_operation(project.root, operation_id)
    if checkpoint.state == "completed":
        return OperationResult(plan.operation_id, plan.operation, "completed", len(plan.items), len(plan.items), False, message=checkpoint.message)
    created = set(checkpoint.created_directories)
    created.update(_mkdirs(project, plan.destination_directories))
    checkpoint = replace(checkpoint, state="running", created_directories=tuple(sorted(created)))
    descriptor = os.open(paths[3], os.O_RDWR | getattr(os, "O_NOFOLLOW", 0))
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        checkpoint = _continue(project, paths, plan, checkpoint, progress, should_cancel, failpoint)
    finally:
        os.close(descriptor)
    reports = write_operation_report(project.root, operation_id)
    return OperationResult(plan.operation_id, plan.operation, checkpoint.state, len(checkpoint.completed_indices), len(plan.items), True, *reports, checkpoint.message)


def undo_operation(project_root: Path, operation_id: str, *, progress: Progress | None = None) -> OperationResult:
    project = validate_project_root(project_root)
    paths, plan, checkpoint = _load(project.root, operation_id)
    checkpoint = reconcile_operation(project.root, operation_id)
    completed = set(checkpoint.completed_indices)
    undone = []
    descriptor = os.open(paths[3], os.O_RDWR | getattr(os, "O_NOFOLLOW", 0))
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for item in reversed(plan.items):
            if item.index not in completed:
                continue
            source = project.root / item.source_relative_path
            target = project.root / item.target_relative_path
            if source.exists() or source.is_symlink() or _location(project, item) != "target":
                raise _fail(f"Rückgängig-Konflikt: {item.source_relative_path}")
            os.replace(target, source)
            if _location(project, item) != "source":
                raise _fail(f"Rückgängig-Nachprüfung fehlgeschlagen: {item.source_relative_path}")
            undone.append(item.index)
            _write_checkpoint(paths[2], plan, OperationCheckpoint("running", tuple(sorted(completed)), tuple(sorted(undone)), checkpoint.created_directories, "Rückgängig läuft."))
            if progress:
                progress(len(undone), len(completed), item.source_relative_path)
        for relative in sorted(checkpoint.created_directories, key=lambda value: len(Path(value).parts), reverse=True):
            try:
                (project.root / relative).rmdir()
            except OSError:
                pass
        checkpoint = OperationCheckpoint("undone", tuple(sorted(completed)), tuple(sorted(undone)), checkpoint.created_directories, "Alle bestätigten Schritte rückgängig gemacht.")
        _write_checkpoint(paths[2], plan, checkpoint)
    finally:
        os.close(descriptor)
    reports = write_operation_report(project.root, operation_id)
    return OperationResult(plan.operation_id, plan.operation, "undone", 0, len(plan.items), bool(undone), *reports, checkpoint.message)


def operation_snapshot(project_root: Path, operation_id: str):
    _, plan, checkpoint = _load(validate_project_root(project_root).root, operation_id)
    return plan, checkpoint


def _report_paths(root: Path, stem: str):
    directory = root / CONTROL / REPORTS
    _private_dir(root / CONTROL)
    _private_dir(directory)
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", stem)
    return directory / f"{safe}.json", directory / f"{safe}.md"


def write_analysis_report(snapshot: InventorySnapshot, duplicates: DuplicateResult | None = None):
    json_path, markdown_path = _report_paths(snapshot.project.root, f"analysis-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}")
    payload = {"schemaVersion": SCHEMA, "type": "analysis", "project": ".", "createdUtc": _utc(), "files": len(snapshot.files), "directories": len(snapshot.directories), "entries": [{"path": entry.relative_path, "type": entry.entry_type, "size": entry.size, "category": entry.category, "flags": list(entry.flags)} for entry in snapshot.entries]}
    if duplicates:
        payload["duplicates"] = [{"sha256": group.sha256, "size": group.size, "paths": list(group.relative_paths)} for group in duplicates.groups]
    _json(json_path, payload)
    _atomic(markdown_path, (f"# Projektanalyse\n\nDateien: {len(snapshot.files)}\nOrdner: {len(snapshot.directories)}\nDuplikatgruppen: {len(duplicates.groups) if duplicates else 0}\n").encode())
    return json_path, markdown_path


def write_operation_report(project_root: Path, operation_id: str):
    _, plan, checkpoint = _load(validate_project_root(project_root).root, operation_id)
    json_path, markdown_path = _report_paths(project_root, f"operation-{operation_id}")
    payload = {"schemaVersion": SCHEMA, "type": "operation", "operationId": operation_id, "operation": plan.operation, "state": checkpoint.state, "planHash": plan.plan_hash, "completed": list(checkpoint.completed_indices), "undone": list(checkpoint.undone_indices), "items": [item.as_dict() for item in plan.items]}
    _json(json_path, payload)
    lines = [f"# Operation {operation_id}", "", f"Zustand: {checkpoint.state}", "", "| Vorher | Nachher |", "|---|---|"] + [f"| `{item.source_relative_path}` | `{item.target_relative_path}` |" for item in plan.items]
    _atomic(markdown_path, ("\n".join(lines) + "\n").encode())
    return json_path, markdown_path


def format_project_safety(project):
    return f"PROJEKTPRÜFUNG GRÜN\nProjekt: {project.root}\nFreier Speicher: {project.free_bytes} Bytes\nSymlinks: blockiert\nÜberschreiben: verboten"


def format_inventory_summary(snapshot):
    return f"DATEIBESTAND ANALYSIERT\nDateien: {len(snapshot.files)}\nOrdner: {len(snapshot.directories)}\nSymlinks ausgeschlossen: {snapshot.symlink_count}\nDateigröße gesamt: {snapshot.total_file_bytes} Bytes\nLesefehler: {len(snapshot.errors)}"


def format_duplicate_summary(result):
    return f"DUPLIKATSUCHE ABGESCHLOSSEN\nGehashte Dateien: {result.hashed_files}\nDuplikatgruppen: {len(result.groups)}\nPotenziell freigebbar: {result.reclaimable_bytes} Bytes\nLöschung: keine"


def format_operation_preview(plan):
    return f"PRODUKTIVE VORSCHAU\nOperations-ID: {plan.operation_id}\nTyp: {plan.operation}\nDateien: {len(plan.items)}\nPlanhash: {plan.plan_hash}\nÜberschreiben: NEIN\nAusführung erst nach Bestätigung"
