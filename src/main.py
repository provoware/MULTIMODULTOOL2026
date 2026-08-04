"""Startbares Linux-Desktop-Grundgerüst für MULTIMODULTOOL2026."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .manifest_validator import format_validation_result, validate_manifest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / "layout-manifest.json"


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
        help="Linux- und Manifestvertrag prüfen und ohne Oberfläche beenden.",
    )
    return parser.parse_args(argv)


def _card(QtWidgets, title: str, value: str, object_name: str = "card"):
    frame = QtWidgets.QFrame()
    frame.setObjectName(object_name)
    layout = QtWidgets.QVBoxLayout(frame)
    layout.setContentsMargins(14, 12, 14, 12)
    title_label = QtWidgets.QLabel(title)
    title_label.setObjectName("muted")
    value_label = QtWidgets.QLabel(value)
    value_label.setObjectName("cardValue")
    layout.addWidget(title_label)
    layout.addWidget(value_label)
    return frame


def _button(QtWidgets, text: str, accent: str = ""):
    button = QtWidgets.QPushButton(text)
    if accent:
        button.setProperty("accent", accent)
    button.setMinimumHeight(54)
    return button


def _section(QtWidgets, title: str, body: str):
    frame = QtWidgets.QFrame()
    frame.setObjectName("panel")
    layout = QtWidgets.QVBoxLayout(frame)
    layout.setContentsMargins(14, 14, 14, 14)
    heading = QtWidgets.QLabel(title)
    heading.setObjectName("sectionTitle")
    content = QtWidgets.QLabel(body)
    content.setWordWrap(True)
    content.setObjectName("muted")
    layout.addWidget(heading)
    layout.addWidget(content)
    layout.addStretch(1)
    return frame


def build_window(QtWidgets, validation_text: str):
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
            shell.setVerticalSpacing(12)
            shell.setColumnStretch(0, 0)
            shell.setColumnStretch(1, 1)
            shell.setColumnStretch(2, 0)
            shell.setRowStretch(4, 1)
            self.setCentralWidget(central)

            header = QtWidgets.QFrame()
            header.setObjectName("header")
            header_layout = QtWidgets.QHBoxLayout(header)
            title = QtWidgets.QLabel("◈  MULTIMODULTOOL2026")
            title.setObjectName("appTitle")
            safety = QtWidgets.QLabel("✓ Linux- und Manifestprüfung grün")
            safety.setObjectName("statusOk")
            header_layout.addWidget(title)
            header_layout.addStretch(1)
            header_layout.addWidget(safety)
            shell.addWidget(header, 0, 0, 1, 3)

            navigation = QtWidgets.QFrame()
            navigation.setObjectName("navigation")
            nav_layout = QtWidgets.QVBoxLayout(navigation)
            nav_layout.setContentsMargins(10, 10, 10, 10)
            for label in (
                "⌂  Übersicht",
                "▦  Module",
                "⌕  Suchen",
                "↕  Organisieren",
                "↶  Rückgängig",
                "⚙  Einstellungen",
                "?  Hilfe",
            ):
                nav_layout.addWidget(_button(QtWidgets, label))
            nav_layout.addStretch(1)
            shell.addWidget(navigation, 1, 0, 5, 1)

            summary = QtWidgets.QWidget()
            summary_layout = QtWidgets.QHBoxLayout(summary)
            summary_layout.setContentsMargins(0, 0, 0, 0)
            summary_layout.setSpacing(10)
            summary_layout.addWidget(_card(QtWidgets, "Plattform", "Linux / KDE"))
            summary_layout.addWidget(_card(QtWidgets, "Layoutvertrag", "9 / 9 Zonen"))
            summary_layout.addWidget(_card(QtWidgets, "Sicherheit", "Vorprüfung grün"))
            summary_layout.addWidget(_card(QtWidgets, "Nächster Schritt", "XDG-Pfade"))
            shell.addWidget(summary, 1, 1, 1, 1)

            actions = QtWidgets.QWidget()
            actions_layout = QtWidgets.QHBoxLayout(actions)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(10)
            for text, accent in (
                ("⌕\nAnalysieren", "cyan"),
                ("▣\nDuplikate", "magenta"),
                ("↕\nOrdnen", "green"),
                ("✎\nUmbenennen", "amber"),
                ("▤\nBerichte", "blue"),
                ("♲\nPapierkorb", "red"),
            ):
                actions_layout.addWidget(_button(QtWidgets, text, accent))
            shell.addWidget(actions, 2, 1, 1, 1)

            process = QtWidgets.QFrame()
            process.setObjectName("panel")
            process_layout = QtWidgets.QVBoxLayout(process)
            steps = QtWidgets.QLabel(
                "1  Quelle wählen     •     2  Vorschau prüfen     •     3  Sicher anwenden"
            )
            steps.setObjectName("sectionTitle")
            progress = QtWidgets.QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(27)
            progress.setFormat("Entwicklungsstand: 27 %")
            process_layout.addWidget(steps)
            process_layout.addWidget(progress)
            shell.addWidget(process, 3, 1, 1, 1)

            workspace = QtWidgets.QWidget()
            workspace_layout = QtWidgets.QHBoxLayout(workspace)
            workspace_layout.setContentsMargins(0, 0, 0, 0)
            workspace_layout.setSpacing(10)
            workspace_layout.addWidget(
                _section(
                    QtWidgets,
                    "1. Auswahl",
                    "Hier werden Linux-Ordner, Dateien oder gespeicherte Profile über geführte Dialoge gewählt.",
                )
            )
            workspace_layout.addWidget(
                _section(
                    QtWidgets,
                    "2. Regeln und Vorschau",
                    "Geplante Änderungen erscheinen vor der Ausführung vollständig und nachvollziehbar.",
                )
            )
            workspace_layout.addWidget(
                _section(
                    QtWidgets,
                    "3. Ergebnis",
                    "Nach der Aktion werden Wirkung, Protokoll, Rückfallweg und nächste Schritte angezeigt.",
                )
            )
            shell.addWidget(workspace, 4, 1, 1, 1)

            context = QtWidgets.QFrame()
            context.setObjectName("contextRail")
            context_layout = QtWidgets.QVBoxLayout(context)
            context_layout.addWidget(
                _section(QtWidgets, "Hinweis", "Wähle zuerst eine Funktionskachel.")
            )
            context_layout.addWidget(_section(QtWidgets, "Diagnose", validation_text))
            shell.addWidget(context, 1, 2, 4, 1)

            action_bar = QtWidgets.QFrame()
            action_bar.setObjectName("panel")
            action_layout = QtWidgets.QHBoxLayout(action_bar)
            action_layout.addWidget(QtWidgets.QLabel("✓ Linux-Vorprüfung erfolgreich"))
            action_layout.addStretch(1)
            action_layout.addWidget(_button(QtWidgets, "↶ Rückgängig"))
            action_layout.addWidget(_button(QtWidgets, "Sicher fortfahren", "magenta"))
            shell.addWidget(action_bar, 5, 1, 1, 2)

            footer = QtWidgets.QFrame()
            footer.setObjectName("footer")
            footer_layout = QtWidgets.QHBoxLayout(footer)
            footer_layout.addWidget(QtWidgets.QLabel("🛡 Lokale Linux-Verarbeitung vorbereitet"))
            footer_layout.addStretch(1)
            footer_layout.addWidget(QtWidgets.QLabel("🔒 Keine Änderung ohne Vorschau"))
            shell.addWidget(footer, 6, 0, 1, 3)

    return MainWindow()


def load_stylesheet() -> str:
    stylesheet_path = PROJECT_ROOT / "src" / "theme.qss"
    try:
        return stylesheet_path.read_text(encoding="utf-8")
    except OSError:
        return ""


def run_gui(validation_text: str) -> int:
    try:
        from PySide6 import QtWidgets
    except ImportError:
        print(
            "FEHLER: PySide6 fehlt.\n"
            "Lösung: python3 -m pip install -r requirements.txt\n"
            "Danach erneut ./start.sh ausführen.",
            file=sys.stderr,
        )
        return 3

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("MULTIMODULTOOL2026")
    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)
    window = build_window(QtWidgets, validation_text)
    window.show()
    return app.exec()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not is_supported_platform():
        print(platform_error_text(), file=sys.stderr)
        return 4

    result = validate_manifest(MANIFEST_PATH, PROJECT_ROOT)
    output = format_validation_result(result)
    print(output)

    if not result.is_valid:
        return 2
    if args.validate_only:
        return 0
    return run_gui(output)


if __name__ == "__main__":
    raise SystemExit(main())
