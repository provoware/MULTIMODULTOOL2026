"""Read-only project trash transaction overview.

The reader never creates, repairs, restores or deletes project data. It reports
valid states and marks malformed or damaged transaction directories visibly.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import os
import re
import stat

from .error_events import SafeOperationError
from .project_trash import inspect_transaction, trash_paths

MAXIMUM_OVERVIEW_RECORDS = 1000
_TRANSACTION_ID_PATTERN = re.compile(r"^MMTTRASH-[0-9]{8}T[0-9]{6}-[A-F0-9]{12}$")
_VISIBLE_STATES = {"prepared", "trashed", "restored", "damaged"}


@dataclass(frozen=True)
class TransactionEntry:
    transaction_id: str
    state: str
    created_utc: str
    original_relative_path: str
    detail: str = ""


@dataclass(frozen=True)
class TransactionSnapshot:
    entries: tuple[TransactionEntry, ...]
    warnings: tuple[str, ...] = ()
    truncated: bool = False

    def filtered(self, state: str = "all") -> tuple[TransactionEntry, ...]:
        selected = state.strip().lower()
        if selected in {"", "all"}:
            return self.entries
        if selected not in _VISIBLE_STATES:
            return ()
        return tuple(item for item in self.entries if item.state == selected)


def _absolute_project(path: Path) -> Path:
    expanded = path.expanduser()
    if not expanded.is_absolute():
        raise ValueError("Projektpfad ist nicht absolut.")
    root = Path(os.path.abspath(os.fspath(expanded)))
    if root.is_symlink():
        raise ValueError("Projektstamm darf kein Symlink sein.")
    metadata = root.lstat()
    if not stat.S_ISDIR(metadata.st_mode):
        raise ValueError("Projektstamm ist kein Verzeichnis.")
    if hasattr(os, "getuid") and metadata.st_uid != os.getuid():
        raise ValueError("Projektstamm gehört nicht dem aktuellen Linux-Nutzer.")
    return root


def _safe_directory(path: Path, label: str) -> None:
    if path.is_symlink():
        raise ValueError(f"{label} darf kein Symlink sein.")
    metadata = path.lstat()
    if not stat.S_ISDIR(metadata.st_mode):
        raise ValueError(f"{label} ist kein Verzeichnis.")
    if hasattr(os, "getuid") and metadata.st_uid != os.getuid():
        raise ValueError(f"{label} gehört nicht dem aktuellen Linux-Nutzer.")
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise ValueError(f"{label} ist zu offen; erforderlich ist 0700.")


def read_transaction_overview(
    project_root: Path,
    *,
    maximum_records: int = MAXIMUM_OVERVIEW_RECORDS,
) -> TransactionSnapshot:
    """Read transaction manifests without changing a single project byte."""

    root = _absolute_project(project_root)
    transactions = trash_paths(root).transactions_root
    if not transactions.exists():
        return TransactionSnapshot(())
    _safe_directory(transactions, "Transaktionsverzeichnis")
    limit = max(1, min(int(maximum_records), MAXIMUM_OVERVIEW_RECORDS))
    entries: list[TransactionEntry] = []
    warnings: list[str] = []
    try:
        children = sorted(
            transactions.iterdir(),
            key=lambda item: item.name,
            reverse=True,
        )
    except OSError as exc:
        raise ValueError(f"Transaktionsverzeichnis konnte nicht gelesen werden: {exc}") from exc

    truncated = len(children) > limit
    for child in children[:limit]:
        transaction_id = child.name
        if child.is_symlink():
            entries.append(
                TransactionEntry(transaction_id, "damaged", "", "", "Symlink blockiert")
            )
            continue
        try:
            metadata = child.lstat()
        except OSError as exc:
            entries.append(
                TransactionEntry(transaction_id, "damaged", "", "", f"Prüfung fehlgeschlagen: {exc}")
            )
            continue
        if not stat.S_ISDIR(metadata.st_mode):
            entries.append(
                TransactionEntry(transaction_id, "damaged", "", "", "Kein Transaktionsverzeichnis")
            )
            continue
        if (
            not _TRANSACTION_ID_PATTERN.fullmatch(transaction_id)
            or (hasattr(os, "getuid") and metadata.st_uid != os.getuid())
            or stat.S_IMODE(metadata.st_mode) & 0o077
        ):
            entries.append(
                TransactionEntry(
                    transaction_id,
                    "damaged",
                    "",
                    "",
                    "ID, Eigentümer oder Rechte sind ungültig",
                )
            )
            continue
        try:
            manifest = inspect_transaction(root, transaction_id)
        except (SafeOperationError, OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            entries.append(
                TransactionEntry(
                    transaction_id,
                    "damaged",
                    "",
                    "",
                    str(exc),
                )
            )
            continue
        entries.append(
            TransactionEntry(
                transaction_id=manifest.transaction_id,
                state=manifest.state,
                created_utc=manifest.created_utc,
                original_relative_path=manifest.original_relative_path,
            )
        )
    if truncated:
        warnings.append(
            f"Ansicht wurde auf die neuesten {limit} Transaktionen begrenzt."
        )
    damaged_count = sum(item.state == "damaged" for item in entries)
    if damaged_count:
        warnings.append(
            f"{damaged_count} beschädigte oder unsichere Transaktion(en) wurden nur markiert."
        )
    return TransactionSnapshot(tuple(entries), tuple(warnings), truncated)
