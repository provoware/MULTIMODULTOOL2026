"""Regressionstests für den Linux-Single-Instance-Schutz."""

from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import stat
import tempfile
import time
import unittest

from src.single_instance import (
    InstanceSecurityError,
    LaunchRequest,
    MESSAGE_SCHEMA_VERSION,
    SingleInstanceCoordinator,
    instance_paths,
    resolve_runtime_root,
    validate_launch_request,
)


class LaunchRequestTests(unittest.TestCase):
    def test_allowed_requests_are_normalized(self) -> None:
        activate = validate_launch_request(
            {"schemaVersion": MESSAGE_SCHEMA_VERSION, "action": "activate"}
        )
        self.assertEqual(LaunchRequest(), activate)
        diagnostics = validate_launch_request(
            {
                "schemaVersion": MESSAGE_SCHEMA_VERSION,
                "action": "show-diagnostics",
                "diagnosticId": "mmt-xdg-20260804-abcd1234",
            }
        )
        self.assertEqual("MMT-XDG-20260804-ABCD1234", diagnostics.diagnostic_id)

    def test_unknown_fields_paths_and_free_arguments_are_rejected(self) -> None:
        with self.assertRaises(InstanceSecurityError):
            validate_launch_request(
                {
                    "schemaVersion": 1,
                    "action": "activate",
                    "path": "/home/test/private",
                }
            )
        with self.assertRaises(InstanceSecurityError):
            validate_launch_request(
                {"schemaVersion": 1, "action": "open-files", "arguments": ["x"]}
            )


class SingleInstanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.runtime = Path(self.temp.name) / "runtime"
        self.runtime.mkdir(mode=0o700)
        os.chmod(self.runtime, 0o700)

    def test_runtime_root_must_be_absolute_private_and_owned(self) -> None:
        self.assertEqual(
            self.runtime,
            resolve_runtime_root({"XDG_RUNTIME_DIR": str(self.runtime)}, uid=os.getuid()),
        )
        os.chmod(self.runtime, 0o755)
        with self.assertRaises(InstanceSecurityError):
            resolve_runtime_root({"XDG_RUNTIME_DIR": str(self.runtime)}, uid=os.getuid())

    def test_second_start_activates_primary_and_delivers_only_allowed_data(self) -> None:
        primary = SingleInstanceCoordinator(self.runtime)
        self.addCleanup(primary.close)
        first = primary.acquire()
        self.assertTrue(first.is_primary, first.message)

        secondary = SingleInstanceCoordinator(self.runtime)
        request = LaunchRequest(
            action="show-diagnostics",
            diagnostic_id="MMT-XDG-20260804-ABCD1234",
        )
        second = secondary.acquire(request)
        self.assertTrue(second.is_secondary, second.message)

        deadline = time.monotonic() + 2
        received = ()
        while time.monotonic() < deadline and not received:
            received = primary.drain_messages()
            time.sleep(0.02)
        self.assertEqual((request,), received)

    def test_close_removes_only_own_socket_and_metadata(self) -> None:
        primary = SingleInstanceCoordinator(self.runtime)
        result = primary.acquire()
        self.assertTrue(result.is_primary)
        paths = instance_paths(self.runtime)
        self.assertTrue(paths.socket_path.exists())
        self.assertTrue(paths.metadata_path.exists())
        primary.close()
        self.assertFalse(paths.socket_path.exists())
        self.assertFalse(paths.metadata_path.exists())
        self.assertTrue(paths.app_directory.is_dir())

    def test_stale_socket_with_dead_pid_is_recovered(self) -> None:
        paths = instance_paths(self.runtime)
        paths.app_directory.mkdir(mode=0o700)
        os.chmod(paths.app_directory, 0o700)
        stale = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        stale.bind(str(paths.socket_path))
        stale.close()
        metadata = {
            "schemaVersion": 1,
            "pid": 99999999,
            "uid": os.getuid(),
            "bootId": "stale-boot",
            "startedUtc": "2026-08-04T00:00:00+00:00",
        }
        paths.metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        os.chmod(paths.metadata_path, 0o600)

        coordinator = SingleInstanceCoordinator(self.runtime, connect_timeout=0.1)
        self.addCleanup(coordinator.close)
        result = coordinator.acquire()
        self.assertTrue(result.is_primary, result.message)
        self.assertTrue(result.recovered_stale)

    def test_damaged_regular_file_at_socket_path_is_blocked_and_unchanged(self) -> None:
        paths = instance_paths(self.runtime)
        paths.app_directory.mkdir(mode=0o700)
        os.chmod(paths.app_directory, 0o700)
        paths.socket_path.write_text("not-a-socket", encoding="utf-8")
        before = paths.socket_path.read_bytes()

        coordinator = SingleInstanceCoordinator(self.runtime)
        result = coordinator.acquire()
        self.assertTrue(result.is_blocked)
        self.assertEqual(before, paths.socket_path.read_bytes())
        self.assertTrue(stat.S_ISREG(paths.socket_path.lstat().st_mode))

    def test_corrupt_metadata_blocks_stale_cleanup(self) -> None:
        paths = instance_paths(self.runtime)
        paths.app_directory.mkdir(mode=0o700)
        os.chmod(paths.app_directory, 0o700)
        stale = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        stale.bind(str(paths.socket_path))
        stale.close()
        paths.metadata_path.write_text("{broken", encoding="utf-8")
        os.chmod(paths.metadata_path, 0o600)

        coordinator = SingleInstanceCoordinator(self.runtime, connect_timeout=0.1)
        result = coordinator.acquire()
        self.assertTrue(result.is_blocked)
        self.assertTrue(paths.socket_path.exists())
        self.assertTrue(paths.metadata_path.exists())


if __name__ == "__main__":
    unittest.main()
