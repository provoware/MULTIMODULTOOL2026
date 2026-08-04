"""Read-only Qt panel for the project trash safety contract.

PySide6 is injected by the caller so the module remains importable without GUI
dependencies. The panel exposes no delete, empty-trash, upload or execute action.
"""

from __future__ import annotations


def build_trash_contract_panel(QtWidgets):
    panel = QtWidgets.QFrame()
    panel.setObjectName("trashContractPanel")
    layout = QtWidgets.QVBoxLayout(panel)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(8)

    title = QtWidgets.QLabel("Projektpapierkorb – Sicherheitsvertrag")
    title.setObjectName("sectionTitle")
    title.setWordWrap(True)
    layout.addWidget(title)

    description = QtWidgets.QLabel(
        "Destruktive Dateiaktionen dürfen reguläre Dateien und Verzeichnisse nur "
        "innerhalb desselben Dateisystems atomar in einen wiederherstellbaren "
        "Projektpapierkorb verschieben."
    )
    description.setWordWrap(True)
    layout.addWidget(description)

    rules = QtWidgets.QLabel(
        "✓ unveränderliche Vorschau und Quellfingerabdruck\n"
        "✓ eindeutige Transaktions-ID und privates Manifest\n"
        "✓ Projektordner 0700, Manifest 0600\n"
        "✓ os.replace statt Kopieren-und-Löschen\n"
        "✓ Mountwechsel, Symlinks, Hardlinks und Konflikte blockiert\n"
        "✓ Wiederherstellung nur bei unverändertem Payload\n"
        "✗ keine dauerhafte Löschung"
    )
    rules.setObjectName("trashContractRules")
    rules.setWordWrap(True)
    layout.addWidget(rules)

    status = QtWidgets.QFrame()
    status.setObjectName("trashStatusPanel")
    status_layout = QtWidgets.QVBoxLayout(status)
    status_layout.setContentsMargins(10, 8, 10, 8)
    status_label = QtWidgets.QLabel(
        "Kernvertrag geprüft. Produktive Auswahl und Ausführung bleiben bis zum "
        "geführten Projektworkflow gesperrt."
    )
    status_label.setObjectName("trashContractStatus")
    status_label.setProperty("safetyStatus", True)
    status_label.setWordWrap(True)
    status_layout.addWidget(status_label)
    layout.addWidget(status)

    preview_button = QtWidgets.QPushButton("Nur Vertragsvorschau")
    preview_button.setObjectName("trashPreviewOnlyButton")
    preview_button.setToolTip("Zeigt ausschließlich den Sicherheitsvertrag; führt keine Dateiaktion aus.")
    layout.addWidget(preview_button)
    return panel
