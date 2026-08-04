"""Worker intentionally killed by the SIGKILL run-control matrix."""

from __future__ import annotations

import os
from pathlib import Path
import signal
import sys

from src.run_control import resume_run


def main() -> int:
    if len(sys.argv) != 5:
        return 64
    project = Path(sys.argv[1])
    run_id = sys.argv[2]
    target_stage = sys.argv[3]
    marker = Path(sys.argv[4])

    def failpoint(stage: str) -> None:
        if stage != target_stage:
            return
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0)
        descriptor = os.open(marker, flags, 0o600)
        try:
            os.write(descriptor, (stage + "\n").encode("ascii"))
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.kill(os.getpid(), signal.SIGKILL)

    resume_run(project, run_id, failpoint=failpoint)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
