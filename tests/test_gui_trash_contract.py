"""Qt offscreen checks for trash, transaction and run-control contracts."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6 import QtWidgets
except ImportError:  # CI installs PySide6 explicitly.
    QtWidgets = None


@unittest.skipUnless(QtWidgets is not None, "PySide6 ist für den GUI-Test erforderlich.")
class TrashContractGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from src.trash_contract_panel import build_trash_contract_panel
        from src.transaction_overview import TransactionEntry, TransactionSnapshot

        snapshot = TransactionSnapshot(
            (
                TransactionEntry(
                    transaction_id="MMTTRASH-20260804T120000-ABCDEF123456",
                    state="trashed",
                    created_utc="2026-08-04T12:00:00Z",
                    original_relative_path="data/example.txt",
                    detail="",
                ),
                TransactionEntry(
                    transaction_id="MMTTRASH-20260804T120001-ABCDEF123457",
                    state="damaged",
                    created_utc="",
                    original_relative_path="",
                    detail="Manifest beschädigt; unverändert.",
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

    def test_contract_and_read_only_transaction_overview_are_visible(self) -> None:
        contract = self.panel.findChild(QtWidgets.QFrame, "trashContractPanel")
        status = self.panel.findChild(QtWidgets.QFrame, "trashStatusPanel")
        preview = self.panel.findChild(QtWidgets.QPushButton, "trashPreviewOnlyButton")
        overview = self.panel.findChild(QtWidgets.QFrame, "transactionOverview")
        listing = self.panel.findChild(QtWidgets.QListWidget, "transactionList")
        detail = self.panel.findChild(QtWidgets.QPlainTextEdit, "transactionDetail")
        self.assertTrue(contract.isVisible())
        self.assertTrue(status.isVisible())
        self.assertTrue(preview.isEnabled())
        self.assertTrue(overview.isVisible())
        self.assertEqual(2, listing.count())
        self.assertTrue(detail.isReadOnly())

    def test_state_filter_marks_damaged_without_mutation_action(self) -> None:
        state_filter = self.panel.findChild(QtWidgets.QComboBox, "transactionStateFilter")
        listing = self.panel.findChild(QtWidgets.QListWidget, "transactionList")
        damaged_index = state_filter.findData("damaged")
        state_filter.setCurrentIndex(damaged_index)
        self.app.processEvents()
        self.assertEqual(1, listing.count())
        self.assertIn("DAMAGED", listing.item(0).text())

    def test_run_control_contract_is_visible_and_read_only(self) -> None:
        contract = self.panel.findChild(QtWidgets.QFrame, "runControlContract")
        rules = self.panel.findChild(QtWidgets.QLabel, "runControlRules")
        notice = self.panel.findChild(QtWidgets.QLabel, "runControlReadOnlyNotice")
        self.assertTrue(contract.isVisible())
        self.assertIn("MMTRUN", rules.text())
        self.assertIn("SIGKILL", rules.text())
        self.assertTrue(notice.isVisible())
        for forbidden in (
            "runStartButton",
            "runCancelButton",
            "runResumeButton",
            "runRepairButton",
        ):
            self.assertIsNone(self.panel.findChild(QtWidgets.QPushButton, forbidden))

    def test_no_destructive_or_export_actions_exist(self) -> None:
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
            "transactionUploadButton",
            "transactionExportButton",
        ):
            self.assertIsNone(self.panel.findChild(QtWidgets.QPushButton, forbidden))

    def test_panel_build_performs_no_file_operation(self) -> None:
        buttons = self.panel.findChildren(QtWidgets.QPushButton)
        self.assertEqual(["trashPreviewOnlyButton"], [button.objectName() for button in buttons])
        self.assertTrue(all(button.toolTip().strip() for button in buttons))


if __name__ == "__main__":
    unittest.main()
