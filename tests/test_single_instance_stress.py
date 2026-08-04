"""Parallelstart-Stresstest für zwanzig nahezu gleichzeitige Zweitstarts."""

from __future__ import annotations

from collections import Counter
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest

from src.single_instance import LaunchRequest, SingleInstanceCoordinator, instance_paths


class ParallelStartStressTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.runtime = Path(self.temp.name) / "runtime"
        self.runtime.mkdir(mode=0o700)
        os.chmod(self.runtime, 0o700)

    def test_twenty_parallel_secondaries_reach_exactly_one_primary_once(self) -> None:
        primary = SingleInstanceCoordinator(self.runtime, connect_timeout=3.0)
        primary_result = primary.acquire()
        self.assertTrue(primary_result.is_primary, primary_result.message)

        count = 20
        barrier = threading.Barrier(count + 1)
        results: list[object | None] = [None] * count
        requests = [
            LaunchRequest(
                action="show-diagnostics",
                diagnostic_id=f"MMT-STRESS-{index:02d}",
            )
            for index in range(count)
        ]

        def start_secondary(index: int) -> None:
            coordinator = SingleInstanceCoordinator(self.runtime, connect_timeout=3.0)
            try:
                barrier.wait(timeout=5.0)
                results[index] = coordinator.acquire(requests[index])
            finally:
                coordinator.close()

        threads = [
            threading.Thread(
                target=start_secondary,
                args=(index,),
                name=f"mmt-secondary-{index:02d}",
            )
            for index in range(count)
        ]
        for thread in threads:
            thread.start()
        barrier.wait(timeout=5.0)
        for thread in threads:
            thread.join(timeout=8.0)
            self.assertFalse(thread.is_alive(), thread.name)

        self.assertEqual(1, int(primary_result.is_primary))
        self.assertTrue(all(result is not None for result in results))
        self.assertTrue(
            all(getattr(result, "is_secondary", False) for result in results),
            [getattr(result, "message", "fehlend") for result in results],
        )

        received: list[LaunchRequest] = []
        deadline = time.monotonic() + 6.0
        while time.monotonic() < deadline and len(received) < count:
            received.extend(primary.drain_messages(limit=100))
            if len(received) < count:
                time.sleep(0.02)

        expected_keys = {(item.action, item.diagnostic_id) for item in requests}
        received_keys = [(item.action, item.diagnostic_id) for item in received]
        counts = Counter(received_keys)
        self.assertEqual(expected_keys, set(received_keys))
        self.assertEqual(count, len(received_keys))
        self.assertTrue(all(value == 1 for value in counts.values()), counts)

        paths = instance_paths(self.runtime)
        self.assertTrue(paths.socket_path.exists())
        self.assertTrue(paths.metadata_path.exists())
        primary.close()
        self.assertFalse(paths.socket_path.exists())
        self.assertFalse(paths.metadata_path.exists())
        self.assertEqual([], list(paths.app_directory.iterdir()))


if __name__ == "__main__":
    unittest.main()
