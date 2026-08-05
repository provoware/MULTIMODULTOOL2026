"""Contextual, read-only help dialog for the guarded Linux workflow."""

from __future__ import annotations

HELP_SECTIONS: tuple[tuple[str, str], ...] = (
    (
        "Sicherer Einstieg",
        "Start zeigt ausschließlich bereits geprüfte Schutzfunktionen. Produktive Dateiaktionen "
        "bleiben deaktiviert, bis Projektordner, Rechte, Mountgrenzen und Speicherplatz über den "
        "geführten Auswahlworkflow validiert werden können.",
    ),
    (
        "Verlauf und Wiederanlauf",
        "Zeigt Papierkorbtransaktionen, Undo/Redo-Zustände, Laufpläne und Checkpoints rein lesend. "
        "Nichts wird automatisch repariert, gelöscht oder fortgesetzt. Bei einem Widerspruch bleibt "
        "der Datenstand unverändert blockiert.",
    ),
    (
        "Diagnose",
        "Zeigt lokal gespeicherte und bereinigte Ereignisse. Nach Schweregrad oder Diagnosekennung "
        "filtern und genau einen sicheren Bericht kopieren. Es gibt keinen Upload, keine Löschung und "
        "keinen automatischen Export.",
    ),
    (
        "Gesperrte Bereiche",
        "Analysieren, Duplikate, Organisieren, Umbenennen und Berichte sind sichtbar, aber absichtlich "
        "gesperrt. Der jeweilige Tooltip nennt die fehlende Freigabe. Eine Sperre darf nicht manuell "
        "umgangen werden.",
    ),
    (
        "Abbruch und Fortsetzung",
        "Ein Abbruch wird nur vor einem neuen Intent oder nach einem vollständig bestätigten Schritt "
        "übernommen. Nach einem Neustart werden Checkpoint, Journal, Manifest, Originalpfad und Payload "
        "gemeinsam geprüft, damit keine Dateioperation doppelt ausgeführt wird.",
    ),
    (
        "Release-Dateien",
        "Erst nach grünen Kubuntu-22.04- und Kubuntu-24.04-Lebenszyklen werden die geprüften "
        "Ausgabedateien mit dem Zusatz _save_ erzeugt. Quelldateien behalten ihre normalen Namen, "
        "damit Imports, Startpfade und Manifeste stabil bleiben.",
    ),
)


def build_help_dialog(QtWidgets, parent=None):
    """Build a non-destructive help dialog without reading or writing user data."""

    dialog = QtWidgets.QDialog(parent)
    dialog.setObjectName("helpDialog")
    dialog.setWindowTitle("MULTIMODULTOOL2026 – Hilfe und Sicherheitsgrenzen")
    dialog.resize(760, 620)
    dialog.setMinimumSize(620, 480)
    dialog.setModal(False)

    outer = QtWidgets.QVBoxLayout(dialog)
    title = QtWidgets.QLabel("Hilfe, Status und sichere nächste Schritte")
    title.setObjectName("helpDialogTitle")
    title.setWordWrap(True)
    outer.addWidget(title)

    intro = QtWidgets.QLabel(
        "Diese Hilfe erklärt nur freigegebene Funktionen und bewusst gesperrte Grenzen. "
        "Sie verändert keine Einstellungen, Journale, Checkpoints, Manifeste oder Nutzerdaten."
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
