"""Linux-Desktop-Grundgerüst mit sicherer XDG-Pfadverwaltung."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .manifest_validator import format_validation_result, validate_manifest
from .xdg_paths import (
    XDGPaths,
    ensure_xdg_paths,
    format_path_report,
    resolve_xdg_paths,
    validate_xdg_paths,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / "layout-manifest.json"
DEVELOPMENT_PROGRESS = 31


def is_supported_platform(platform_name: str | None = None) -> bool:
    """Nur Linux ist Teil des verbindlichen Projektumfangs."""

    return (platform_name or sys.platform).startswith("linux")


def platform_error_text() -> str:
    return (
        "FEHLER: MULTIMODULTOOL2026 wird ausschließlich für Linux-Desktop-Systeme gebaut.\n"
        "Unterstützt: Kubuntu 22.04/24.04, KDE Plasma, X11 oder Wayland.\n"
        "Dieses System wird nicht unterstützt. Es wurden keine Daten verändert."
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MULTIMODULTOOL2026 starten oder prüfen")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Linux-, Manifest- und XDG-Vertrag rein lesend prüfen.",
    )
    parser.add_argument(
        "--paths-only",
        action="store_true",
        help="Berechnete XDG-Speicherorte anzeigen und ohne Oberfläche beenden.",
    )
    return parser.parse_args(argv)


def _display_path(path: Path) -> str:
    try:
        return f"~/{path.relative_to(Path.home())}"
    except ValueError:
        return str(path)


def _card(QtWidgets, title: str, value: str, detail: str = ""):
    frame = QtWidgets.QFrame()
    frame.setObjectName("card")
    layout = QtWidgets.QVBoxLayout(frame)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(4)
    title_label = QtWidgets.QLabel(title)
    title_label.setObjectName("muted")
    value_label = QtWidgets.QLabel(value)
    value_label.setObjectName("cardValue")
    value_label.setWordWrap(True)
    layout.addWidget(title_label)
    layout.addWidget(value_label)
    if detail:
        detail_label = QtWidgets.QLabel(detail)
        detail_label.setObjectName("smallMuted")
        detail_label.setWordWrap(True)
        layout.addWidget(detail_label)
    return frame


def _button(
    QtWidgets,
    text: str,
    *,
    accent: str = "",
    active: bool = False,
    enabled: bool = True,
    tooltip: str = "",
):
    button = QtWidgets.QPushButton(text)
    if accent:
        button.setProperty("accent", accent)
    if active:
        button.setProperty("active", True)
    button.setEnabled(enabled)
    button.setMinimumHeight(48)
    if tooltip:
        button.setToolTip(tooltip)
    return button


def _section(QtWidgets, title: str, body: str, object_name: str = "panel"):
    frame = QtWidgets.QFrame()
    frame.setObjectName(object_name)
    layout = QtWidgets.QVBoxLayout(frame)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(8)
    heading = QtWidgets.QLabel(title)
    heading.setObjectName("sectionTitle")
    content = QtWidgets.QLabel(body)
    content.setWordWrap(True)
    content.setObjectName("muted")
    layout.addWidget(heading)
    layout.addWidget(content)
    return frame


def _workflow_step(QtWidgets, QtCore, number: str, title: str, state: str):
    frame = QtWidgets.QFrame()
    frame.setProperty("workflowState", state)
    layout = QtWidgets.QHBoxLayout(frame)
    layout.setContentsMargins(10, 8, 10, 8)
    layout.setSpacing(7)
    badge = QtWidgets.QLabel(number)
    badge.setObjectName("stepBadge")
    badge.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
    badge.setFixedSize(28, 28)
    label = QtWidgets.QLabel(title)
    label.setObjectName("stepTitle")
    layout.addWidget(badge)
    layout.addWidget(label)
    layout.addStretch(1)
    return frame


def _path_panel(QtWidgets, QtCore, paths: XDGPaths):
    frame = QtWidgets.QFrame()
    frame.setObjectName("panel")
    layout = QtWidgets.QVBoxLayout(frame)
    layout.setContentsMargins(14, 14, 14, 14)
    layout.setSpacing(7)
    title = QtWidgets.QLabel("Sichere Linux-Speicherorte")
    title.setObjectName("sectionTitle")
    subtitle = QtWidgets.QLabel("Programmdateien und Nutzerdaten sind strikt getrennt.")
    subtitle.setObjectName("smallMuted")
    subtitle.setWordWrap(True)
    layout.addWidget(title)
    layout.addWidget(subtitle)
    for label, path in paths.items():
        row = QtWidgets.QFrame()
        row.setObjectName("pathRow")
        row_layout = QtWidgets.QVBoxLayout(row)
        row_layout.setContentsMargins(9, 6, 9, 6)
        row_layout.setSpacing(2)
        name = QtWidgets.QLabel(f"✓ {label}")
        name.setObjectName("pathName")
        value = QtWidgets.QLabel(_display_path(path))
        value.setObjectName("pathValue")
        value.setWordWrap(True)
        value.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
        )
        row_layout.addWidget(name)
        row_layout.addWidget(value)
        layout.addWidget(row)
    layout.addStretch(1)
    return frame


def build_window(
    QtWidgets,
    QtCore,
    *,
    validation_text: str,
    path_text: str,
    paths: XDGPaths,
):
    class MainWindow(QtWidgets.QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("MULTIMODULTOOL2026 – Linux")
            self.resize(1500, 900)
            self.setMinimumSize(1024, 680)

            central = QtWidgets.QWidget()
            shell = QtWidgets.QGridLayout(central)
            shell.setContentsMargins(12, 12, 12, 12)
            shell.setHorizontalSpacing(12)
            shell.setVerticalSpacing(10)
            shell.setColumnStretch(1, 1)
            shell.setRowStretch(4, 1)
            self.setCentralWidget(central)

            header = QtWidgets.QFrame()
            header.setObjectName("header")
            header_layout = QtWidgets.QHBoxLayout(header)
            header_layout.setContentsMargins(18, 10, 18, 10)
            identity = QtWidgets.QVBoxLayout()
            identity.setSpacing(1)
            title = QtWidgets.QLabel("◈  MULTIMODULTOOL2026")
            title.setObjectName("appTitle")
            subtitle = QtWidgets.QLabel(
                "Sicher organisieren: erst auswählen, dann prüfen, erst danach verändern."
            )
            subtitle.setObjectName("smallMuted")
            identity.addWidget(title)
            identity.addWidget(subtitle)
            safety = QtWidgets.QLabel("● XDG- UND SYSTEMPRÜFUNG GRÜN")
            safety.setObjectName("statusOk")
            header_layout.addLayout(identity)
            header_layout.addStretch(1)
            header_layout.addWidget(safety)
            shell.addWidget(header, 0, 0, 1, 3)

            navigation = QtWidgets.QFrame()
            navigation.setObjectName("navigation")
            navigation.setFixedWidth(178)
            nav_layout = QtWidgets.QVBoxLayout(navigation)
            nav_layout.setContentsMargins(10, 12, 10, 12)
            nav_layout.setSpacing(7)
            nav_title = QtWidgets.QLabel("HAUPTBEREICHE")
            nav_title.setObjectName("navTitle")
            nav_layout.addWidget(nav_title)
            for label, active in (
                ("⌂  Start", True),
                ("⌕  Analysieren", False),
                ("▣  Duplikate", False),
                ("↕  Organisieren", False),
                ("✎  Umbenennen", False),
                ("▤  Berichte", False),
                ("♲  Papierkorb", False),
            ):
                nav_layout.addWidget(
                    _button(
                        QtWidgets,
                        label,
                        active=active,
                        tooltip=(
                            "Aktuelle Startübersicht."
                            if active
                            else "Wird nach Freigabe des sicheren Kernworkflows aktiv."
                        ),
                    )
                )
            nav_layout.addStretch(1)
            nav_layout.addWidget(_button(QtWidgets, "⚙  Einstellungen"))
            nav_layout.addWidget(_button(QtWidgets, "?  Hilfe"))
            shell.addWidget(navigation, 1, 0, 5, 1)

            summary = QtWidgets.QWidget()
            summary_layout = QtWidgets.QHBoxLayout(summary)
            summary_layout.setContentsMargins(0, 0, 0, 0)
            summary_layout.setSpacing(8)
            for title_text, value, detail in (
                ("System", "Linux / KDE", "X11 und Wayland vorgesehen"),
                ("Speichertrennung", "6 / 6 GRÜN", "XDG-konform vorbereitet"),
                ("Sicherheitsmodus", "Nur Vorschau", "Keine Dateiaktion aktiv"),
                ("Entwicklung", "31 %", "19 erledigt · 43 offen"),
            ):
                summary_layout.addWidget(_card(QtWidgets, title_text, value, detail))
            shell.addWidget(summary, 1, 1, 1, 1)

            actions = QtWidgets.QWidget()
            actions_layout = QtWidgets.QHBoxLayout(actions)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(7)
            for text, accent in (
                ("1\nOrdner wählen", "cyan"),
                ("2\nBestand prüfen", "blue"),
                ("3\nRegeln wählen", "magenta"),
                ("4\nVorschau", "amber"),
                ("5\nSicher anwenden", "green"),
                ("6\nBericht", "cyan"),
            ):
                actions_layout.addWidget(
                    _button(
                        QtWidgets,
                        text,
                        accent=accent,
                        enabled=False,
                        tooltip=(
                            "Noch nicht freigeschaltet. Produktive Funktionen folgen "
                            "erst nach Einstellungen, Fehlerzentrale, Papierkorb und Undo."
                        ),
                    )
                )
            shell.addWidget(actions, 2, 1, 1, 1)

            process = QtWidgets.QFrame()
            process.setObjectName("workflowPanel")
            process_layout = QtWidgets.QVBoxLayout(process)
            process_layout.setContentsMargins(14, 12, 14, 12)
            process_layout.setSpacing(8)
            process_title = QtWidgets.QLabel("GEFÜHRTER SICHERHEITS-WORKFLOW")
            process_title.setObjectName("navTitle")
            process_layout.addWidget(process_title)
            step_row = QtWidgets.QHBoxLayout()
            step_row.setSpacing(6)
            for number, name, state in (
                ("1", "Quelle", "active"),
                ("2", "Analyse", "pending"),
                ("3", "Vorschau", "pending"),
                ("4", "Freigabe", "locked"),
                ("5", "Bericht", "locked"),
            ):
                step_row.addWidget(
                    _workflow_step(QtWidgets, QtCore, number, name, state)
                )
            process_layout.addLayout(step_row)
            progress = QtWidgets.QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(DEVELOPMENT_PROGRESS)
            progress.setFormat("Entwicklungsstand: 31 %")
            process_layout.addWidget(progress)
            shell.addWidget(process, 3, 1, 1, 1)

            workspace = QtWidgets.QFrame()
            workspace.setObjectName("workspace")
            workspace_layout = QtWidgets.QVBoxLayout(workspace)
            workspace_layout.setContentsMargins(16, 16, 16, 16)
            workspace_layout.setSpacing(12)

            hero = QtWidgets.QFrame()
            hero.setObjectName("hero")
            hero_layout = QtWidgets.QHBoxLayout(hero)
            hero_layout.setContentsMargins(18, 14, 18, 14)
            hero_text = QtWidgets.QVBoxLayout()
            hero_title = QtWidgets.QLabel("Nächster sinnvoller Schritt")
            hero_title.setObjectName("heroTitle")
            hero_body = QtWidgets.QLabel(
                "Die Linux-Speicherorte sind sicher getrennt. Als Nächstes folgt "
                "das transaktionale Einstellungsformat mit Backup und Rollback."
            )
            hero_body.setObjectName("muted")
            hero_body.setWordWrap(True)
            hero_text.addWidget(hero_title)
            hero_text.addWidget(hero_body)
            hero_status = QtWidgets.QLabel("P0-002  ✓ ABGESCHLOSSEN")
            hero_status.setObjectName("statusOk")
            hero_layout.addLayout(hero_text, 1)
            hero_layout.addWidget(hero_status)
            workspace_layout.addWidget(hero)

            workflow_cards = QtWidgets.QHBoxLayout()
            workflow_cards.setSpacing(9)
            for heading, body in (
                (
                    "1. Quelle auswählen",
                    "Später wird ein Ordner ausschließlich über einen geprüften "
                    "Linux-Auswahldialog gewählt. Noch erfolgt keine Dateiänderung.",
                ),
                (
                    "2. Wirkung verstehen",
                    "Vor jeder Aktion erscheinen Umfang, Konflikte, Speicherbedarf, "
                    "Risiko und Rückfallweg in einfacher Sprache.",
                ),
                (
                    "3. Kontrolliert anwenden",
                    "Erst nach vollständiger Vorschau und bewusster Freigabe darf "
                    "eine reversible Operation starten.",
                ),
            ):
                workflow_cards.addWidget(_section(QtWidgets, heading, body), 1)
            workspace_layout.addLayout(workflow_cards)
            workspace_layout.addWidget(
                _section(
                    QtWidgets,
                    "Aktuelle Schutzgrenze",
                    "Analyse-, Umbenennungs-, Verschiebe- und Löschfunktionen bleiben "
                    "gesperrt. So verändert der unfertige Entwicklungsstand keine privaten Dateien.",
                    "warningPanel",
                )
            )
            workspace_layout.addStretch(1)

            workspace_scroll = QtWidgets.QScrollArea()
            workspace_scroll.setObjectName("workspaceScroll")
            workspace_scroll.setWidgetResizable(True)
            workspace_scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
            workspace_scroll.setHorizontalScrollBarPolicy(
                QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )
            workspace_scroll.setWidget(workspace)
            shell.addWidget(workspace_scroll, 4, 1, 1, 1)

            context = QtWidgets.QFrame()
            context.setObjectName("contextRail")
            context.setFixedWidth(285)
            context_layout = QtWidgets.QVBoxLayout(context)
            context_layout.setContentsMargins(10, 10, 10, 10)
            context_layout.setSpacing(9)
            context_layout.addWidget(_path_panel(QtWidgets, QtCore, paths), 1)
            context_layout.addWidget(
                _section(QtWidgets, "Prüfergebnis", f"{validation_text}\n\n{path_text}")
            )
            shell.addWidget(context, 1, 2, 4, 1)

            action_bar = QtWidgets.QFrame()
            action_bar.setObjectName("actionBar")
            action_layout = QtWidgets.QHBoxLayout(action_bar)
            action_layout.setContentsMargins(14, 8, 14, 8)
            state = QtWidgets.QLabel("✓ Programm und Nutzerdaten strikt getrennt")
            state.setObjectName("statusOk")
            action_layout.addWidget(state)
            action_layout.addStretch(1)
            action_layout.addWidget(
                _button(
                    QtWidgets,
                    "System erneut prüfen",
                    accent="cyan",
                    tooltip="Die sichtbare Wiederholungsdiagnose folgt in einer späteren Iteration.",
                )
            )
            action_layout.addWidget(
                _button(
                    QtWidgets,
                    "Weiter zu Einstellungen",
                    accent="magenta",
                    enabled=False,
                    tooltip="Wird mit P0-003 freigeschaltet.",
                )
            )
            shell.addWidget(action_bar, 5, 1, 1, 2)

            footer = QtWidgets.QFrame()
            footer.setObjectName("footer")
            footer_layout = QtWidgets.QHBoxLayout(footer)
            footer_layout.setContentsMargins(16, 7, 16, 7)
            footer_layout.addWidget(
                QtWidgets.QLabel(
                    "🛡 XDG-Pfade geprüft · Modus 0700 · keine Quelldaten beschrieben"
                )
            )
            footer_layout.addStretch(1)
            footer_layout.addWidget(
                QtWidgets.QLabel("🔒 Produktive Dateiaktionen weiterhin gesperrt")
            )
            shell.addWidget(footer, 6, 0, 1, 3)

    return MainWindow()


def load_stylesheet() -> str:
    try:
        return (PROJECT_ROOT / "src" / "theme.qss").read_text(encoding="utf-8")
    except OSError:
        return ""


def run_gui(validation_text: str, path_text: str, paths: XDGPaths) -> int:
    try:
        from PySide6 import QtCore, QtWidgets
    except ImportError:
        print(
            "FEHLER: PySide6 fehlt.\n"
            "Lösung: ./setup.sh ausführen und danach erneut ./start.sh starten.",
            file=sys.stderr,
        )
        return 3

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("MULTIMODULTOOL2026")
    app.setOrganizationName("provoware")
    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)
    window = build_window(
        QtWidgets,
        QtCore,
        validation_text=validation_text,
        path_text=path_text,
        paths=paths,
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

    if args.validate_only or args.paths_only:
        path_result = validate_xdg_paths(resolved.paths, project_root=PROJECT_ROOT)
        print(
            format_path_report(
                path_result,
                include_paths=args.paths_only,
                prepared=False,
            )
        )
        return 0 if path_result.is_valid else 5

    path_result = ensure_xdg_paths(resolved.paths, project_root=PROJECT_ROOT)
    path_text = format_path_report(path_result, include_paths=False, prepared=True)
    print(path_text)
    if not path_result.is_valid or path_result.paths is None:
        return 5
    return run_gui(manifest_text, path_text, path_result.paths)


if __name__ == "__main__":
    raise SystemExit(main())
