"""Qt-Offscreen-Prüfung für den sichtbaren Papierkorb-Sicherheitsvertrag."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6 import QtCore, QtWidgets
except ImportError:  # CI installiert PySide6 ausdrücklich.
    QtCore = None
    QtWidgets = None


@unittest.skipUnless(QtWidgets is not None, "PySide6 ist für den GUI-Test erforderlich.")
class TrashContractGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from src.diagnostics_center import DiagnosticSnapshot
        from src.error_events import ErrorEventCenter
        from src.main import build_window
        from src.settings_manager import SettingsLoadResult, default_settings
        from src.xdg_paths import XDGPaths

        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        sentinel = Path(cls.temp.name) / "must-remain-absent"
        cls.sentinel = sentinel
        paths = XDGPaths(
            config=sentinel / "config",
            data=sentinel / "data",
            cache=sentinel / "cache",
            state=sentinel / "state",
            logs=sentinel / "state" / "logs",
            backups=sentinel / "data" / "backups",
        )
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        cls.window = build_window(
            QtWidgets,
            QtCore,
            validation_text="GRÜN",
            path_text="GRÜN",
            settings_text="GRÜN",
            paths=paths,
            settings_result=SettingsLoadResult(settings=default_settings(), source="active"),
            diagnostics=DiagnosticSnapshot(()),
            event_center=ErrorEventCenter(),
        )
        cls.window.show()
        cls.app.processEvents()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.window.close()
        cls.app.processEvents()

    def test_visible_trash_contract_and_no_permanent_delete(self) -> None:
        navigation = self.window.findChild(QtWidgets.QPushButton, "trashNavigation")
        contract = self.window.findChild(QtWidgets.QFrame, "trashContractPanel")
        status = self.window.findChild(QtWidgets.QFrame, "trashStatusPanel")
        self.assertIsNotNone(navigation)
        self.assertTrue(navigation.isEnabled())
        self.assertTrue(contract.isVisible())
        self.assertTrue(status.isVisible())
        all_text = "\n".join(
            widget.text() for widget in self.window.findChildren(QtWidgets.QAbstractButton)
        ).lower()
        self.assertNotIn("dauerhaft löschen", all_text)
        for forbidden in ("permanentDeleteButton", "trashDeleteButton", "emptyTrashButton"):
            self.assertIsNone(self.window.findChild(QtWidgets.QPushButton, forbidden))

    def test_productive_actions_remain_locked_and_build_is_read_only(self) -> None:
        locked = self.window.findChildren(QtWidgets.QPushButton, "lockedPrimaryAction")
        self.assertEqual(6, len(locked))
        self.assertTrue(all(not button.isEnabled() for button in locked))
        self.assertFalse(self.sentinel.exists())


if __name__ == "__main__":
    unittest.main()
