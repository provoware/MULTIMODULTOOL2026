"""Qt-Offscreen-Prüfung für Papierkorb- und Transaktionsübersicht."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6 import QtWidgets
except ImportError:  # CI installiert PySide6 ausdrücklich.
    QtWidgets = None


@unittest.skipUnless(QtWidgets is not None, "PySide6 ist für den GUI-Test erforderlich.")
class TrashContractGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from src.transaction_overview import TransactionEntry, TransactionSnapshot
        from src.trash_contract_panel import build_trash_contract_panel

        snapshot = TransactionSnapshot(
            (
                TransactionEntry(
                    "MMTTRASH-20260804T164200-ABCDEF123456",
                    "prepared",
                    "2026-08-04T16:42:00Z",
                    "daten/a.txt",
                ),
                TransactionEntry(
                    "MMTTRASH-20260804T164201-ABCDEF123457",
                    "trashed",
                    "2026-08-04T16:42:01Z",
                    "daten/b.txt",
                ),
                TransactionEntry(
                    "MMTTRASH-20260804T164202-ABCDEF123458",
                    "restored",
                    "2026-08-04T16:42:02Z",
                    "daten/c.txt",
                ),
                TransactionEntry(
                    "MMTTRASH-20260804T164203-ABCDEF123459",
                    "damaged",
                    "",
                    "",
                    "Manifest beschädigt",
                ),
            )
        )
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        cls.panel = build_trash_contract_panel(QtWidgets, snapshot)
        cls.panel.show()
        cls.app.processEvents()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.panel.close()
        cls.app.processEvents()

    def test_contract_is_visible_and_destructive_actions_are_absent(self) -> None:
        contract = self.panel.findChild(QtWidgets.QFrame, "trashContractPanel")
        status = self.panel.findChild(QtWidgets.QFrame, "trashStatusPanel")
        preview = self.panel.findChild(QtWidgets.QPushButton, "trashPreviewOnlyButton")
        self.assertIsNotNone(contract)
        self.assertTrue(contract.isVisible())
        self.assertTrue(status.isVisible())
        self.assertTrue(preview.isEnabled())
        all_text = "\n".join(
            widget.text() for widget in self.panel.findChildren(QtWidgets.QAbstractButton)
        ).lower()
        self.assertNotIn("dauerhaft löschen", all_text)
        for forbidden in (
            "permanentDeleteButton",
            "trashDeleteButton",
            "emptyTrashButton",
            "transactionRestoreButton",
            "transactionRepairButton",
            "transactionDeleteButton",
            "transactionUploadButton",
            "transactionExportButton",
        ):
            self.assertIsNone(self.panel.findChild(QtWidgets.QPushButton, forbidden))

    def test_transaction_overview_is_read_only_and_filterable(self) -> None:
        overview = self.panel.findChild(QtWidgets.QFrame, "transactionOverview")
        state_filter = self.panel.findChild(QtWidgets.QComboBox, "transactionStateFilter")
        listing = self.panel.findChild(QtWidgets.QListWidget, "transactionList")
        detail = self.panel.findChild(QtWidgets.QPlainTextEdit, "transactionDetail")
        notice = self.panel.findChild(QtWidgets.QLabel, "transactionReadOnlyNotice")
        self.assertTrue(overview.isVisible())
        self.assertEqual(5, state_filter.count())
        self.assertEqual(4, listing.count())
        self.assertTrue(detail.isReadOnly())
        self.assertTrue(notice.isVisible())
        state_filter.setCurrentIndex(4)
        self.app.processEvents()
        self.assertEqual(1, listing.count())
        self.assertIn("DAMAGED", listing.item(0).text())

    def test_panel_exposes_only_non_destructive_preview_button(self) -> None:
        buttons = self.panel.findChildren(QtWidgets.QPushButton)
        self.assertEqual(["trashPreviewOnlyButton"], [button.objectName() for button in buttons])
        self.assertTrue(all(button.toolTip().strip() for button in buttons))


if __name__ == "__main__":
    unittest.main()
