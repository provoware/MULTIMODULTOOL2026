"""Rein lesende Diagnosezentrale für das lokale XDG-Ereignisjournal."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import stat
from typing import Iterable, Mapping

MAX_DIAGNOSTIC_BYTES = 2 * 1024 * 1024
MAX_DIAGNOSTIC_RECORDS = 500
_ALLOWED_SEVERITIES = frozenset({"all", "info", "warning", "error", "critical"})
_REQUIRED_FIELDS = (
    "timestamp_utc",
    "diagnostic_id",
    "category",
    "severity",
    "cause",
    "consequence",
    "data_state",
    "solution",
    "next_step",
)


@dataclass(frozen=True)
class DiagnosticEntry:
    timestamp_utc: str
    diagnostic_id: str
    category: str
    severity: str
    cause: str
    consequence: str
    data_state: str
    solution: str
    next_step: str
    technical_detail: str = ""

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> "DiagnosticEntry":
        missing = [name for name in _REQUIRED_FIELDS if not str(value.get(name, "")).strip()]
        if missing:
            raise ValueError("Diagnoseeintrag enthält leere Pflichtfelder: " + ", ".join(missing))
        severity = str(value["severity"]).strip().lower()
        if severity not in _ALLOWED_SEVERITIES - {"all"}:
            raise ValueError("Diagnoseeintrag besitzt einen unbekannten Schweregrad.")
        return cls(
            timestamp_utc=str(value["timestamp_utc"]).strip(),
            diagnostic_id=str(value["diagnostic_id"]).strip(),
            category=str(value["category"]).strip(),
            severity=severity,
            cause=str(value["cause"]).strip(),
            consequence=str(value["consequence"]).strip(),
            data_state=str(value["data_state"]).strip(),
            solution=str(value["solution"]).strip(),
            next_step=str(value["next_step"]).strip(),
            technical_detail=str(value.get("technical_detail", "")).strip(),
        )

    def user_report(self) -> str:
        return "\n".join(
            (
                f"Zeit: {self.timestamp_utc}",
                f"Schweregrad: {self.severity.upper()}",
                f"Kategorie: {self.category}",
                f"Ursache: {self.cause}",
                f"Folge: {self.consequence}",
                f"Datenstand: {self.data_state}",
                f"Lösung: {self.solution}",
                f"Diagnosekennung: {self.diagnostic_id}",
                f"Sicherer nächster Schritt: {self.next_step}",
            )
        )


@dataclass(frozen=True)
class DiagnosticSnapshot:
    entries: tuple[DiagnosticEntry, ...]
    warnings: tuple[str, ...] = ()
    truncated: bool = False


def _validate_read_target(path: Path, *, uid: int | None = None) -> os.stat_result | None:
    current_uid = os.getuid() if uid is None else uid
    if path.is_symlink():
        raise ValueError("Ereignisjournal darf kein Symlink sein.")
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError("Ereignisjournal ist keine reguläre Datei.")
    if metadata.st_uid != current_uid:
        raise ValueError("Ereignisjournal gehört nicht dem aktuellen Linux-Nutzer.")
    if metadata.st_nlink != 1:
        raise ValueError("Ereignisjournal besitzt zusätzliche Hardlinks.")
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise ValueError("Ereignisjournal ist zu offen; erforderlich ist 0600.")
    return metadata


def read_diagnostics(
    journal_path: Path,
    *,
    maximum_bytes: int = MAX_DIAGNOSTIC_BYTES,
    maximum_records: int = MAX_DIAGNOSTIC_RECORDS,
    uid: int | None = None,
) -> DiagnosticSnapshot:
    """Journal sicher und ausschließlich lesend einlesen."""

    limit_bytes = max(1024, min(maximum_bytes, 16 * 1024 * 1024))
    limit_records = max(1, min(maximum_records, 5000))
    metadata = _validate_read_target(journal_path, uid=uid)
    if metadata is None:
        return DiagnosticSnapshot(())

    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(journal_path, flags)
    try:
        checked = os.fstat(descriptor)
        if not stat.S_ISREG(checked.st_mode) or checked.st_nlink != 1:
            raise ValueError("Ereignisjournal wurde während der Prüfung ausgetauscht.")
        truncated = checked.st_size > limit_bytes
        if truncated:
            os.lseek(descriptor, max(0, checked.st_size - limit_bytes), os.SEEK_SET)
        raw = bytearray()
        while len(raw) < limit_bytes:
            block = os.read(descriptor, min(65536, limit_bytes - len(raw)))
            if not block:
                break
            raw.extend(block)
    finally:
        os.close(descriptor)

    text = bytes(raw).decode("utf-8", errors="replace")
    lines = text.splitlines()
    if truncated and lines:
        lines = lines[1:]
    warnings: list[str] = []
    entries: list[DiagnosticEntry] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError("kein JSON-Objekt")
            entries.append(DiagnosticEntry.from_mapping(value))
        except (json.JSONDecodeError, ValueError) as exc:
            warnings.append(f"Ein lokaler Journaleintrag wurde übersprungen: {exc}")
        if len(entries) > limit_records:
            entries = entries[-limit_records:]
            truncated = True
    return DiagnosticSnapshot(tuple(entries), tuple(warnings), truncated)


def filter_diagnostics(
    entries: Iterable[DiagnosticEntry],
    *,
    severity: str = "all",
    diagnostic_query: str = "",
) -> tuple[DiagnosticEntry, ...]:
    normalized_severity = severity.strip().lower() or "all"
    if normalized_severity not in _ALLOWED_SEVERITIES:
        raise ValueError("Unbekannter Diagnose-Schweregrad.")
    query = diagnostic_query.strip().upper()
    return tuple(
        entry
        for entry in entries
        if (normalized_severity == "all" or entry.severity == normalized_severity)
        and (not query or query in entry.diagnostic_id.upper())
    )


class DiagnosticsController:
    """Kleine UI-Steuerung ohne Lösch-, Upload- oder Exportfunktion."""

    def __init__(self, QtWidgets, entries: Iterable[DiagnosticEntry]) -> None:
        self.QtWidgets = QtWidgets
        self.entries = tuple(entries)
        self.widget = QtWidgets.QFrame()
        self.widget.setObjectName("diagnosticsCenter")
        layout = QtWidgets.QVBoxLayout(self.widget)

        title = QtWidgets.QLabel("Diagnosezentrale · ausschließlich lesend")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        help_text = QtWidgets.QLabel(
            "Lokale, bereits bereinigte Ereignisse filtern und einzelne Berichte kopieren. "
            "Kein Löschen, Upload oder automatischer Export."
        )
        help_text.setObjectName("smallMuted")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

        filters = QtWidgets.QHBoxLayout()
        self.severity = QtWidgets.QComboBox()
        self.severity.setObjectName("diagnosticsSeverityFilter")
        self.severity.addItem("Alle Schweregrade", "all")
        self.severity.addItem("Information", "info")
        self.severity.addItem("Warnung", "warning")
        self.severity.addItem("Fehler", "error")
        self.severity.addItem("Kritisch", "critical")
        filters.addWidget(self.severity)

        self.query = QtWidgets.QLineEdit()
        self.query.setObjectName("diagnosticsIdFilter")
        self.query.setPlaceholderText("Diagnosekennung filtern, z. B. MMT-XDG")
        self.query.setClearButtonEnabled(True)
        filters.addWidget(self.query, 1)
        layout.addLayout(filters)

        split = QtWidgets.QSplitter()
        split.setObjectName("diagnosticsSplitter")
        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.setObjectName("diagnosticsList")
        self.detail = QtWidgets.QPlainTextEdit()
        self.detail.setObjectName("diagnosticsDetail")
        self.detail.setReadOnly(True)
        split.addWidget(self.list_widget)
        split.addWidget(self.detail)
        split.setStretchFactor(1, 2)
        layout.addWidget(split, 1)

        actions = QtWidgets.QHBoxLayout()
        self.status = QtWidgets.QLabel()
        self.status.setObjectName("diagnosticsStatus")
        actions.addWidget(self.status, 1)
        self.copy_button = QtWidgets.QPushButton("Bereinigten Bericht kopieren")
        self.copy_button.setObjectName("diagnosticsCopyButton")
        self.copy_button.setEnabled(False)
        actions.addWidget(self.copy_button)
        layout.addLayout(actions)

        self.severity.currentIndexChanged.connect(self.refresh)
        self.query.textChanged.connect(self.refresh)
        self.list_widget.currentRowChanged.connect(self._show_current)
        self.copy_button.clicked.connect(self._copy_current)
        self.refresh()

    def refresh(self) -> None:
        selected_id = ""
        current = self.current_entry()
        if current is not None:
            selected_id = current.diagnostic_id
        filtered = filter_diagnostics(
            self.entries,
            severity=str(self.severity.currentData()),
            diagnostic_query=self.query.text(),
        )
        self._filtered = filtered
        self.list_widget.clear()
        for entry in reversed(filtered):
            item = self.QtWidgets.QListWidgetItem(
                f"{entry.severity.upper()} · {entry.diagnostic_id}\n{entry.cause}"
            )
            item.setData(256, entry.diagnostic_id)
            self.list_widget.addItem(item)
        self.status.setText(f"{len(filtered)} von {len(self.entries)} Ereignissen sichtbar")
        if self.list_widget.count():
            row = 0
            for index in range(self.list_widget.count()):
                if self.list_widget.item(index).data(256) == selected_id:
                    row = index
                    break
            self.list_widget.setCurrentRow(row)
        else:
            self.detail.setPlainText("Keine passenden lokalen Ereignisse.")
            self.copy_button.setEnabled(False)

    def _entry_for_row(self, row: int) -> DiagnosticEntry | None:
        if row < 0 or row >= len(self._filtered):
            return None
        return tuple(reversed(self._filtered))[row]

    def current_entry(self) -> DiagnosticEntry | None:
        return self._entry_for_row(self.list_widget.currentRow())

    def _show_current(self, row: int) -> None:
        entry = self._entry_for_row(row)
        self.detail.setPlainText(entry.user_report() if entry else "Keine Diagnose ausgewählt.")
        self.copy_button.setEnabled(entry is not None)

    def _copy_current(self) -> None:
        entry = self.current_entry()
        if entry is None:
            return
        self.QtWidgets.QApplication.clipboard().setText(entry.user_report())
        self.status.setText("Bereinigter Bericht wurde in die Zwischenablage kopiert.")

    def focus_diagnostic(self, diagnostic_id: str = "") -> None:
        self.query.setText(diagnostic_id)
        self.query.setFocus()
        if self.list_widget.count():
            self.list_widget.setCurrentRow(0)
