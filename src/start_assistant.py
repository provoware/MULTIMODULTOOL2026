"""P1-001 guided start selection with read-only prevalidation."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import stat
from typing import Mapping

from .error_events import SafeOperationError
from .productive_workflow import CONTROL, ProjectSafety, validate_project_root

MINIMUM_FREE_BYTES = 16 * 1024**2
MODE_READ_ONLY = "read-only"
MODE_PREVIEW_REPORT = "preview-report"
MODE_PRODUCTIVE = "productive"


@dataclass(frozen=True)
class SafetyMode:
    key: str
    label: str
    description: str
    allows_report: bool
    allows_write: bool


SAFETY_MODES: tuple[SafetyMode, ...] = (
    SafetyMode(
        MODE_READ_ONLY,
        "Nur prüfen",
        "Analyse, Duplikatsuche und Vorschauen; keine Berichte und keine Dateiänderung.",
        False,
        False,
    ),
    SafetyMode(
        MODE_PREVIEW_REPORT,
        "Vorschau und Bericht",
        "Analyse, Vorschauen und private JSON-/Markdown-Berichte; keine Dateiänderung.",
        True,
        False,
    ),
    SafetyMode(
        MODE_PRODUCTIVE,
        "Produktiv mit Bestätigung",
        "Dateiänderungen erst nach Startfreigabe, vollständiger Vorschau und zweiter Bestätigung.",
        True,
        True,
    ),
)
SAFETY_MODE_BY_KEY: Mapping[str, SafetyMode] = {mode.key: mode for mode in SAFETY_MODES}


def _fail(cause: str) -> SafeOperationError:
    return SafeOperationError(
        category="start-assistant",
        cause=cause,
        consequence="Der Startassistent hat die Freigabe kontrolliert blockiert.",
        data_state="Projekt-, Ziel- und Steuerdaten blieben unverändert.",
        solution="Projektordner, Zielordner, Eigentümer, Rechte, Mountgrenze und Sicherheitsmodus prüfen.",
        next_step="Auswahl korrigieren und die vollständige Vorvalidierung erneut ausführen.",
    )


def _absolute(path: Path, label: str) -> Path:
    value = path.expanduser()
    if not value.is_absolute():
        raise _fail(f"{label} muss als absoluter Linux-Pfad gewählt werden.")
    return Path(os.path.abspath(os.fspath(value)))


def _no_symlink_components(path: Path, root: Path) -> None:
    current = root
    if root.is_symlink():
        raise _fail("Der Projektordner darf kein Symlink sein.")
    for part in path.relative_to(root).parts:
        current /= part
        try:
            metadata = current.lstat()
        except OSError as exc:
            raise _fail(f"Zielpfad ist nicht vollständig lesbar: {current.name}: {exc}") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise _fail(f"Symbolische Zielpfadkomponente ist gesperrt: {current.name}")


def _format_bytes(value: int) -> str:
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    size = float(max(value, 0))
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{value} B"


@dataclass(frozen=True)
class StartSelection:
    project: ProjectSafety
    target_root: Path
    target_relative: str
    safety_mode: SafetyMode
    target_device: int
    target_inode: int
    target_owner_uid: int
    target_mode: int
    target_free_bytes: int
    target_is_empty: bool
    summary: str

    @property
    def allows_report(self) -> bool:
        return self.safety_mode.allows_report

    @property
    def allows_write(self) -> bool:
        return self.safety_mode.allows_write


def _summary(
    project: ProjectSafety,
    target_root: Path,
    target_relative: str,
    mode: SafetyMode,
    *,
    target_device: int,
    target_owner_uid: int,
    target_mode: int,
    target_free_bytes: int,
    target_is_empty: bool,
) -> str:
    write_gate = (
        "Dateiänderungen freigegeben – weiterhin nur nach vollständiger Vorschau "
        "und einer zweiten ausdrücklichen Bestätigung."
        if mode.allows_write
        else "Dateiänderungen gesperrt."
    )
    report_gate = (
        "Private JSON-/Markdown-Berichte erlaubt."
        if mode.allows_report
        else "Auch Berichtsschreibzugriffe gesperrt."
    )
    return "\n".join(
        (
            "GRÜN: Startauswahl vollständig vorvalidiert",
            f"Projektordner: {project.root}",
            f"Zielordner: {target_root}",
            f"Projekt-relatives Ziel: {target_relative}",
            f"Sicherheitsmodus: {mode.label}",
            f"Moduswirkung: {mode.description}",
            f"Eigentümer: Projekt UID {project.owner_uid} · Ziel UID {target_owner_uid}",
            f"Dateisystem: Projektgerät {project.device} · Zielgerät {target_device} · identisch",
            f"Zielrechte: {target_mode:04o}",
            f"Freier Speicher: {_format_bytes(target_free_bytes)}",
            f"Zielinhalt: {'leer' if target_is_empty else 'vorhanden; Konflikte werden später vollständig blockiert'}",
            "Symlinkprüfung: keine symbolische Komponente",
            "Mountprüfung: keine getrennte Mountgrenze",
            report_gate,
            write_gate,
            "Übernahme erfolgt erst nach Bestätigung dieser Zusammenfassung.",
        )
    )


def validate_start_selection(
    project_root: Path,
    target_root: Path,
    safety_mode: str,
    *,
    minimum_free_bytes: int = MINIMUM_FREE_BYTES,
) -> StartSelection:
    mode = SAFETY_MODE_BY_KEY.get(str(safety_mode))
    if mode is None:
        raise _fail("Unbekannter Sicherheitsmodus.")

    project = validate_project_root(
        project_root,
        require_writable=mode.allows_report or mode.allows_write,
        minimum_free_bytes=minimum_free_bytes,
    )
    target = _absolute(target_root, "Zielordner")
    if target == project.root:
        raise _fail("Projekt- und Zielordner müssen getrennt gewählt werden.")
    if not target.is_relative_to(project.root):
        raise _fail(
            "Der Zielordner muss innerhalb des geprüften Projektordners liegen. "
            "Produktive Operationen dürfen die Projekt- und Dateisystemgrenze nicht verlassen."
        )
    relative = target.relative_to(project.root)
    if relative == Path(".") or CONTROL in relative.parts:
        raise _fail("Der interne Steuerordner darf nicht als Ziel verwendet werden.")

    _no_symlink_components(target, project.root)
    try:
        metadata = target.lstat()
    except OSError as exc:
        raise _fail(f"Zielordner ist nicht lesbar: {exc}") from exc
    if not stat.S_ISDIR(metadata.st_mode):
        raise _fail("Ziel muss ein regulärer Linux-Ordner sein.")
    if hasattr(os, "getuid") and metadata.st_uid != os.getuid():
        raise _fail("Zielordner muss dem aktuellen Linux-Nutzer gehören.")
    if metadata.st_dev != project.device:
        raise _fail("Projekt- und Zielordner liegen auf unterschiedlichen Dateisystemen.")
    if os.path.ismount(target):
        raise _fail("Ein zusätzlicher Mountpunkt innerhalb des Projekts ist als Ziel gesperrt.")

    readable = os.access(target, os.R_OK | os.X_OK)
    writable = os.access(target, os.W_OK | os.X_OK)
    if not readable:
        raise _fail("Zielordner ist nicht vollständig les- und betretbar.")
    if (mode.allows_report or mode.allows_write) and not writable:
        raise _fail("Der gewählte Sicherheitsmodus benötigt einen schreibbaren Zielordner.")

    usage = shutil.disk_usage(target)
    if (mode.allows_report or mode.allows_write) and usage.free < minimum_free_bytes:
        raise _fail("Freier Speicher im Zielordner reicht für den gewählten Modus nicht aus.")

    try:
        target_is_empty = next(os.scandir(target), None) is None
    except OSError as exc:
        raise _fail(f"Zielinhalt konnte nicht sicher geprüft werden: {exc}") from exc

    target_mode = stat.S_IMODE(metadata.st_mode)
    target_relative = relative.as_posix()
    return StartSelection(
        project=project,
        target_root=target,
        target_relative=target_relative,
        safety_mode=mode,
        target_device=metadata.st_dev,
        target_inode=metadata.st_ino,
        target_owner_uid=getattr(metadata, "st_uid", -1),
        target_mode=target_mode,
        target_free_bytes=usage.free,
        target_is_empty=target_is_empty,
        summary=_summary(
            project,
            target,
            target_relative,
            mode,
            target_device=metadata.st_dev,
            target_owner_uid=getattr(metadata, "st_uid", -1),
            target_mode=target_mode,
            target_free_bytes=usage.free,
            target_is_empty=target_is_empty,
        ),
    )


def revalidate_start_selection(
    selection: StartSelection,
    *,
    minimum_free_bytes: int = MINIMUM_FREE_BYTES,
) -> StartSelection:
    current = validate_start_selection(
        selection.project.root,
        selection.target_root,
        selection.safety_mode.key,
        minimum_free_bytes=minimum_free_bytes,
    )
    if current.project.device != selection.project.device:
        raise _fail("Das Projektdateisystem hat sich seit der Startfreigabe geändert.")
    if current.target_device != selection.target_device or current.target_inode != selection.target_inode:
        raise _fail("Der Zielordner wurde seit der Startfreigabe ersetzt oder neu eingebunden.")
    if current.target_owner_uid != selection.target_owner_uid:
        raise _fail("Der Eigentümer des Zielordners hat sich seit der Startfreigabe geändert.")
    return current


def create_start_assistant_dialog(
    QtWidgets,
    parent=None,
    *,
    initial_project: Path | None = None,
    initial_target: Path | None = None,
    initial_mode: str = MODE_PRODUCTIVE,
):
    """Create the modal assistant. Construction and validation perform no writes."""

    dialog = QtWidgets.QDialog(parent)
    dialog.setObjectName("startAssistantDialog")
    dialog.setWindowTitle("P1-001 – Geführter sicherer Start")
    dialog.resize(820, 650)
    dialog.setMinimumSize(680, 520)
    dialog.setModal(True)
    dialog.selection = None

    outer = QtWidgets.QVBoxLayout(dialog)
    title = QtWidgets.QLabel("Projekt, getrenntes Ziel und Sicherheitsmodus")
    title.setObjectName("startAssistantTitle")
    title.setWordWrap(True)
    outer.addWidget(title)

    intro = QtWidgets.QLabel(
        "Der Assistent prüft die gesamte Auswahl rein lesend. "
        "Eine Dateiaktion wird hier weder vorbereitet noch ausgeführt."
    )
    intro.setObjectName("startAssistantIntro")
    intro.setWordWrap(True)
    intro.setProperty("safetyStatus", True)
    outer.addWidget(intro)

    def selection_row(number: str, label_text: str, field_name: str, button_name: str):
        group = QtWidgets.QGroupBox(f"{number}. {label_text}")
        layout = QtWidgets.QHBoxLayout(group)
        field = QtWidgets.QLineEdit()
        field.setObjectName(field_name)
        field.setReadOnly(True)
        button = QtWidgets.QPushButton("Ordner auswählen …")
        button.setObjectName(button_name)
        button.setMinimumHeight(42)
        layout.addWidget(field, 1)
        layout.addWidget(button)
        outer.addWidget(group)
        return field, button

    project_field, project_button = selection_row(
        "1", "Projektordner", "assistantProjectField", "assistantChooseProjectButton"
    )
    target_field, target_button = selection_row(
        "2", "Getrennter Zielordner", "assistantTargetField", "assistantChooseTargetButton"
    )
    project_field.setText(str(initial_project or ""))
    target_field.setText(str(initial_target or ""))

    mode_group = QtWidgets.QGroupBox("3. Sicherheitsmodus")
    mode_layout = QtWidgets.QVBoxLayout(mode_group)
    mode_combo = QtWidgets.QComboBox()
    mode_combo.setObjectName("assistantSafetyModeCombo")
    for mode in SAFETY_MODES:
        mode_combo.addItem(mode.label, mode.key)
        mode_combo.setItemData(mode_combo.count() - 1, mode.description, 3)
    mode_index = max(mode_combo.findData(initial_mode), 0)
    mode_combo.setCurrentIndex(mode_index)
    mode_description = QtWidgets.QLabel()
    mode_description.setObjectName("assistantModeDescription")
    mode_description.setWordWrap(True)
    mode_layout.addWidget(mode_combo)
    mode_layout.addWidget(mode_description)
    outer.addWidget(mode_group)

    validate_button = QtWidgets.QPushButton("4. Auswahl vollständig prüfen")
    validate_button.setObjectName("assistantValidateButton")
    validate_button.setMinimumHeight(44)
    outer.addWidget(validate_button)

    status = QtWidgets.QLabel("Noch nicht geprüft.")
    status.setObjectName("assistantValidationStatus")
    status.setWordWrap(True)
    status.setProperty("safetyStatus", True)
    outer.addWidget(status)

    summary = QtWidgets.QPlainTextEdit()
    summary.setObjectName("assistantSummary")
    summary.setReadOnly(True)
    summary.setPlaceholderText("Nach erfolgreicher Prüfung erscheint hier die vollständige Freigabezusammenfassung.")
    outer.addWidget(summary, 1)

    confirmation = QtWidgets.QCheckBox(
        "Ich habe Projektordner, Zielordner, Sicherheitsmodus und Schreibgrenzen geprüft."
    )
    confirmation.setObjectName("assistantConfirmationCheck")
    confirmation.setEnabled(False)
    outer.addWidget(confirmation)

    actions = QtWidgets.QHBoxLayout()
    cancel_button = QtWidgets.QPushButton("Abbrechen")
    cancel_button.setObjectName("assistantCancelButton")
    accept_button = QtWidgets.QPushButton("Geprüfte Auswahl übernehmen")
    accept_button.setObjectName("assistantAcceptButton")
    accept_button.setEnabled(False)
    cancel_button.setMinimumHeight(44)
    accept_button.setMinimumHeight(44)
    actions.addWidget(cancel_button)
    actions.addStretch(1)
    actions.addWidget(accept_button)
    outer.addLayout(actions)

    def current_mode() -> SafetyMode:
        return SAFETY_MODE_BY_KEY[str(mode_combo.currentData())]

    def invalidate() -> None:
        dialog.selection = None
        confirmation.setChecked(False)
        confirmation.setEnabled(False)
        accept_button.setEnabled(False)
        summary.clear()
        status.setText("Auswahl geändert – vollständige Prüfung erforderlich.")

    def refresh_mode() -> None:
        mode_description.setText(current_mode().description)
        invalidate()

    def choose_project() -> None:
        start = project_field.text().strip() or str(Path.home())
        chosen = QtWidgets.QFileDialog.getExistingDirectory(
            dialog,
            "Projektordner wählen",
            start,
            QtWidgets.QFileDialog.Option.ShowDirsOnly,
        )
        if chosen:
            project_field.setText(chosen)
            target_field.clear()
            invalidate()

    def choose_target() -> None:
        start = target_field.text().strip() or project_field.text().strip() or str(Path.home())
        chosen = QtWidgets.QFileDialog.getExistingDirectory(
            dialog,
            "Getrennten Zielordner innerhalb des Projekts wählen",
            start,
            QtWidgets.QFileDialog.Option.ShowDirsOnly,
        )
        if chosen:
            target_field.setText(chosen)
            invalidate()

    def validate() -> None:
        try:
            selection = validate_start_selection(
                Path(project_field.text().strip()),
                Path(target_field.text().strip()),
                str(mode_combo.currentData()),
            )
        except BaseException as exc:
            cause = getattr(exc, "cause", str(exc))
            dialog.selection = None
            confirmation.setChecked(False)
            confirmation.setEnabled(False)
            accept_button.setEnabled(False)
            summary.setPlainText(cause)
            status.setText(f"ROT: {cause}")
            return
        dialog.selection = selection
        summary.setPlainText(selection.summary)
        status.setText("GRÜN: Auswahl geprüft – Zusammenfassung bestätigen.")
        confirmation.setEnabled(True)
        accept_button.setEnabled(False)

    def update_accept() -> None:
        accept_button.setEnabled(dialog.selection is not None and confirmation.isChecked())

    project_button.clicked.connect(choose_project)
    target_button.clicked.connect(choose_target)
    mode_combo.currentIndexChanged.connect(refresh_mode)
    validate_button.clicked.connect(validate)
    confirmation.toggled.connect(lambda _checked: update_accept())
    cancel_button.clicked.connect(dialog.reject)
    accept_button.clicked.connect(dialog.accept)
    mode_description.setText(current_mode().description)
    return dialog


def run_start_assistant(
    QtWidgets,
    parent=None,
    *,
    initial_project: Path | None = None,
    initial_target: Path | None = None,
    initial_mode: str = MODE_PRODUCTIVE,
) -> StartSelection | None:
    dialog = create_start_assistant_dialog(
        QtWidgets,
        parent,
        initial_project=initial_project,
        initial_target=initial_target,
        initial_mode=initial_mode,
    )
    if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
        return dialog.selection
    return None
