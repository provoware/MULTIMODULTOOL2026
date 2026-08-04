"""Qt-Offscreen-Smoke-Test für die neun verbindlichen Layoutzonen."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6 import QtCore, QtWidgets
except ImportError:  # pragma: no cover - CI installiert PySide6 ausdrücklich.
    QtCore = None
    QtWidgets = None


@unittest.skipUnless(QtWidgets is not None, "PySide6 ist für den GUI-Smoke-Test erforderlich.")
class OffscreenGuiSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from src.main import ZONE_OBJECT_NAMES, build_window
        from src.settings_manager import SettingsLoadResult, default_settings
        from src.xdg_paths import XDGPaths

        cls._temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls._temp.cleanup)
        root = Path(cls._temp.name) / "must-remain-absent"
        cls._sentinel_root = root
        paths = XDGPaths(
            config=root / "config",
            data=root / "data",
            cache=root / "cache",
            state=root / "state",
            logs=root / "state" / "logs",
            backups=root / "data" / "backups",
        )
        settings_result = SettingsLoadResult(
            settings=default_settings(),
            source="active",
        )
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        cls.window = build_window(
            QtWidgets,
            QtCore,
            validation_text="GRÜN: Manifest gültig.",
            path_text="GRÜN: XDG-Pfadplan gültig.",
            settings_text="GRÜN: Versionierte Einstellungen sind gültig.",
            paths=paths,
            settings_result=settings_result,
        )
        cls.window.show()
        cls.app.processEvents()
        cls.zone_names = ZONE_OBJECT_NAMES

    @classmethod
    def tearDownClass(cls) -> None:
        cls.window.close()
        cls.app.processEvents()

    def test_all_nine_layout_zones_exist_and_are_visible(self) -> None:
        self.assertEqual(9, len(self.zone_names))
        zone_ids: list[str] = []
        for name in self.zone_names:
            with self.subTest(zone=name):
                widget = self.window.findChild(QtWidgets.QWidget, name)
                self.assertIsNotNone(widget)
                self.assertTrue(widget.isVisible())
                zone_ids.append(str(widget.property("zoneId")))
        self.assertEqual([f"Z{index:02d}" for index in range(1, 10)], zone_ids)

    def test_workspace_and_context_remain_scrollable(self) -> None:
        workspace = self.window.findChild(QtWidgets.QScrollArea, "workspaceScroll")
        context = self.window.findChild(QtWidgets.QScrollArea, "contextScroll")
        self.assertIsNotNone(workspace)
        self.assertIsNotNone(context)
        self.assertTrue(workspace.widgetResizable())
        self.assertTrue(context.widgetResizable())
        self.assertEqual(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
            workspace.horizontalScrollBarPolicy(),
        )
        self.assertEqual(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded,
            workspace.verticalScrollBarPolicy(),
        )

    def test_safety_states_are_textual_and_visible(self) -> None:
        labels = [
            label
            for label in self.window.findChildren(QtWidgets.QLabel)
            if bool(label.property("safetyStatus"))
        ]
        self.assertGreaterEqual(len(labels), 3)
        for label in labels:
            self.assertTrue(label.isVisible())
            self.assertTrue(label.text().strip())

    def test_unreleased_actions_are_disabled(self) -> None:
        locked = self.window.findChildren(QtWidgets.QPushButton, "lockedPrimaryAction")
        self.assertEqual(6, len(locked))
        self.assertTrue(all(not button.isEnabled() for button in locked))
        self.assertTrue(all(button.toolTip().strip() for button in locked))

    def test_window_build_does_not_touch_user_data_paths(self) -> None:
        self.assertFalse(self._sentinel_root.exists())


if __name__ == "__main__":
    unittest.main()
