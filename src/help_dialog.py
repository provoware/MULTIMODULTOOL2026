"""Contextual, read-only help for productive and signed Linux workflows."""

from __future__ import annotations

from .start_assistant_integration import install_guided_productive_ui

HELP_SECTIONS: tuple[tuple[str, str], ...] = (
    (
        "Sicherer Einstieg – Startassistent",
        "Der Startassistent führt nacheinander durch Projektordner, getrennten Zielordner und "
        "Sicherheitsmodus. Beide Ordner werden ausschließlich über Auswahldialoge gewählt. Die "
        "Übernahme bleibt gesperrt, bis Eigentümer, Rechte, Symlink-Komponenten, Mountgrenzen, "
        "Dateisystem, Speicher und die verständliche Zusammenfassung vollständig geprüft sind.",
    ),
    (
        "Sicherheitsmodi",
        "Nur prüfen sperrt Berichte und Dateiänderungen. Vorschau und Bericht erlaubt private "
        "JSON-/Markdown-Berichte, aber keine Dateiänderung. Produktiv mit Bestätigung erlaubt "
        "Änderungen erst nach Startfreigabe, vollständiger Vorher-/Nachher-Vorschau und einer "
        "zweiten ausdrücklichen Bestätigung.",
    ),
    (
        "Dateibestand analysieren",
        "Die Analyse liest Typ, Größe, Änderungszeit, Dateiendung, Kategorie und Namenshinweise. "
        "Symlinks werden sichtbar als ausgeschlossen gemeldet, nicht verfolgt. Mountgrenzen, interne "
        "Steuerdaten und nicht reguläre Dateien werden nicht produktiv verarbeitet.",
    ),
    (
        "Duplikate per SHA-256",
        "Nur reguläre Dateien gleicher Größe werden streamend gehasht. Vor und nach dem Hashen wird "
        "der Dateifingerabdruck geprüft. Die Suche ist rein lesend: Sie löscht, verschiebt oder ersetzt nichts.",
    ),
    (
        "Organisieren und Massenumbenennen",
        "Der bestätigte Zielordner gilt für die Organisation. Massenumbenennung bleibt am jeweiligen "
        "Ursprungsort. Zuerst entsteht immer eine vollständige Vorher-/Nachher-Liste mit Planhash. "
        "Doppelte Ziele, belegte Namen, Rename-Zyklen, Hardlinks, Symlinks und Dateisystemwechsel "
        "blockieren den gesamten Plan.",
    ),
    (
        "Abbruch und Fortsetzung – Checkpoint und Rückgängig",
        "Jeder bestätigte Schritt wird in einem privaten Operationsordner protokolliert. Nach einer Unterbrechung "
        "werden Quelle, Ziel und Fingerabdruck mit dem unveränderlichen Plan abgeglichen. Rückgängig arbeitet "
        "rückwärts und nur bei unveränderten Zieldateien sowie freien Originalpfaden.",
    ),
    (
        "Berichte",
        "Analyse- und Operationsberichte werden als JSON und Markdown im privaten Projektsteuerordner gespeichert. "
        "Sie enthalten ausschließlich projekt-relative Pfade und keinen automatischen Upload. Im Modus Nur prüfen "
        "bleibt auch dieser Schreibzugriff gesperrt.",
    ),
    (
        "Release-Dateien und kryptografische Signaturen",
        "Nach grüner Kubuntu-Matrix werden die _save_-Dateien mit Sigstore keyless OIDC signiert. Jede Datei erhält "
        "ein JSON-Bundle; zusätzlich wird ein SHA-256-Releasemanifest erstellt und selbst signiert. Die Prüfung bindet "
        "Workflowidentität und OIDC-Aussteller. Im Repository liegt kein langlebiger privater Schlüssel.",
    ),
    (
        "Gesperrte Bereiche und bewusste Grenzen",
        "Die kachelbasierte Navigation mit vollständig geprüftem Aktivzustand und Zurück-Pfad, grafische Einstellungen, "
        "vollständige KDE-Tastaturabnahme, Zoom 80–200 Prozent, weitere Themes, Journalrotation, Datenmigration, "
        "Plugin-Sandbox und physische X11-/Wayland-Abnahme bleiben getrennte Aufgaben.",
    ),
)


def build_help_dialog(QtWidgets, parent=None):
    """Build help and attach the guided local-only productive UI without touching project data."""

    if parent is not None:
        install_guided_productive_ui(QtWidgets, parent)

    dialog = QtWidgets.QDialog(parent)
    dialog.setObjectName("helpDialog")
    dialog.setWindowTitle("MULTIMODULTOOL2026 – Hilfe und Sicherheitsgrenzen")
    dialog.resize(800, 680)
    dialog.setMinimumSize(620, 480)
    dialog.setModal(False)

    outer = QtWidgets.QVBoxLayout(dialog)
    title = QtWidgets.QLabel("Hilfe, geführter Start und sichere nächste Schritte")
    title.setObjectName("helpDialogTitle")
    title.setWordWrap(True)
    outer.addWidget(title)

    intro = QtWidgets.QLabel(
        "Diese Hilfe erklärt den vollständig vorvalidierten Start sowie die freigegebenen lokalen "
        "Dateiworkflows und ihre harten Blocker. Sie verändert keine Einstellungen, Projektdateien, "
        "Journale, Checkpoints oder Signaturen."
    )
    intro.setObjectName("helpDialogIntro")
    intro.setWordWrap(True)
    outer.addWidget(intro)

    scroll = QtWidgets.QScrollArea()
    scroll.setObjectName("helpDialogScroll")
    scroll.setWidgetResizable(True)
    body = QtWidgets.QWidget()
    body_layout = QtWidgets.QVBoxLayout(body)
    for index, (heading, text) in enumerate(HELP_SECTIONS, start=1):
        frame = QtWidgets.QFrame()
        frame.setObjectName("helpTopic")
        frame.setProperty("helpTopicIndex", index)
        layout = QtWidgets.QVBoxLayout(frame)
        heading_label = QtWidgets.QLabel(f"{index}. {heading}")
        heading_label.setObjectName("helpTopicTitle")
        heading_label.setWordWrap(True)
        body_label = QtWidgets.QLabel(text)
        body_label.setObjectName("helpTopicBody")
        body_label.setWordWrap(True)
        layout.addWidget(heading_label)
        layout.addWidget(body_label)
        body_layout.addWidget(frame)
    body_layout.addStretch(1)
    scroll.setWidget(body)
    outer.addWidget(scroll, 1)

    close_button = QtWidgets.QPushButton("Hilfe schließen")
    close_button.setObjectName("helpDialogCloseButton")
    close_button.setMinimumHeight(44)
    close_button.setToolTip("Schließt nur dieses Hilfefenster. Es werden keine Daten verändert.")
    close_button.clicked.connect(dialog.close)
    outer.addWidget(close_button)
    return dialog
