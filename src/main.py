"""Linux-Desktop-App mit XDG-Pfaden und transaktionalen Einstellungen."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .manifest_validator import format_validation_result, validate_manifest
from .settings_manager import (
    SettingsLoadResult,
    format_settings_report,
    inspect_settings,
    load_or_recover_settings,
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
DEVELOPMENT_PROGRESS = 33
COMPLETED_POINTS = 21
OPEN_POINTS = 42
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
        "FEHLER: MULTIMODULTOOL2026 wird ausschließlich für Linux-Desktop-Systeme gebaut.\n"
        "Unterstützt: Kubuntu 22.04/24.04, KDE Plasma, X11 oder Wayland.\n"
        "Es wurden keine Daten verändert."
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MULTIMODULTOOL2026 starten oder prüfen")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--paths-only", action="store_true")
    parser.add_argument("--settings-only", action="store_true")
    return parser.parse_args(argv)


def _label(QtWidgets, text: str, name: str = "muted", *, safety: bool = False):
    item = QtWidgets.QLabel(text)
    item.setObjectName(name)
    item.setWordWrap(True)
    if safety:
        item.setProperty("safetyStatus", True)
    return item


def _button(QtWidgets, text: str, *, enabled: bool = True, name: str = "", tooltip: str = ""):
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


def _zone(widget, object_name: str, zone_id: str):
    widget.setObjectName(object_name)
    widget.setProperty("zoneId", zone_id)
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
):
    """Neun sichtbare und maschinenprüfbare Layoutzonen erzeugen."""

    window = QtWidgets.QMainWindow()
    window.setWindowTitle("MULTIMODULTOOL2026 – Linux")
    window.resize(1500, 900)
    window.setMinimumSize(1024, 680)
    central = QtWidgets.QWidget()
    shell = QtWidgets.QGridLayout(central)
    shell.setContentsMargins(12, 12, 12, 12)
    shell.setSpacing(9)
    shell.setColumnStretch(1, 1)
    shell.setRowStretch(4, 1)
    window.setCentralWidget(central)

    header = _zone(QtWidgets.QFrame(), "header", "Z01")
    header_layout = QtWidgets.QHBoxLayout(header)
    identity = QtWidgets.QVBoxLayout()
    identity.addWidget(_label(QtWidgets, "◈  MULTIMODULTOOL2026", "appTitle"))
    identity.addWidget(_label(QtWidgets, "Erst prüfen, dann vorschauen, erst danach verändern.", "smallMuted"))
    header_layout.addLayout(identity)
    header_layout.addStretch(1)
    header_layout.addWidget(
        _label(QtWidgets, "● SYSTEM-, XDG- UND EINSTELLUNGSPRÜFUNG GRÜN", "statusOk", safety=True)
    )
    shell.addWidget(header, 0, 0, 1, 3)

    navigation = _zone(QtWidgets.QFrame(), "navigation", "Z02")
    navigation.setFixedWidth(178)
    nav = QtWidgets.QVBoxLayout(navigation)
    nav.addWidget(_label(QtWidgets, "HAUPTBEREICHE", "navTitle"))
    nav.addWidget(_button(QtWidgets, "⌂  Start"))
    locked_tip = "Noch gesperrt, bis der sichere Kernworkflow vollständig ist."
    for text in ("⌕  Analysieren", "▣  Duplikate", "↕  Organisieren", "✎  Umbenennen", "▤  Berichte", "♲  Papierkorb"):
        nav.addWidget(_button(QtWidgets, text, enabled=False, name="lockedNavigation", tooltip=locked_tip))
    nav.addStretch(1)
    nav.addWidget(_button(QtWidgets, "⚙  Einstellungen", enabled=False, tooltip="Dateiformat aktiv; Bedienseite folgt."))
    nav.addWidget(_button(QtWidgets, "?  Hilfe"))
    shell.addWidget(navigation, 1, 0, 5, 1)

    summary = _zone(QtWidgets.QWidget(), "summaryCards", "Z03")
    cards = QtWidgets.QHBoxLayout(summary)
    status = "WIEDERHERGESTELLT" if settings_result.recovered else "1 / 1 GRÜN"
    for title, value, detail in (
        ("System", "Linux / KDE", "X11 und Wayland"),
        ("XDG-Speicher", "6 / 6 GRÜN", "Pfade 0700"),
        ("Einstellungen", status, "Schema 1 · Dateien 0600"),
        ("Entwicklung", "33 %", "21 erledigt · 42 offen"),
    ):
        cards.addWidget(_panel(QtWidgets, title, f"{value}\n{detail}", "card"))
    shell.addWidget(summary, 1, 1, 1, 1)

    actions = _zone(QtWidgets.QWidget(), "primaryActionTiles", "Z04")
    action_layout = QtWidgets.QHBoxLayout(actions)
    for text in ("1\nOrdner wählen", "2\nBestand prüfen", "3\nRegeln wählen", "4\nVorschau", "5\nSicher anwenden", "6\nBericht"):
        action_layout.addWidget(
            _button(QtWidgets, text, enabled=False, name="lockedPrimaryAction", tooltip=locked_tip)
        )
    shell.addWidget(actions, 2, 1, 1, 1)

    workflow = _zone(QtWidgets.QFrame(), "workflowPanel", "Z05")
    flow = QtWidgets.QVBoxLayout(workflow)
    flow.addWidget(_label(QtWidgets, "GEFÜHRTER SICHERHEITS-WORKFLOW", "navTitle"))
    flow.addWidget(_label(QtWidgets, "1 Quelle  →  2 Analyse  →  3 Vorschau  →  4 Freigabe  →  5 Bericht", "sectionTitle"))
    progress = QtWidgets.QProgressBar()
    progress.setRange(0, 100)
    progress.setValue(DEVELOPMENT_PROGRESS)
    progress.setFormat("Entwicklungsstand: 33 %")
    flow.addWidget(progress)
    shell.addWidget(workflow, 3, 1, 1, 1)

    workspace = QtWidgets.QWidget()
    workspace_layout = QtWidgets.QVBoxLayout(workspace)
    workspace_layout.addWidget(
        _panel(
            QtWidgets,
            "P0-003 abgeschlossen",
            "Versionierte Einstellungen werden vorvalidiert, atomar gespeichert und bei Beschädigung aus Backup oder sicheren Standardwerten wiederhergestellt.",
            "hero",
        )
    )
    row = QtWidgets.QHBoxLayout()
    row.addWidget(_panel(QtWidgets, "1. Sicher laden", "Version, Felder, Typen und Wertebereiche prüfen."))
    row.addWidget(_panel(QtWidgets, "2. Atomar speichern", "Temporäre Datei, fsync, Nachvalidierung und os.replace."))
    row.addWidget(_panel(QtWidgets, "3. Zurückfallen", "Defekt isolieren und letzte gültige Sicherung aktivieren."))
    workspace_layout.addLayout(row)
    workspace_layout.addWidget(
        _panel(QtWidgets, "Aktuelle Schutzgrenze", "Produktive Dateiaktionen bleiben gesperrt. Nächster Schritt: globale Fehlerzentrale.", "warningPanel")
    )
    workspace_layout.addStretch(1)
    workspace_scroll = _zone(QtWidgets.QScrollArea(), "workspaceScroll", "Z06")
    workspace_scroll.setWidgetResizable(True)
    workspace_scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
    workspace_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    workspace_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    workspace_scroll.setWidget(workspace)
    shell.addWidget(workspace_scroll, 4, 1, 1, 1)

    context = _zone(QtWidgets.QFrame(), "contextRail", "Z07")
    context.setFixedWidth(290)
    context_layout = QtWidgets.QVBoxLayout(context)
    context_content = QtWidgets.QWidget()
    context_items = QtWidgets.QVBoxLayout(context_content)
    context_items.addWidget(_panel(QtWidgets, "Einstellungen", settings_text, "settingsPanel"))
    context_items.addWidget(_panel(QtWidgets, "Systemprüfung", f"{validation_text}\n\n{path_text}"))
    paths_text = "\n".join(f"✓ {name}: {_display_path(path)}" for name, path in paths.items())
    context_items.addWidget(_panel(QtWidgets, "Sichere Speicherorte", paths_text))
    context_items.addStretch(1)
    context_scroll = QtWidgets.QScrollArea()
    context_scroll.setObjectName("contextScroll")
    context_scroll.setWidgetResizable(True)
    context_scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
    context_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    context_scroll.setWidget(context_content)
    context_layout.addWidget(context_scroll)
    shell.addWidget(context, 1, 2, 4, 1)

    action_bar = _zone(QtWidgets.QFrame(), "actionBar", "Z08")
    action_layout = QtWidgets.QHBoxLayout(action_bar)
    action_layout.addWidget(
        _label(QtWidgets, "✓ XDG-Pfade und versionierte Einstellungen sicher vorbereitet", "statusOk", safety=True)
    )
    action_layout.addStretch(1)
    action_layout.addWidget(_button(QtWidgets, "Diagnose erneut prüfen", enabled=False, tooltip="Folgt mit P0-004."))
    action_layout.addWidget(_button(QtWidgets, "Weiter zur Fehlerzentrale", enabled=False, tooltip="Wird mit P0-004 freigeschaltet."))
    shell.addWidget(action_bar, 5, 1, 1, 2)

    footer = _zone(QtWidgets.QFrame(), "footer", "Z09")
    footer_layout = QtWidgets.QHBoxLayout(footer)
    footer_layout.addWidget(
        _label(QtWidgets, "🛡 XDG 0700 · Einstellungen 0600 · atomarer Austausch · Rollback bereit", safety=True)
    )
    footer_layout.addStretch(1)
    footer_layout.addWidget(_label(QtWidgets, "🔒 Produktive Dateiaktionen weiterhin gesperrt"))
    shell.addWidget(footer, 6, 0, 1, 3)
    return window


def load_stylesheet() -> str:
    try:
        return (PROJECT_ROOT / "src" / "theme.qss").read_text(encoding="utf-8")
    except OSError:
        return ""


def run_gui(validation_text: str, path_text: str, settings_text: str, paths: XDGPaths, settings_result: SettingsLoadResult) -> int:
    try:
        from PySide6 import QtCore, QtGui, QtWidgets
    except ImportError:
        print("FEHLER: PySide6 fehlt. Lösung: ./setup.sh ausführen.", file=sys.stderr)
        return 3
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("MULTIMODULTOOL2026")
    app.setOrganizationName("provoware")
    scale = settings_result.settings["ui"]["fontScalePercent"] / 100
    font = QtGui.QFont(app.font())
    if font.pointSizeF() > 0:
        font.setPointSizeF(max(8.0, font.pointSizeF() * scale))
        app.setFont(font)
    style = load_stylesheet()
    if style:
        app.setStyleSheet(style)
    window = build_window(
        QtWidgets,
        QtCore,
        validation_text=validation_text,
        path_text=path_text,
        settings_text=settings_text,
        paths=paths,
        settings_result=settings_result,
    )
    window.show()
    return app.exec()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not is_supported_platform():
        print(platform_error_text(), file=sys.stderr)
        return 4

    manifest_result = validate_manifest(MANIFEST_PATH, PROJECT_ROOT)
    manifest_text = format_validation_result(manifest_result)
    print(manifest_text)
    if not manifest_result.is_valid:
        return 2

    resolved = resolve_xdg_paths()
    if not resolved.is_valid or resolved.paths is None:
        print(format_path_report(resolved, prepared=False), file=sys.stderr)
        return 5

    if args.paths_only:
        path_result = validate_xdg_paths(resolved.paths, project_root=PROJECT_ROOT)
        print(format_path_report(path_result, include_paths=True, prepared=False))
        return 0 if path_result.is_valid else 5

    if args.validate_only or args.settings_only:
        path_result = validate_xdg_paths(resolved.paths, project_root=PROJECT_ROOT)
        print(format_path_report(path_result, include_paths=False, prepared=False))
        if not path_result.is_valid:
            return 5
        settings_result = inspect_settings(resolved.paths.config)
        print(format_settings_report(settings_result))
        return 0 if settings_result.is_valid else 6

    path_result = ensure_xdg_paths(resolved.paths, project_root=PROJECT_ROOT)
    path_text = format_path_report(path_result, include_paths=False, prepared=True)
    print(path_text)
    if not path_result.is_valid or path_result.paths is None:
        return 5
    settings_result = load_or_recover_settings(path_result.paths.config)
    settings_text = format_settings_report(settings_result)
    print(settings_text)
    if not settings_result.is_valid:
        return 6
    return run_gui(manifest_text, path_text, settings_text, path_result.paths, settings_result)


if __name__ == "__main__":
    raise SystemExit(main())
