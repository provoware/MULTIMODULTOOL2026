"""Linux-Desktop-App mit XDG-Pfaden, Einstellungen und zentraler Fehlerarchitektur."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import threading

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
from .xdg_paths import (
    XDGPaths,
    ensure_xdg_paths,
    format_path_report,
    resolve_xdg_paths,
    validate_xdg_paths,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / "layout-manifest.json"
DEVELOPMENT_PROGRESS = 36
COMPLETED_POINTS = 23
OPEN_POINTS = 41
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
        "FEHLER: MULTIMODULTOOL2026 wird ausschlieÃŸlich fÃ¼r Linux-Desktop-Systeme gebaut.\n"
        "UnterstÃ¼tzt: Kubuntu 22.04/24.04, KDE Plasma, X11 oder Wayland.\n"
        "Es wurden keine Daten verÃ¤ndert."
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MULTIMODULTOOL2026 starten oder prÃ¼fen")
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


def _zone(widget, object_name: str, zone_id: str):
    widget.setObjectName(object_name)
    widget.setProperty("zoneId", zone_id)
    return widget


def _display_path(path: Path) -> str:
    try:
        return f"~/{path.relative_to(Path.home())}"
    except ValueError:
        return str(path)


def _event_center_text(event_center: ErrorEventCenter | None) -> str:
    if event_center is None:
        return "Zentrale Ereignisschicht vorbereitet; in diesem reinen Fenstertest ist kein Journal verbunden."
    latest = event_center.latest
    if latest is None:
        return "Aktiv Â· keine offenen Fehler Â· Diagnosekennungen und JSONL-Journal mit 0600 bereit."
    return (
        f"Letztes Ereignis: {latest.severity.upper()}\n"
        f"Diagnose: {latest.diagnostic_id}\n"
        f"Datenstand: {latest.data_state}"
    )


def build_window(
    QtWidgets,
    QtCore,
    *,
    validation_text: str,
    path_text: str,
    settings_text: str,
    paths: XDGPaths,
    settings_result: SettingsLoadResult,
    event_center: ErrorEventCenter | None = None,
):
    """Neun sichtbare und maschinenprÃ¼fbare Layoutzonen erzeugen."""

    window = QtWidgets.QMainWindow()
    window.setWindowTitle("MULTIMODULTOOL2026 â€“ Linux")
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
    identity.addWidget(_label(QtWidgets, "â—ˆ  MULTIMODULTOOL2026", "appTitle"))
    identity.addWidget(
        _label(
            QtWidgets,
            "Fehler kontrolliert stoppen, Datenstand erklÃ¤ren, sicheren nÃ¤chsten Schritt zeigen.",
            "smallMuted",
        )
    )
    header_layout.addLayout(identity)
    header_layout.addStretch(1)
    header_layout.addWidget(
        _label(
            QtWidgets,
            "â— ZENTRALE FEHLER-, XDG- UND EINSTELLUNGSPRÃœFUNG GRÃœN",
            "statusOk",
            safety=True,
        )
    )
    shell.addWidget(header, 0, 0, 1, 3)

    navigation = _zone(QtWidgets.QFrame(), "navigation", "Z02")
    navigation.setFixedWidth(178)
    nav = QtWidgets.QVBoxLayout(navigation)
    nav.addWidget(_label(QtWidgets, "HAUPTBEREICHE", "navTitle"))
    nav.addWidget(_button(QtWidgets, "âŒ‚  Start"))
    locked_tip = "Noch gesperrt, bis der sichere Kernworkflow vollstÃ¤ndig ist."
    for text in (
        "âŒ•  Analysieren",
        "â–£  Duplikate",
        "â†•  Organisieren",
        "âœŽ  Umbenennen",
        "â–¤  Berichte",
        "â™²  Papierkorb",
    ):
        nav.addWidget(
            _button(
                QtWidgets,
                text,
                enabled=False,
                name="lockedNavigation",
                tooltip=locked_tip,
            )
        )
    nav.addStretch(1)
    nav.addWidget(
        _button(
            QtWidgets,
            "âš™  Einstellungen",
            enabled=False,
            tooltip="Dateiformat aktiv; Bedienseite folgt.",
        )
    )
    nav.addWidget(_button(QtWidgets, "?  Hilfe"))
    shell.addWidget(navigation, 1, 0, 5, 1)

    summary = _zone(QtWidgets.QWidget(), "summaryCards", "Z03")
    cards = QtWidgets.QHBoxLayout(summary)
    settings_status = "WIEDERHERGESTELLT" if settings_result.recovered else "1 / 1 GRÃœN"
    error_status = "EREIGNIS VORHANDEN" if event_center and event_center.latest else "AKTIV"
    for title, value, detail in (
        ("System", "Linux / KDE", "X11 und Wayland"),
        ("Einstellungen", settings_status, "Schema 1 Â· Dateien 0600"),
        ("Fehlerzentrum", error_status, "6 Pflichtfelder Â· Diagnose-ID Â· Journal 0600"),
        ("Entwicklung", "36 %", "23 erledigt Â· 41 offen"),
    ):
        cards.addWidget(_panel(QtWidgets, title, f"{value}\n{detail}", "card"))
    shell.addWidget(summary, 1, 1, 1, 1)

    actions = _zone(QtWidgets.QWidget(), "primaryActionTiles", "Z04")
    action_layout = QtWidgets.QHBoxLayout(actions)
    for text in (
        "1\nOrdner wÃ¤hlen",
        "2\nBestand prÃ¼fen",
        "3\nRegeln wÃ¤hlen",
        "4\nVorschau",
        "5\nSicher anwenden",
        "6\nBericht",
    ):
        action_layout.addWidget(
            _button(
                QtWidgets,
                text,
                enabled=False,
                name="lockedP²È="24€€€€‘…Ñ…}ÍÑ…Ñ”ô‰ÌÝÕÉ‘•¸­•¥¹”Y•Éé•¥¡¹¥ÍÍ”°¥¹ÍÑ•±±Õ¹•¸½‘•È9ÕÑé•É‘…Ñ•¸Ù•Ë‘¹‘•ÉÐ¸ˆ°(€€€€€€€€€€€€€€€Í½±ÕÑ¥½¸ô‰…ÌAÉ½©•­ÐÕ¹Ñ•È-Õ‰Õ¹ÑÔ€ÈÈ¸ÀÐ¼ÈÐ¸ÀÐ½‘•È•¥¹•´­½µÁ…Ñ¥‰±•¸1¥¹Õàµ•Í­Ñ½ÀÍÑ…ÉÑ•¸¸ˆ°(€€€€€€€€€€€€€€€¹•áÑ}ÍÑ•Àô‰U¹Ñ•È1¥¹Õà€¸½ÍÑ…ÉÐ¹Í …ÕÍ›ñ¡É•¸¸ˆ°(€€€€€€€€€€€€¤°(€€€€€€€€€€€€Ð°(€€€€€€€€¤((€€€µ…¹¥™•ÍÑ}É•ÍÕ±Ð€ôÙ…±¥‘…Ñ•}µ…¹¥™•ÍÐ¡59%MQ}AQ °AI=)Q}I==P¤(€€€µ…¹¥™•ÍÑ}Ñ•áÐ€ô™½Éµ…Ñ}Ù…±¥‘…Ñ¥½¹}É•ÍÕ±Ð¡µ…¹¥™•ÍÑ}É•ÍÕ±Ð¤(€€€ÁÉ¥¹Ð¡µ…¹¥™•ÍÑ}Ñ•áÐ¤(€€€¥˜¹½Ðµ…¹¥™•ÍÑ}É•ÍÕ±Ð¹¥Í}Ù…±¥è(€€€€€€€É•ÑÕÉ¸}ÁÉ¥¹Ñ}‰±½­¥¹}•Ù•¹Ð (€€€€€€€€€€€•Ù•¹Ñ}™É½µ}µ•ÍÍ…•Ì (€€€€€€€€€€€€€€€µ…¹¥™•ÍÑ}É•ÍÕ±Ð¹•ÉÉ½ÉÌ°(€€€€€€€€€€€€€€€…Ñ•½Éäô‰µ…¹¥™•ÍÐˆ°(€€€€€€€€€€€€€€€…ÕÍ•}ÁÉ•™¥àô‰•ÈAÉ½©•­Ð´Õ¹1…å½ÕÑÙ•ÉÑÉ…œ¥ÍÐÕ¹Ÿñ±Ñ¥œ¸ˆ°(€€€€€€€€€€€€€€€½¹Í•ÅÕ•¹”ô‰¥”=‰•É™³‘¡”Õ¹…±±”ÁÉ½‘Õ­Ñ¥Ù•¸Õ¹­Ñ¥½¹•¸‰±•¥‰•¸•ÍÁ•ÉÉÐ¸ˆ°(€€€€€€€€€€€€€€€‘…Ñ…}ÍÑ…Ñ”ô‰ÌÝÕÉ‘•¸­•¥¹”aµY•Éé•¥¡¹¥ÍÍ”½‘•È9ÕÑé•É‘…Ñ•¸Ù•Ë‘¹‘•ÉÐ¸ˆ°(€€€€€€€€€€€€€€€Í½±ÕÑ¥½¸ô‰¥”•¹…¹¹Ñ•¸5…¹¥™•ÍÑ™•¡±•È¥´I•Á½Í¥Ñ½Éä‰•¡•‰•¸¸ˆ°(€€€€€€€€€€€€€€€¹•áÑ}ÍÑ•Àô‰ÁåÑ¡½¸ÌÑ½½±Ì½Ù…±¥‘…Ñ•}É•Á½Í¥Ñ½Éä¹Áä…ÕÍ›ñ¡É•¸Õ¹•ÉÍÐ‰•¤Ëñ¹•´É•‰¹¥Ì¹•ÔÍÑ…ÉÑ•¸¸ˆ°(€€€€€€€€€€€€¤°(€€€€€€€€€€€€È°(€€€€€€€€¤((€€€É•Í½±Ù•€ôÉ•Í½±Ù•}á‘}Á…Ñ¡Ì ¤(€€€¥˜¹½ÐÉ•Í½±Ù•¹¥Í}Ù…±¥½ÈÉ•Í½±Ù•¹Á…Ñ¡Ì¥Ì9½¹”è(€€€€€€€É•ÑÕÉ¸}ÁÉ¥¹Ñ}‰±½­¥¹}•Ù•¹Ð (€€€€€€€€€€€•Ù•¹Ñ}™É½µ}µ•ÍÍ…•Ì (€€€€€€€€€€€€€€€É•Í½±Ù•¹•ÉÉ½ÉÌ°(€€€€€€€€€€€€€€€…Ñ•½Éäô‰á‘œµÉ•Í½±ÕÑ¥½¸ˆ°(€€€€€€€€€€€€€€€…ÕÍ•}ÁÉ•™¥àô‰¥”aµA™…‘”­½¹¹Ñ•¸¹¥¡ÐÍ¥¡•È‰•É•¡¹•ÐÝ•É‘•¸¸ˆ°(€€€€€€€€€€€€€€€½¹Í•ÅÕ•¹”ô‰•ÈMÑ…ÉÐÝ¥ÉÙ½È©•‘•´M¡É•¥‰éÕÉ¥™˜‰±½­¥•ÉÐ¸ˆ°(€€€€€€€€€€€€€€€‘…Ñ…}ÍÑ…Ñ”ô‰AÉ½É…µµÙ•Éé•¥¡¹¥ÌÕ¹9ÕÑé•É‘…Ñ•¸‰±•¥‰•¸Õ¹Ù•Ë‘¹‘•ÉÐ¸ˆ°(€€€€€€€€€€€€€€€Í½±ÕÑ¥½¸ô‰I•±…Ñ¥Ù”½‘•ÈÕ¹éÕ³‘ÍÍ¥”aµUµ•‰Õ¹ÍÙ…É¥…‰±•¸­½ÉÉ¥¥•É•¸¸ˆ°(€€€€€€€€€€€€€€€¹•áÑ}ÍÑ•Àô‰ÁåÑ¡½¸Ì€µ´ÍÉŒ¹µ…¥¸€´µÁ…Ñ¡Ìµ½¹±ä•É¹•ÕÐ…ÕÍ›ñ¡É•¸¸ˆ°(€€€€€€€€€€€€¤°(€€€€€€€€€€€€Ô°(€€€€€€€€¤((€€€¥˜…ÉÌ¹Á…Ñ¡Í}½¹±äè(€€€€€€€Á…Ñ¡}É•ÍÕ±Ð€ôÙ…±¥‘…Ñ•}á‘}Á…Ñ¡Ì¡É•Í½±Ù•¹Á…Ñ¡Ì°ÁÉ½©•Ñ}É½½ÐõAI=)Q}I==P¤(€€€€€€€ÁÉ¥¹Ð¡™½Éµ…Ñ}Á…Ñ¡}É•Á½ÉÐ¡Á…Ñ¡}É•ÍÕ±Ð°¥¹±Õ‘•}Á…Ñ¡ÌõQÉÕ”°ÁÉ•Á…É•õ…±Í”¤¤(€€€€€€€¥˜Á…Ñ¡}É•ÍÕ±Ð¹¥Í}Ù…±¥è(€€€€€€€€€€€É•ÑÕÉ¸€À(€€€€€€€É•ÑÕÉ¸}ÁÉ¥¹Ñ}‰±½­¥¹}•Ù•¹Ð (€€€€€€€€€€€•Ù•¹Ñ}™É½µ}µ•ÍÍ…•Ì (€€€€€€€€€€€€€€€Á…Ñ¡}É•ÍÕ±Ð¹•ÉÉ½ÉÌ°(€€€€€€€€€€€€€€€…Ñ•½Éäô‰á‘œµÙ…±¥‘…Ñ¥½¸ˆ°(€€€€€€€€€€€€€€€…ÕÍ•}ÁÉ•™¥àô‰•ÈaµA™…‘Á±…¸Ù•É±•ÑéÐ•¥¹”M¥¡•É¡•¥ÑÍÉ•¹é”¸ˆ°(€€€€€€€€€€€€€€€½¹Í•ÅÕ•¹”ô‰ÌÝ•É‘•¸­•¥¹”Y•Éé•¥¡¹¥ÍÍ”…¹•±•Ð¸ˆ°(€€€€€€€€€€€€€€€‘…Ñ…}ÍÑ…Ñ”ô‰•È…Ñ•¹ÍÑ…¹¥ÍÐÕ¹Ù•Ë‘¹‘•ÉÐ¸ˆ°(€€€€€€€€€€€€€€€Í½±ÕÑ¥½¸ô‰Måµ±¥¹­Ì°A™…‘É•¹é•¸°…Ñ•¥ÑåÁ•¸½‘•ÈI•¡Ñ”­½ÉÉ¥¥•É•¸¸ˆ°(€€€€€€€€€€€€€€€¹•áÑ}ÍÑ•Àô‰•¸A™…‘Á±…¸•É¹•ÕÐÉ•¥¸±•Í•¹ÁËñ™•¸¸ˆ°(€€€€€€€€€€€€¤°(€€€€€€€€€€€€Ô°(€€€€€€€€¤((€€€¥˜…ÉÌ¹Ù…±¥‘…Ñ•}½¹±ä½È…ÉÌ¹Í•ÑÑ¥¹Í}½¹±äè(€€€€€€€Á…Ñ¡}É•ÍÕ±Ð€ôÙ…±¥‘…Ñ•}á‘}Á…Ñ¡Ì¡É•Í½±Ù•¹Á…Ñ¡Ì°ÁÉ½©•Ñ}É½½ÐõAI=)Q}I==P¤(€€€€€€€ÁÉ¥¹Ð¡™½Éµ…Ñ}Á…Ñ¡}É•Á½ÉÐ¡Á…Ñ¡}É•ÍÕ±Ð°¥¹±Õ‘•}Á…Ñ¡Ìõ…±Í”°ÁÉ•Á…É•õ…±Í”¤¤(€€€€€€€¥˜¹½ÐÁ…Ñ¡}É•ÍÕ±Ð¹¥Í}Ù…±¥è(€€€€€€€€€€€É•ÑÕÉ¸}ÁÉ¥¹Ñ}‰±½­¥¹}•Ù•¹Ð (€€€€€€€€€€€€€€€•Ù•¹Ñ}™É½µ}µ•ÍÍ…•Ì (€€€€€€€€€€€€€€€€€€€Á…Ñ¡}É•ÍÕ±Ð¹•ÉÉ½ÉÌ°(€€€€€€€€€€€€€€€€€€€…Ñ•½Éäô‰á‘œµÙ…±¥‘…Ñ¥½¸ˆ°(€€€€€€€€€€€€€€€€€€€…ÕÍ•}ÁÉ•™¥àô‰•ÈaµA™…‘Á±…¸¥ÍÐÕ¹Ÿñ±Ñ¥œ¸ˆ°(€€€€€€€€€€€€€€€€€€€½¹Í•ÅÕ•¹”ô‰¥”¥¹ÍÑ•±±Õ¹ÍÁËñ™Õ¹œÝ¥É¹¥¡Ð™½ÉÑ•Í•ÑéÐ¸ˆ°(€€€€€€€€€€€€€€€€€€€‘…Ñ…}ÍÑ…Ñ”ô‰•È1•Í•µ½‘ÕÌ¡…Ð­•¥¹”…Ñ•¥•¸…¹•±•Ð½‘•ÈÙ•Ë‘¹‘•ÉÐ¸ˆ°(€€€€€€€€€€€€€€€€€€€Í½±ÕÑ¥½¸ô‰¥”•¹…¹¹Ñ•¸aµUÉÍ…¡•¸­½ÉÉ¥¥•É•¸¸ˆ°(€€€€€€€€€€€€€€€€€€€¹•áÑ}ÍÑ•Àôˆ´µÁ…Ñ¡Ìµ½¹±ä…ÕÍ›ñ¡É•¸Õ¹•ÉÍÐ‰•¤Ëñ¹•´É•‰¹¥Ì™½ÉÑÍ•Ñé•¸¸ˆ°(€€€€€€€€€€€€€€€€¤°(€€€€€€€€€€€€€€€€Ô°(€€€€€€€€€€€€¤(€€€€€€€Í•ÑÑ¥¹Í}É•ÍÕ±Ð€ô¥¹ÍÁ•Ñ}Í•ÑÑ¥¹Ì¡É•Í½±Ù•¹Á…Ñ¡Ì¹½¹™¥œ¤(€€€€€€€ÁÉ¥¹Ð¡™½Éµ…Ñ}Í•ÑÑ¥¹Í}É•Á½ÉÐ¡Í•ÑÑ¥¹Í}É•ÍÕ±Ð¤¤(€€€€€€€¥˜Í•ÑÑ¥¹Í}É•ÍÕ±Ð¹¥Í}Ù…±¥è(€€€€€€€€€€€¥˜Í•ÑÑ¥¹Í}É•ÍÕ±Ð¹É•½Ù•É•è(€€€€€€€€€€€€€€€ÁÉ¥¹Ð¡™½Éµ…Ñ}•Ù•¹Ñ}™½É}ÕÍ•È¡•Ù•¹Ñ}™É½µ}Í•ÑÑ¥¹Í}É•ÍÕ±Ð¡Í•ÑÑ¥¹Í}É•ÍÕ±Ð¤¤¤(€€€€€€€€€€€É•ÑÕÉ¸€À(€€€€€€€É•ÑÕÉ¸}ÁÉ¥¹Ñ}‰±½­¥¹}•Ù•¹Ð¡•Ù•¹Ñ}™É½µ}Í•ÑÑ¥¹Í}É•ÍÕ±Ð¡Í•ÑÑ¥¹Í}É•ÍÕ±Ð¤°€Ø¤((€€€Á…Ñ¡}É•ÍÕ±Ð€ô•¹ÍÕÉ•}á‘}Á…Ñ¡Ì¡É•Í½±Ù•¹Á…Ñ¡Ì°ÁÉ½©•Ñ}É½½ÐõAI=)Q}I==P¤(€€€Á…Ñ¡}Ñ•áÐ€ô™½Éµ…Ñ}Á…Ñ¡}É•Á½ÉÐ¡Á…Ñ¡}É•ÍÕ±Ð°¥¹±Õ‘•}Á…Ñ¡Ìõ…±Í”°ÁÉ•Á…É•õQÉÕ”¤(€€€ÁÉ¥¹Ð¡Á…Ñ¡}Ñ•áÐ¤(€€€¥˜¹½ÐÁ…Ñ¡}É•ÍÕ±Ð¹¥Í}Ù…±¥½ÈÁ…Ñ¡}É•ÍÕ±Ð¹Á…Ñ¡Ì¥Ì9½¹”è(€€€€€€€É•ÑÕÉ¸}ÁÉ¥¹Ñ}‰±½­¥¹}•Ù•¹Ð (€€€€€€€€€€€•Ù•¹Ñ}™É½µ}µ•ÍÍ…•Ì (€€€€€€€€€€€€€€€Á…Ñ¡}É•ÍÕ±Ð¹•ÉÉ½ÉÌ°(€€€€€€€€€€€€€€€…Ñ•½Éäô‰á‘œµÁÉ•Á…É”ˆ°(€€€€€€€€€€€€€€€…ÕÍ•}ÁÉ•™¥àô‰¥”ÁÉ¥Ù…Ñ•¸aµY•Éé•¥¡¹¥ÍÍ”­½¹¹Ñ•¸¹¥¡ÐÍ¥¡•ÈÙ½É‰•É•¥Ñ•ÐÝ•É‘•¸¸ˆ°(€€€€€€€€€€€€€€€½¹Í•ÅÕ•¹”ô‰¥¹ÍÑ•±±Õ¹•¸Õ¹=‰•É™³‘¡”‰±•¥‰•¸•ÍÁ•ÉÉÐ¸ˆ°(€€€€€€€€€€€€€€€‘…Ñ…}ÍÑ…Ñ”ô‰Q•µÁ½Ë‘É”M¡É•¥‰ÁÉ½‰•¸ÝÕÉ‘•¸•¹Ñ™•É¹ÐìÁÉ½‘Õ­Ñ¥Ù”9ÕÑé•É‘…Ñ•¸‰±¥•‰•¸Õ¹Ù•Ë‘¹‘•ÉÐ¸ˆ°(€€€€€€€€€€€€€€€Í½±ÕÑ¥½¸ô‰I•¡Ñ”°Måµ±¥¹­Ì°5½Õ¹ÑéÕÍÑ…¹Õ¹™É•¥•¸MÁ•¥¡•ÈÁËñ™•¸¸ˆ°(€€€€€€€€€€€€€€€¹•áÑ}ÍÑ•Àô‰9… ‘•È-½ÉÉ•­ÑÕÈ€´µÙ…±¥‘…Ñ”µ½¹±ä…ÕÍ›ñ¡É•¸¸ˆ°(€€€€€€€€€€€€¤°(€€€€€€€€€€€€Ô°(€€€€€€€€¤((€€€©½ÕÉ¹…°€ôÙ•¹Ñ)½ÕÉ¹…°¡Á…Ñ¡}É•ÍÕ±Ð¹Á…Ñ¡Ì¹±½Ì¤(€€€©½ÕÉ¹…±}•ÉÉ½ÉÌ€ô©½ÕÉ¹…°¹Ù…±¥‘…Ñ” ¤(€€€¥˜©½ÕÉ¹…±}•ÉÉ½ÉÌè(€€€€€€€É•ÑÕÉ¸}ÁÉ¥¹Ñ}‰±½­¥¹}•Ù•¹Ð (€€€€€€€€€€€•Ù•¹Ñ}™É½µ}µ•ÍÍ…•Ì (€€€€€€€€€€€€€€€©½ÕÉ¹…±}•ÉÉ½ÉÌ°(€€€€€€€€€€€€€€€…Ñ•½Éäô‰•Ù•¹Ðµ©½ÕÉ¹…°ˆ°(€€€€€€€€€€€€€€€…ÕÍ•}ÁÉ•™¥àô‰…Ìé•¹ÑÉ…±”É•¥¹¥Í©½ÕÉ¹…°¥ÍÐ¹¥¡ÐÍ¥¡•È¹ÕÑé‰…È¸ˆ°(€€€€€€€€€€€€€€€½¹Í•ÅÕ•¹”ô‰¥”¹Ý•¹‘Õ¹œÍÑ…ÉÑ•Ð½¡¹”Ù•É³‘ÍÍ±¥¡”•¡±•ÉÁÉ½Ñ½­½±±¥•ÉÕ¹œ¹¥¡Ð¸ˆ°(€€€€€€€€€€€€€€€‘…Ñ…}ÍÑ…Ñ”ô‰¥¹ÍÑ•±±Õ¹•¸Õ¹9ÕÑé•É‘…Ñ•¸ÝÕÉ‘•¸¹¥¡ÐÙ•Ë‘¹‘•ÉÐ¸ˆ°(€€€€€€€€€€€€€€€Í½±ÕÑ¥½¸ô‰aµ1½Á™…°Måµ±¥¹­Ì°…Ñ•¥ÑåÀÕ¹I•¡Ñ”€ÀØÀÀ­½ÉÉ¥¥•É•¸¸ˆ°(€€€€€€€€€€€€€€€¹•áÑ}ÍÑ•Àô‰1½Á™…ÁËñ™•¸Õ¹‘…¹… €¸½ÍÑ…ÉÐ¹Í •É¹•ÕÐ…ÕÍ›ñ¡É•¸¸ˆ°(€€€€€€€€€€€€¤°(€€€€€€€€€€€€Ü°(€€€€€€€€¤(€€€•Ù•¹Ñ}•¹Ñ•È€ôÉÉ½ÉÙ•¹Ñ•¹Ñ•È¡©½ÕÉ¹…°¤((€€€Í•ÑÑ¥¹Í}É•ÍÕ±Ð€ô±½…‘}½É}É•½Ù•É}Í•ÑÑ¥¹Ì¡Á…Ñ¡}É•ÍÕ±Ð¹Á…Ñ¡Ì¹½¹™¥œ¤(€€€Í•ÑÑ¥¹Í}Ñ•áÐ€ô™½Éµ…Ñ}Í•ÑÑ¥¹Í}É•Á½ÉÐ¡Í•ÑÑ¥¹Í}É•ÍÕ±Ð¤(€€€ÁÉ¥¹Ð¡Í•ÑÑ¥¹Í}Ñ•áÐ¤(€€€¥˜Í•ÑÑ¥¹Í}É•ÍÕ±Ð¹É•½Ù•É•è(€€€€€€€•Ù•¹Ñ}•¹Ñ•È¹…ÁÑÕÉ”¡•Ù•¹Ñ}™É½µ}Í•ÑÑ¥¹Í}É•ÍÕ±Ð¡Í•ÑÑ¥¹Í}É•ÍÕ±Ð¤¤(€€€¥˜¹½ÐÍ•ÑÑ¥¹Í}É•ÍÕ±Ð¹¥Í}Ù…±¥è(€€€€€€€•Ù•¹Ð€ô•Ù•¹Ñ}•¹Ñ•È¹…ÁÑÕÉ”¡•Ù•¹Ñ}™É½µ}Í•ÑÑ¥¹Í}É•ÍÕ±Ð¡Í•ÑÑ¥¹Í}É•ÍÕ±Ð¤¤(€€€€€€€É•ÑÕÉ¸}ÁÉ¥¹Ñ}‰±½­¥¹}•Ù•¹Ð¡•Ù•¹Ð°€Ø¤((€€€É•ÑÕÉ¸ÉÕ¹}Õ¤ (€€€€€€€µ…¹¥™•ÍÑ}Ñ•áÐ°(€€€€€€€Á…Ñ¡}Ñ•áÐ°(€€€€€€€Í•ÑÑ¥¹Í}Ñ•áÐ°(€€€€€€€Á…Ñ¡}É•ÍÕ±Ð¹Á…Ñ¡Ì°(€€€€€€€Í•ÑÑ¥¹Í}É•ÍÕ±Ð°(€€€€€€€•Ù•¹Ñ}•¹Ñ•È°(€€€€¤(()‘•˜±¥}•¹ÑÉåÁ½¥¹Ð¡…ÉØè±¥ÍÑmÍÑÉtð9½¹”€ô9½¹”¤€´ø¥¹Ðè(€€€€ˆˆ‰1•ÑéÑ”M¡ÕÑéÍ¡¥¡Ð›ñÈÕ¹•ÉÝ…ÉÑ•Ñ”	½½ÑÍÑÉ…ÀµÕÍ¹…¡µ•¸¸ˆˆˆ((€€€ÑÉäè(€€€€€€€É•ÑÕÉ¸µ…¥¸¡…ÉØ¤(€€€•á•ÁÐ-•å‰½…É‘%¹Ñ•ÉÉÕÁÐè(€€€€€€€•Ù•¹Ð€ôÉ•…Ñ•}•Ù•¹Ð (€€€€€€€€€€€…Ñ•½Éäô‰ÕÍ•Èµ¥¹Ñ•ÉÉÕÁÐˆ°(€€€€€€€€€€€Í•Ù•É¥Ñäô‰Ý…É¹¥¹œˆ°(€€€€€€€€€€€…ÕÍ”ô‰•ÈMÑ…ÉÐÝÕÉ‘”‘ÕÉ ‘•¸9ÕÑé•ÈÕ¹Ñ•É‰É½¡•¸¸ˆ°(€€€€€€€€€€€½¹Í•ÅÕ•¹”ô‰•È…­ÑÕ•±±”MÑ…ÉÑÍ¡É¥ÑÐÝÕÉ‘”‰••¹‘•Ð¸ˆ°(€€€€€€€€€€€‘…Ñ…}ÍÑ…Ñ”ô‰	•É•¥ÑÌ‰•ÍÓ‘Ñ¥Ñ”…Ñ•¥•¸‰±•¥‰•¸Ù½±±ÍÓ‘¹‘¥œì­•¥¹”Ý•¥Ñ•É”­Ñ¥½¸ÝÕÉ‘”•ÍÑ…ÉÑ•Ð¸ˆ°(€€€€€€€€€€€Í½±ÕÑ¥½¸ô‰Y½È•¥¹•´9•ÕÍÑ…ÉÐÁËñ™•¸°½ˆ•¥¸M•ÑÕÀ´½‘•ÈM¡É•¥‰Ù½É…¹œ¹½ ³‘Õ™Ð¸ˆ°(€€€€€€€€€€€¹•áÑ}ÍÑ•Àô‰9… ‰Í¡±ÕÍÌ…±±•ÈAÉ½é•ÍÍ”€¸½ÍÑ…ÉÐ¹Í •É¹•ÕÐ…ÕÍ›ñ¡É•¸¸ˆ°(€€€€€€€€¤(€€€€€€€É•ÑÕÉ¸}ÁÉ¥¹Ñ}‰±½­¥¹}•Ù•¹Ð¡•Ù•¹Ð°€ÄÌÀ¤(€€€•á•ÁÐ	…Í•á•ÁÑ¥½¸…Ì•áŒè(€€€€€€€•Ù•¹Ð€ô•Ù•¹Ñ}™É½µ}•á•ÁÑ¥½¸ (€€€€€€€€€€€•áŒ°(€€€€€€€€€€€…Ñ•½Éäô‰‰½½ÑÍÑÉ…Àµ•á•ÁÑ¥½¸ˆ°(€€€€€€€€€€€½¹Ñ•áÐô‰¥¹”Õ¹•ÉÝ…ÉÑ•Ñ”ÕÍ¹…¡µ”ß‘¡É•¹‘•ÌAÉ½É…µµÍÑ…ÉÑÌÝÕÉ‘”…‰•™…¹•¸¸ˆ°(€€€€€€€€€€€‘…Ñ…}ÍÑ…Ñ”ô‰•ÈMÑ…ÉÐÝÕÉ‘”­½¹ÑÉ½±±¥•ÉÐ‰••¹‘•ÐìÁÉ½‘Õ­Ñ¥Ù”…Ñ•¥…­Ñ¥½¹•¸Ý…É•¸¹½ •ÍÁ•ÉÉÐ¸ˆ°(€€€€€€€€¤(€€€€€€€É•ÑÕÉ¸}ÁÉ¥¹Ñ}‰±½­¥¹}•Ù•¹Ð¡•Ù•¹Ð°€ÜÀ¤(()¥˜}}¹…µ•}|€ôô€‰}}µ…¥¹}|ˆè(€€€É…¥Í”MåÍÑ•µá¥Ð¡±¥}•¹ÑÉåÁ½¥¹Ð ¤¤(