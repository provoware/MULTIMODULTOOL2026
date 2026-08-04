"""Tests für die sichere XDG-Pfadverwaltung."""

from __future__ import annotations

from pathlib import Path
import stat
import tempfile
import unittest

from src.xdg_paths import ensure_xdg_paths, resolve_xdg_paths, validate_xdg_paths


class XDGPathTests(unittest.TestCase):
    def test_default_layout_uses_linux_xdg_fallbacks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir) / "home"
            result = resolve_xdg_paths(environment={}, home=home)
            self.assertTrue(result.is_valid, result.errors)
            self.assertEqual(home / ".config" / "multimodultool2026", result.paths.config)
            self.assertEqual(
                home / ".local" / "share" / "multimodultool2026",
                result.paths.data,
            )
            self.assertEqual(home / ".cache" / "multimodultool2026", result.paths.cache)
            self.assertEqual(
                home / ".local" / "state" / "multimodultool2026",
                result.paths.state,
            )
            self.assertEqual(result.paths.state / "logs", result.paths.logs)
            self.assertEqual(result.paths.data / "backups", result.paths.backups)

    def test_custom_xdg_roots_are_honored(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            env = {
                "XDG_CONFIG_HOME": str(root / "cfg"),
                "XDG_DATA_HOME": str(root / "data"),
                "XDG_CACHE_HOME": str(root / "cache"),
                "XDG_STATE_HOME": str(root / "state"),
            }
            result = resolve_xdg_paths(environment=env, home=root / "home")
            self.assertTrue(result.is_valid, result.errors)
            self.assertEqual(root / "cfg" / "multimodultool2026", result.paths.config)
            self.assertEqual(
                root / "state" / "multimodultool2026" / "logs",
                result.paths.logs,
            )

    def test_relative_xdg_root_is_rejected(self) -> None:
        result = resolve_xdg_paths(
            environment={"XDG_CONFIG_HOME": "relative/config"},
            home=Path("/tmp/home"),
        )
        self.assertFalse(result.is_valid)
        self.assertTrue(any("absoluter Linux-Pfad" in item for item in result.errors))

    def test_source_tree_overlap_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir) / "project"
            project.mkdir()
            env = {
                "XDG_CONFIG_HOME": str(project / "config"),
                "XDG_DATA_HOME": str(Path(temp_dir) / "data"),
                "XDG_CACHE_HOME": str(Path(temp_dir) / "cache"),
                "XDG_STATE_HOME": str(Path(temp_dir) / "state"),
            }
            resolved = resolve_xdg_paths(environment=env, home=Path(temp_dir) / "home")
            check = validate_xdg_paths(resolved.paths, project_root=project)
            self.assertFalse(check.is_valid)
            self.assertTrue(any("Programmverzeichnis" in item for item in check.errors))

    def test_app_specific_symlink_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = root / "project"
            project.mkdir()
            config_base = root / "config"
            config_base.mkdir()
            outside = root / "outside"
            outside.mkdir()
            (config_base / "multimodultool2026").symlink_to(
                outside,
                target_is_directory=True,
            )
            env = {
                "XDG_CONFIG_HOME": str(config_base),
                "XDG_DATA_HOME": str(root / "data"),
                "XDG_CACHE_HOME": str(root / "cache"),
                "XDG_STATE_HOME": str(root / "state"),
            }
            resolved = resolve_xdg_paths(environment=env, home=root / "home")
            check = validate_xdg_paths(resolved.paths, project_root=project)
            self.assertFalse(check.is_valid)
            self.assertTrue(any("Symbolischer Link" in item for item in check.errors))

    def test_ensure_creates_private_writable_directories_outside_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = root / "project"
            project.mkdir()
            marker = project / "marker.txt"
            marker.write_text("unverändert", encoding="utf-8")
            env = {
                "XDG_CONFIG_HOME": str(root / "config"),
                "XDG_DATA_HOME": str(root / "data"),
                "XDG_CACHE_HOME": str(root / "cache"),
                "XDG_STATE_HOME": str(root / "state"),
            }
            resolved = resolve_xdg_paths(environment=env, home=root / "home")
            result = ensure_xdg_paths(resolved.paths, project_root=project)
            self.assertTrue(result.is_valid, result.errors)
            self.assertEqual("unverändert", marker.read_text(encoding="utf-8"))
            for _, path in result.paths.items():
                self.assertTrue(path.is_dir())
                self.assertFalse(path.is_symlink())
                self.assertEqual(0o700, stat.S_IMODE(path.stat().st_mode))
                self.assertFalse(any(path.glob(".mmtool-write-test-*")))

    def test_duplicate_top_level_xdg_targets_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            same = root / "same"
            env = {
                "XDG_CONFIG_HOME": str(same),
                "XDG_DATA_HOME": str(same),
                "XDG_CACHE_HOME": str(root / "cache"),
                "XDG_STATE_HOME": str(root / "state"),
            }
            project = root / "project"
            project.mkdir()
            resolved = resolve_xdg_paths(environment=env, home=root / "home")
            check = validate_xdg_paths(resolved.paths, project_root=project)
            self.assertFalse(check.is_valid)
            self.assertTrue(any("doppelt belegt" in item for item in check.errors))


if __name__ == "__main__":
    unittest.main()
