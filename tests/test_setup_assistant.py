"""Tests für den geführten Linux-Einrichtungsassistenten."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest import mock

from tools.setup_assistant import (
    collect_checks,
    confirm,
    detect_session,
    is_debian_family,
    parse_os_release,
    python_version_ok,
    validate_setup_target,
)


class SetupAssistantTests(unittest.TestCase):
    def test_python_minimum(self) -> None:
        self.assertTrue(python_version_ok((3, 10, 0)))
        self.assertTrue(python_version_ok((3, 12, 1)))
        self.assertFalse(python_version_ok((3, 9, 18)))

    def test_kde_wayland_detection(self) -> None:
        desktop, session_type, is_kde = detect_session(
            {"XDG_CURRENT_DESKTOP": "KDE", "XDG_SESSION_TYPE": "wayland"}
        )
        self.assertEqual("KDE", desktop)
        self.assertEqual("wayland", session_type)
        self.assertTrue(is_kde)

    def test_os_release_parser_and_family(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "os-release"
            path.write_text('ID=ubuntu\nID_LIKE="debian"\n', encoding="utf-8")
            values = parse_os_release(path)
        self.assertEqual("ubuntu", values["ID"])
        self.assertTrue(is_debian_family(values))
        self.assertFalse(is_debian_family({"ID": "fedora"}))

    def test_terminal_confirmation_defaults_to_no(self) -> None:
        self.assertFalse(
            confirm("Test", "Test", use_gui=False, input_function=lambda _: "")
        )
        self.assertTrue(
            confirm("Test", "Test", use_gui=False, input_function=lambda _: "ja")
        )

    def test_symlinked_venv_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "requirements.txt").write_text("PySide6\n", encoding="utf-8")
            target = root / "target"
            target.mkdir()
            (root / ".venv").symlink_to(target, target_is_directory=True)
            with mock.patch("tools.setup_assistant.PROJECT_ROOT", root):
                ok, message = validate_setup_target(root)
        self.assertFalse(ok)
        self.assertIn("symbolischer Link", message)

    def test_non_linux_is_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            checks = collect_checks(
                Path(temp_dir),
                environ={"XDG_CURRENT_DESKTOP": "KDE", "XDG_SESSION_TYPE": "x11"},
                platform_name="win32",
            )
        platform_check = next(item for item in checks if item.key == "platform")
        self.assertEqual("red", platform_check.state)
        self.assertTrue(platform_check.blocking)


if __name__ == "__main__":
    unittest.main()
