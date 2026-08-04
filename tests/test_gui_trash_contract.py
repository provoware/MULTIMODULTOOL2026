"""Qt-Offscreen-Prüfung für den Papierkorb-Sicherheitsvertrag."""

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
        from src.trash_contract_panel import build_trash_contract_panel

        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        cls.panel = build_trash_contract_panel(QtWidgets)
        cls.panel.show()
        cls.app.processEvents()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.panel.close()
        cls.app.processEvents()

    def test_contract_is_visible_and_copy_delete_actions_are_absent(self) -> None:
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
        for forbidden in ("permanentDeleteButton", "trashDeleteButton", "emptyTrashButton"):
            self.assertIsNone(self.panel.findChild(QtWidgets.QPushButton, forbidden))

    def test_panel_build_performs_no_file_operation(self) -> None:
        buttons = self.panel.findChildren(QtWidgets.QPushButton)
        self.assertEqual(["trashPreviewOnlyButton"], [button.objectName() for button in buttons])
        self.assertTrue(all(button.toolTip().strip() for button in buttons))


if __name__ == "__main__":
    unittest.main()
