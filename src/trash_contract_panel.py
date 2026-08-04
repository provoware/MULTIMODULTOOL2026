"""Read-only Qt panels for trash, transaction history and long-run recovery.

PySide6 is injected by the caller so the module remains importable without GUI
dependencies. No restore, repair, delete, empty-trash, run, cancel, upload or
export action is exposed here.
"""

from __future__ import annotations


def build_trash_contract_panel(QtWidgets, transaction_snapshot=None):
    from .transaction_overview import TransactionSnapshot

    snapshot = transaction_snapshot or TransactionSnapshot(())

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
        "✓ append-only Undo-/Redo-Journal mit Hashkette\n"
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
    preview_button.setToolTip(
        "Zeigt ausschließlich den Sicherheitsvertrag; führt keine Dateiaktion aus."
    )
    layout.addWidget(preview_button)

    overview = QtWidgets.QFrame()
    overview.setObjectName("transactionOverview")
    overview_layout = QtWidgets.QVBoxLayout(overview)
    overview_layout.setContentsMargins(10, 10, 10, 10)
    overview_title = QtWidgets.QLabel("Transaktionsübersicht – ausschließlich lesend")
    overview_title.setObjectName("sectionTitle")
    overview_title.setWordWrap(True)
    overview_layout.addWidget(overview_title)

    filter_row = QtWidgets.QHBoxLayout()
    filter_label = QtWidgets.QLabel("Zustand:")
    state_filter = QtWidgets.QComboBox()
    state_filter.setObjectName("transactionStateFilter")
    state_filter.addItem("Alle", "all")
    state_filter.addItem("Vorbereitet", "prepared")
    state_filter.addItem("Im Papierkorb", "trashed")
    state_filter.addItem("Wiederhergestellt", "restored")
    state_filter.addItem("Beschädigt", "damaged")
    filter_row.addWidget(filter_label)
    filter_row.addWidget(state_filter, 1)
    overview_layout.addLayout(filter_row)

    listing = QtWidgets.QListWidget()
    listing.setObjectName("transactionList")
    listing.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
    overview_layout.addWidget(listing)

    detail = QtWidgets.QPlainTextEdit()
    detail.setObjectName("transactionDetail")
    detail.setReadOnly(True)
    detail.setPlaceholderText(
        "Keine Transaktion ausgewählt. Die Ansicht verändert keine Manifeste."
    )
    overview_layout.addWidget(detail)

    notice = QtWidgets.QLabel(
        "Kein Wiederherstellen · kein Reparieren · kein Löschen · kein Upload · kein Export"
    )
    notice.setObjectName("transactionReadOnlyNotice")
    notice.setProperty("safetyStatus", True)
    notice.setWordWrap(True)
    overview_layout.addWidget(notice)
    layout.addWidget(overview)

    run_contract = QtWidgets.QFrame()
    run_contract.setObjectName("runControlContract")
    run_layout = QtWidgets.QVBoxLayout(run_contract)
    run_layout.setContentsMargins(10, 10, 10, 10)
    run_title = QtWidgets.QLabel("Abbruch und Wiederanlauf – Vertragsansicht")
    run_title.setObjectName("sectionTitle")
    run_title.setWordWrap(True)
    run_layout.addWidget(run_title)
    run_rules = QtWidgets.QLabel(
        "✓ eindeutige MMTRUN-Lauf-ID\n"
        "✓ unveränderlicher Plan und atomarer Checkpoint\n"
        "✓ private Laufordner 0700, Laufdateien 0600\n"
        "✓ Abbruch nur vor Intent oder nach vollständig bestätigtem Schritt\n"
        "✓ idempotenter Neustart aus Checkpoint, Journal und Manifest\n"
        "✓ SIGKILL-Matrix vor/nach Intent, Dateioperation, fsync, Manifest und Journal\n"
        "✗ keine Doppeloperation und kein stiller Zwischenzustand"
    )
    run_rules.setObjectName("runControlRules")
    run_rules.setWordWrap(True)
    run_layout.addWidget(run_rules)
    run_status = QtWidgets.QLabel(
        "Laufsteuerung geprüft. Diese Ansicht startet, stoppt oder repariert keinen Lauf."
    )
    run_status.setObjectName("runControlReadOnlyNotice")
    run_status.setProperty("safetyStatus", True)
    run_status.setWordWrap(True)
    run_layout.addWidget(run_status)
    layout.addWidget(run_contract)

    def populate() -> None:
        listing.clear()
        state = str(state_filter.currentData() or "all")
        entries = snapshot.filtered(state)
        for entry in entries:
            item = QtWidgets.QListWidgetItem(
                f"{entry.state.upper()} · {entry.transaction_id}"
            )
            item.setData(256, entry)
            listing.addItem(item)
        if listing.count():
            listing.setCurrentRow(0)
        else:
            detail.setPlainText(
                "Keine passenden Transaktionen vorhanden. "
                "Die Übersicht hat keine Datei oder kein Manifest verändert."
            )

    def show_selected() -> None:
        item = listing.currentItem()
        if item is None:
            return
        entry = item.data(256)
        detail.setPlainText(
            "\n".join(
                (
                    f"Transaktions-ID: {entry.transaction_id}",
                    f"Zustand: {entry.state}",
                    f"Erstellt: {entry.created_utc or 'nicht lesbar'}",
                    f"Originalpfad: {entry.original_relative_path or 'nicht lesbar'}",
                    f"Hinweis: {entry.detail or 'Manifest gültig; nur Anzeige.'}",
                )
            )
        )

    state_filter.currentIndexChanged.connect(populate)
    listing.currentItemChanged.connect(lambda *_args: show_selected())
    populate()
    return panel
