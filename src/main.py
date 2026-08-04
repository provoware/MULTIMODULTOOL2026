"""Linux-Desktop-App mit XDG-, Fehler-, Instanz- und Papierkorbschutz."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .diagnostics_center import DiagnosticsController, DiagnosticSnapshot, read_diagnostics
from .error_dialog import show_error_dialog
from .error_events import (
    ErrorEvent,
    ErrorEventCenter,
    EventJournal,
    create_event,
    event_from_exception,
    event_from_messages,
    event_from_settings_result,
    format_event_for_user,
    install_exception_hooks,
)
from .manifest_validator import format_validation_result, validate_manifest
from .settings_manager import (
    SettingsLoadResult,
    format_settings_report,
    inspect_settings,
    load_or_recover_settings,
)
from .single_instance import (
    InstanceResult,
    LaunchRequest,
    SingleInstanceCoordinator,
    resolve_runtime_root,
)
from .xdg_paths import (
    XDGPaths,
    ensure_xdg_paths,
    format_path_report,
    resolve_xdg_paths,
    validate_xdg_paths,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / "layout-manifest.json"
DEVELOPMENT_PROGRESS = 41
COMPLETED_POINTS = 27
OPEN_POINTS = 39
ZONE_OBJECT_NAMES = (
    "header",
    "navigation",
    "summaryCards",
    "primaryActionTiles",
    "workflowPanel",
    "workspaceScroll",
    "contextRail",
    "actionBar",
    "footer",
)


def is_supported_platform(platform_name: str | None = None) -> bool:
    return (platform_name or sys.platform).startswith("linux")


def platform_error_text() -> str:
    return (
        "MULTIMODULTOOL2026 wird ausschließlich für Linux-Desktop-Systeme gebaut. "
        "Unterstützt werden Kubuntu 22.04/24.04, KDE Plasma, X11 und Wayland."
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MULTIMODULTOOL2026 starten oder prüfen")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--paths-only", action="store_true")
    parser.add_argument("--settings-only", action="store_true")
    parser.add_argument(
        "--show-diagnostics",
        action="store_true",
        help="Bestehende Instanz aktivieren und die Diagnosezentrale fokussieren.",
    )
    parser.add_argument(
        "--diagnostic-id",
        default="",
        help="Erlaubte Diagnosekennung für den lokalen Diagnosefilter.",
    )
    return parser.parse_args(argv)


def _label(QtWidgets, text: str, name: str = "muted", *, safety: bool = False):
    item = QtWidgets.QLabel(text)
    item.setObjectName(name)
    item.setWordWrap(True)
    if safety:
        item.setProperty("safetyStatus", True)
    return item


def _button(
    QtWidgets,
    text: str,
    *,
    enabled: bool = True,
    name: str = "",
    tooltip: str = "",
):
    button = QtWidgets.QPushButton(text)
    button.setEnabled(enabled)
    button.setMinimumHeight(44)
    if name:
        button.setObjectName(name)
    if tooltip:
        button.setToolTip(tooltip)
    return button


def _panel(QtWidgets, title: str, body: str, name: str = "panel"):
    frame = QtWidgets.QFrame()
    frame.setObjectName(name)
    layout = QtWidgets.QVBoxLayout(frame)
    layout.setContentsMargins(12, 10, 12, 10)
    layout.addWidget(_label(QtWidgets, title, "sectionTitle"))
    layout.addWidget(_label(QtWidgets, body))
    return frame


def _zone(widget, name: str, number: int):
    widget.setObjectName(name)
    widget.setProperty("zoneId", f"Z{number:02d}")
    return widget


def _display_path(path: Path) -> str:
    try:
        return f"~/{path.relative_to(Path.home())}"
    except ValueError:
        return str(path)


def build_window(
    QtWidgets,
    QtCore,
    *,
    validation_text: str,
    path_text: str,
    settings_text: str,
    paths: XDGPaths,
    settings_result: SettingsLoadResult,
    diagnostics: DiagnosticSnapshot | None = None,
    event_center: ErrorEventCenter | None = None,
):
    """Neun sichtbare Layoutzonen ohne Dateioperation erzeugen."""

    snapshot = diagnostics or DiagnosticSnapshot(())
    latest = event_center.latest if event_center else None
    window = QtWidgets.QMainWindow()
    window.setObjectName("mainWindow")
    window.setWindowTitle("MULTIMODULTOOL2026 – Linux")
    window.resize(1500, 900)
    window.setMinimumSize(1024, 680)
    central = QtWidgets.QWidget()
    grid = QtWidgets.QGridLayout(central)
    grid.setContentsMargins(12, 12, 12, 12)
    grid.setSpacing(9)
    grid.setColumnStretch(1, 1)
    grid.setRowStretch(4, 1)
    window.setCentralWidget(central)

    header = _zone(QtWidgets.QFrame(), "header", 1)
    header_layout = QtWidgets.QHBoxLayout(header)
    identity = QtWidgets.QVBoxLayout()
    identity.addWidget(_label(QtWidgets, "◈  MULTIMODULTOOL2026", "appTitle"))
    identity.addWidget(
        _label(
            QtWidgets,
            "Eine Instanz · atomarer Projektpapierkorb · lokale Diagnose.",
            "smallMuted",
        )
    )
    header_layout.addLayout(identity)
    header_layout.addStretch(1)
    header_layout.addWidget(
        _label(
            QtWidgets,
            "● INSTANZ-, PAPIERKORB- UND FEHLERPRÜFUNG GRÜN",
            "statusOk",
            safety=True,
        )
    )
    grid.addWidget(header, 0, 0, 1, 3)

    navigation = _zone(QtWidgets.QFrame(), "navigation", 2)
    navigation.setFixedWidth(198)
    nav = QtWidgets.QVBoxLayout(navigation)
    nav.addWidget(_label(QtWidgets, "HAUPTBEREICHE", "navTitle"))
    nav.addWidget(_button(QtWidgets, "⌂  Start"))
    trash_button = _button(
        QtWidgets,
        "♲  Papierkorbvertrag",
        name="trashNavigation",
        tooltip="Atomaren, wiederherstellbaren Projektpapierkorb anzeigen.",
    )
    trash_button.setProperty("active", True)
    nav.addWidget(trash_button)
    diagnosis_button = _button(
        QtWidgets,
        "⚕  Diagnose",
        name="diagnosticsNavigation",
        tooltip="Lokale bereinigte Ereignisse ausschließlich lesend anzeigen.",
    )
    nav.addWidget(diagnosis_button)
    lock_tip = "Noch gesperrt, bis Undo und Wiederanlauf vollständig geprüft sind."
    for text in (
        "⌕  Analysieren",
        "▣  Duplikate",
        "↕  Organisieren",
        "✎  Umbenennen",
        "▤  Berichte",
    ):
        nav.addWidget(
            _button(
                QtWidgets,
                text,
                enabled=False,
                name="lockedNavigation",
                tooltip=lock_tip,
            )
        )
    nav.addStretch(1)
    nav.addWidget(
        _button(
            QtWidgets,
            "⚙  Einstellungen",
            enabled=False,
            tooltip="Datenformat aktiv; Bedienseite folgt.",
        )
    )
    nav.addWidget(_button(QtWidgets, "?  Hilfe"))
    grid.addWidget(navigation, 1, 0, 5, 1)

    summary = _zone(QtWidgets.QWidget(), "summaryCards", 3)
    cards = QtWidgets.QHBoxLayout(summary)
    settings_status = "WIEDERHERGESTELLT" if settings_result.recovered else "1 / 1 GRÜN"
    for title, value, detail in (
        ("Instanzschutz", "1 PRIMÄR", "Unix-Socket · Peer-UID"),
        ("Papierkorb", "ATOMAR", "Vorschau · Manifest · Restore"),
        ("Diagnose", str(len(snapshot.entries)), "lokal · lesend · gefiltert"),
        ("Entwicklung", "41 %", "27 erledigt · 39 offen"),
    ):
        cards.addWidget(_panel(QtWidgets, title, f"{value}\n{detail}", "card"))
    grid.addWidget(summary, 1, 1)

    actions = _zone(QtWidgets.QWidget(), "primaryActionTiles", 4)
    action_layout = QtWidgets.QHBoxLayout(actions)
    for text in (
        "1\nProjekt wählen",
        "2\nQuelle prüfen",
        "3\nVorschau",
        "4\nFreigabe",
        "5\nAtomar verschieben",
        "6\nBericht",
    ):
        action_layout.addWidget(
            _button(
                QtWidgets,
                text,
                enabled=False,
                name="lockedPrimaryAction",
                tooltip="Papierkorb-Kern aktiv; geführte Projektauswahl folgt mit P1-001/P1-003.",
            )
        )
    grid.addWidget(actions, 2, 1)

    workflow = _zone(QtWidgets.QFrame(), "workflowPanel", 5)
    flow = QtWidgets.QVBoxLayout(workflow)
    flow.addWidget(_label(QtWidgets, "GEFÜHRTER SICHERHEITS-WORKFLOW", "navTitle"))
    flow.addWidget(
        _label(
            QtWidgets,
            "1 Projekt  →  2 Pfadprüfung  →  3 Vorschau  →  4 Transaktion  →  5 Restore",
            "sectionTitle",
        )
    )
    progress = QtWidgets.QProgressBar()
    progress.setValue(DEVELOPMENT_PROGRESS)
    progress.setFormat("Entwicklungsstand: 41 %")
    flow.addWidget(progress)
    grid.addWidget(workflow, 3, 1)

    workspace = QtWidgets.QWidget()
    work = QtWidgets.QVBoxLayout(workspace)
    work.addWidget(
        _panel(
            QtWidgets,
            "P0-006 abgeschlossen",
            "Destruktive Dateiaktionen dürfen reguläre Dateien und Verzeichnisse nur "
            "innerhalb desselben Dateisystems atomar in einen projektbezogenen, "
            "wiederherstellbaren Papierkorb verschieben.",
            "hero",
        )
    )
    trash_contract = _panel(
        QtWidgets,
        "Papierkorb-Sicherheitsvertrag",
        "✓ unveränderliche Vorschau und Quellfingerabdruck\n"
        "✓ eindeutige Transaktions-ID und Manifest mit 0600\n"
        "✓ private Projektordner mit 0700\n"
        "✓ os.replace statt Kopieren-und-Löschen\n"
        "✓ Mountwechsel, Symlinks, Hardlinks und Konflikte blockiert\n"
        "✓ Wiederherstellung nur bei unverändertem Payload und freiem Originalpfad\n"
        "✗ keine dauerhafte Löschung",
        "trashContractPanel",
    )
    work.addWidget(trash_contract)
    work.addWidget(
        _panel(
            QtWidgets,
            "Aktuelle Bediengrenze",
            "Die Transaktions-API ist geprüft. Die grafische Datei- und Projektwahl bleibt "
            "gesperrt, bis P1-001 und P1-003 sichere Auswahldialoge bereitstellen.",
            "warningPanel",
        )
    )
    diagnostics_controller = DiagnosticsController(QtWidgets, snapshot.entries)
    work.addWidget(diagnostics_controller.widget, 1)
    if snapshot.warnings or snapshot.truncated:
        notes = list(snapshot.warnings)
        if snapshot.truncated:
            notes.append("Die Ansicht wurde auf die neuesten sicheren Einträge begrenzt.")
        work.addWidget(_panel(QtWidgets, "Diagnosehinweis", "\n".join(notes)))
    work.addStretch(1)
    workspace_scroll = _zone(QtWidgets.QScrollArea(), "workspaceScroll", 6)
    workspace_scroll.setWidgetResizable(True)
    workspace_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    workspace_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    workspace_scroll.setWidget(workspace)
    grid.addWidget(workspace_scroll, 4, 1)

    context_body = QtWidgets.QWidget()
    context_layout = QtWidgets.QVBoxLayout(context_body)
    context_layout.addWidget(
        _panel(
            QtWidgets,
            "Papierkorbstatus",
            "Projektlokal · gleiches Dateisystem · Manifest 0600 · Verzeichnisse 0700 · "
            "Namenskonflikte blockieren Restore.",
            "trashStatusPanel",
        )
    )
    context_layout.addWidget(
        _panel(
            QtWidgets,
            "Instanzstatus",
            "Primäre Instanz hält einen privaten Unix-Domain-Socket. "
            "Lokale Absender werden per Linux-Peer-UID geprüft.",
            "instanceStatusPanel",
        )
    )
    context_layout.addWidget(
        _panel(
            QtWidgets,
            "Sichere Speicherorte",
            "\n".join(f"✓ {name}: {_display_path(path)}" for name, path in paths.items()),
        )
    )
    context_layout.addWidget(
        _panel(
            QtWidgets,
            "Prüfergebnisse",
            f"{validation_text}\n\n{path_text}\n\n{settings_text}",
        )
    )
    if latest is not None:
        context_layout.addWidget(
            _panel(
                QtWidgets,
                "Letztes Ereignis",
                f"{latest.severity.upper()} · {latest.diagnostic_id}\n{latest.data_state}",
            )
        )
    context_layout.addStretch(1)
    context_scroll = QtWidgets.QScrollArea()
    context_scroll.setObjectName("contextScroll")
    context_scroll.setWidgetResizable(True)
    context_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    context_scroll.setWidget(context_body)
    context = _zone(QtWidgets.QFrame(), "contextRail", 7)
    context.setFixedWidth(320)
    context_layout_outer = QtWidgets.QVBoxLayout(context)
    context_layout_outer.addWidget(context_scroll)
    grid.addWidget(context, 1, 2, 4, 1)

    action_bar = _zone(QtWidgets.QFrame(), "actionBar", 8)
    bottom = QtWidgets.QHBoxLayout(action_bar)
    activation_status = _label(
        QtWidgets,
        "✓ Primärinstanz aktiv · Papierkorb atomar · Diagnose ausschließlich lesend",
        "statusOk",
        safety=True,
    )
    activation_status.setObjectName("instanceActivationStatus")
    bottom.addWidget(activation_status)
    bottom.addStretch(1)
    focus_button = _button(
        QtWidgets,
        "Diagnose fokussieren",
        name="focusDiagnosticsButton",
        tooltip="Springt zur lokalen Diagnosekennungssuche.",
    )
    bottom.addWidget(focus_button)
    grid.addWidget(action_bar, 5, 1, 1, 2)

    footer = _zone(QtWidgets.QFrame(), "footer", 9)
    footer_layout = QtWidgets.QHBoxLayout(footer)
    footer_layout.addWidget(
        _label(
            QtWidgets,
            "🛡 Peer-UID · Projektpapierkorb 0700 · Manifest 0600 · Journal 0600",
            safety=True,
        )
    )
    footer_layout.addStretch(1)
    footer_layout.addWidget(
        _label(QtWidgets, "🔒 Keine dauerhafte Löschung · kein Upload · kein Auto-Export", safety=True)
    )
    grid.addWidget(footer, 6, 0, 1, 3)

    diagnosis_button.clicked.connect(lambda: diagnostics_controller.focus_diagnostic())
    focus_button.clicked.connect(lambda: diagnostics_controller.focus_diagnostic())
    trash_button.clicked.connect(lambda: workspace_scroll.ensureWidgetVisible(trash_contract))
    window.diagnosticsController = diagnostics_controller
    window.instanceActivationStatus = activation_status
    return window


def load_stylesheet() -> str:
    try:
        return (PROJECT_ROOT / "src" / "theme.qss").read_text(encoding="utf-8")
    except OSError:
        return ""


def _activate_window(window, request: LaunchRequest) -> None:
    if window.isMinimized():
        window.showNormal()
    else:
        window.show()
    window.raise_()
    window.activateWindow()
    handle = window.windowHandle()
    if handle is not None:
        handle.requestActivate()
    controller = getattr(window, "diagnosticsController", None)
    if request.action == "show-diagnostics" and controller is not None:
        controller.focus_diagnostic(request.diagnostic_id)
    status = getattr(window, "instanceActivationStatus", None)
    if status is not None:
        suffix = f" · Filter {request.diagnostic_id}" if request.diagnostic_id else ""
        status.setText("✓ Vorhandene Instanz sicher aktiviert" + suffix)


def run_gui(
    validation_text: str,
    path_text: str,
    settings_text: str,
    paths: XDGPaths,
    settings_result: SettingsLoadResult,
    event_center: ErrorEventCenter,
    coordinator: SingleInstanceCoordinator,
    initial_request: LaunchRequest,
) -> int:
    try:
        from PySide6 import QtCore, QtWidgets
    except ImportError as exc:
        event = event_center.capture(
            event_from_exception(exc, category="pyside6-import", context="PySide6 konnte nicht geladen werden.")
        )
        print(format_event_for_user(event), file=sys.stderr)
        coordinator.close()
        return 3

    class SafeApplication(QtWidgets.QApplication):
        eventRaised = QtCore.Signal(object)

        def notify(self, receiver, event):  # noqa: ANN001
            try:
                return super().notify(receiver, event)
            except BaseException as exc:
                captured = event_center.capture(
                    event_from_exception(
                        exc,
                        category="qt-event-exception",
                        context="Eine Ausnahme während eines Qt-Ereignisses wurde abgefangen.",
                    )
                )
                self.eventRaised.emit(captured)
                return False

    try:
        snapshot = read_diagnostics(event_center.journal.log_file)
    except ValueError as exc:
        captured = event_center.capture(
            event_from_exception(
                exc,
                category="diagnostics-read",
                context="Das Ereignisjournal konnte nicht sicher gelesen werden.",
                data_state="Das Journal wurde nicht verändert; die Diagnoseansicht startet leer.",
            )
        )
        snapshot = DiagnosticSnapshot((), (captured.cause,))

    app = SafeApplication(sys.argv)
    app.setApplicationName("MULTIMODULTOOL2026")
    app.setOrganizationName("provoware")
    if stylesheet := load_stylesheet():
        app.setStyleSheet(stylesheet)
    window = build_window(
        QtWidgets,
        QtCore,
        validation_text=validation_text,
        path_text=path_text,
        settings_text=settings_text,
        paths=paths,
        settings_result=settings_result,
        diagnostics=snapshot,
        event_center=event_center,
    )

    def display_event(event: ErrorEvent) -> None:
        show_error_dialog(QtWidgets, event, window)

    app.eventRaised.connect(display_event)
    install_exception_hooks(event_center, on_event=lambda event: app.eventRaised.emit(event))

    def process_secondary_requests() -> None:
        for request in coordinator.drain_messages(limit=100):
            _activate_window(window, request)

    instance_timer = QtCore.QTimer(window)
    instance_timer.setObjectName("singleInstanceMessageTimer")
    instance_timer.setInterval(100)
    instance_timer.timeout.connect(process_secondary_requests)
    instance_timer.start()

    window.show()
    QtCore.QTimer.singleShot(0, lambda: _activate_window(window, initial_request))
    if settings_result.recovered and event_center.latest is not None:
        QtCore.QTimer.singleShot(0, lambda: display_event(event_center.latest))
    try:
        return app.exec()
    finally:
        instance_timer.stop()
        coordinator.close()


def _blocking(event: ErrorEvent, code: int) -> int:
    print(format_event_for_user(event), file=sys.stderr)
    return code


def _instance_event(result: InstanceResult, *, blocked: bool) -> ErrorEvent:
    if blocked:
        return create_event(
            category="single-instance",
            severity="error",
            cause=result.message,
            consequence="Der neue Programmstart wurde kontrolliert blockiert.",
            data_state="Bestehende Instanz, Sperrdateien und Nutzerdaten blieben unverändert.",
            solution="XDG-Laufzeitpfad, Eigentümer, Dateityp und Instanzmetadaten prüfen.",
            next_step="Die Sperre nicht manuell überschreiben; Diagnose sichern und erneut prüfen.",
        )
    return create_event(
        category="single-instance-recovery",
        severity="warning",
        cause=result.message,
        consequence="Der aktuelle Start übernimmt kontrolliert die primäre Instanzrolle.",
        data_state="Nur eine eindeutig veraltete Socket- und Metadatensperre wurde entfernt.",
        solution="Keine Korrektur erforderlich; Instanzstatus prüfen.",
        next_step="Mit Diagnose oder freigegebenem Workflow fortfahren.",
    )


def _launch_request(args: argparse.Namespace) -> LaunchRequest:
    diagnostic_id = str(args.diagnostic_id or "").strip().upper()
    if args.show_diagnostics or diagnostic_id:
        return LaunchRequest("show-diagnostics", diagnostic_id)
    return LaunchRequest()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not is_supported_platform():
        return _blocking(
            create_event(
                category="platform",
                severity="error",
                cause=platform_error_text(),
                consequence="Der Start wurde blockiert.",
                data_state="Es wurden keine Daten verändert.",
                solution="Das Tool unter einem unterstützten Kubuntu-System starten.",
                next_step="Unter Linux ./start.sh ausführen.",
            ),
            4,
        )

    manifest = validate_manifest(MANIFEST_PATH, PROJECT_ROOT)
    manifest_text = format_validation_result(manifest)
    print(manifest_text)
    if not manifest.is_valid:
        return _blocking(
            event_from_messages(
                manifest.errors,
                category="manifest",
                cause_prefix="Der Projekt- und Layoutvertrag ist ungültig.",
                consequence="Oberfläche und produktive Funktionen bleiben gesperrt.",
                data_state="Keine XDG- oder Nutzerdaten wurden verändert.",
                solution="Manifestfehler im Repository beheben.",
                next_step="python3 tools/validate_repository.py ausführen.",
            ),
            2,
        )

    resolved = resolve_xdg_paths()
    if not resolved.is_valid or resolved.paths is None:
        return _blocking(
            event_from_messages(
                resolved.errors,
                category="xdg-resolution",
                cause_prefix="XDG-Pfade konnten nicht sicher berechnet werden.",
                consequence="Der Start wurde vor Schreibzugriff blockiert.",
                data_state="Programm- und Nutzerdaten bleiben unverändert.",
                solution="XDG-Umgebungsvariablen korrigieren.",
                next_step="--paths-only erneut ausführen.",
            ),
            5,
        )

    if args.paths_only:
        result = validate_xdg_paths(resolved.paths, project_root=PROJECT_ROOT)
        print(format_path_report(result, include_paths=True, prepared=False))
        return 0 if result.is_valid else 5

    if args.validate_only or args.settings_only:
        paths_result = validate_xdg_paths(resolved.paths, project_root=PROJECT_ROOT)
        print(format_path_report(paths_result, include_paths=False, prepared=False))
        if not paths_result.is_valid:
            return 5
        settings_result = inspect_settings(resolved.paths.config)
        print(format_settings_report(settings_result))
        if settings_result.recovered:
            print(format_event_for_user(event_from_settings_result(settings_result)))
        return 0 if settings_result.is_valid else 6

    path_result = ensure_xdg_paths(resolved.paths, project_root=PROJECT_ROOT)
    path_text = format_path_report(path_result, include_paths=False, prepared=True)
    print(path_text)
    if not path_result.is_valid or path_result.paths is None:
        return _blocking(
            event_from_messages(
                path_result.errors,
                category="xdg-prepare",
                cause_prefix="XDG-Verzeichnisse konnten nicht sicher vorbereitet werden.",
                consequence="Einstellungen und Oberfläche bleiben gesperrt.",
                data_state="Produktive Nutzerdaten blieben unverändert.",
                solution="Rechte, Symlinks und Mountzustand prüfen.",
                next_step="--validate-only erneut ausführen.",
            ),
            5,
        )

    journal = EventJournal(path_result.paths.logs)
    journal_errors = journal.validate()
    if journal_errors:
        return _blocking(
            event_from_messages(
                journal_errors,
                category="event-journal",
                cause_prefix="Das Ereignisjournal ist nicht sicher nutzbar.",
                consequence="Die Anwendung startet ohne verlässliches Fehlerjournal nicht.",
                data_state="Einstellungen und Nutzerdaten wurden nicht verändert.",
                solution="Logpfad, Symlinks, Dateityp und Rechte 0600 korrigieren.",
                next_step="Logpfad prüfen und ./start.sh erneut ausführen.",
            ),
            7,
        )
    event_center = ErrorEventCenter(journal)

    try:
        runtime_root = resolve_runtime_root()
    except BaseException as exc:
        return _blocking(
            event_center.capture(
                event_from_exception(
                    exc,
                    category="single-instance-runtime",
                    context="Der private Linux-Laufzeitpfad konnte nicht sicher bestimmt werden.",
                    data_state="Keine Instanzsperre und keine Nutzerdaten wurden verändert.",
                )
            ),
            8,
        )

    request = _launch_request(args)
    coordinator = SingleInstanceCoordinator(runtime_root)
    instance_result = coordinator.acquire(request)
    if instance_result.is_secondary:
        print("GRÜN: Bestehende MULTIMODULTOOL2026-Instanz wurde sicher aktiviert.")
        return 0
    if instance_result.is_blocked:
        return _blocking(event_center.capture(_instance_event(instance_result, blocked=True)), 8)
    if instance_result.recovered_stale:
        event_center.capture(_instance_event(instance_result, blocked=False))

    settings_result = load_or_recover_settings(path_result.paths.config)
    settings_text = format_settings_report(settings_result)
    print(settings_text)
    if settings_result.recovered:
        event_center.capture(event_from_settings_result(settings_result))
    if not settings_result.is_valid:
        coordinator.close()
        return _blocking(event_center.capture(event_from_settings_result(settings_result)), 6)

    return run_gui(
        manifest_text,
        path_text,
        settings_text,
        path_result.paths,
        settings_result,
        event_center,
        coordinator,
        request,
    )


def cli_entrypoint(argv: list[str] | None = None) -> int:
    """Letzte Schutzschicht für unerwartete Bootstrap-Ausnahmen."""

    try:
        return main(argv)
    except KeyboardInterrupt:
        return _blocking(
            create_event(
                category="user-interrupt",
                severity="warning",
                cause="Der Start wurde durch den Nutzer unterbrochen.",
                consequence="Der aktuelle Startschritt wurde beendet.",
                data_state="Bereits bestätigte Dateien bleiben vollständig.",
                solution="Laufende Setup- oder Schreibvorgänge vor dem Neustart prüfen.",
                next_step="Danach ./start.sh erneut ausführen.",
            ),
            130,
        )
    except BaseException as exc:
        return _blocking(
            event_from_exception(
                exc,
                category="bootstrap-exception",
                context="Eine unerwartete Ausnahme während des Programmstarts wurde abgefangen.",
                data_state="Der Start wurde kontrolliert beendet; produktive Dateiaktionen waren gesperrt.",
            ),
            70,
        )


if __name__ == "__main__":
    raise SystemExit(cli_entrypoint())
