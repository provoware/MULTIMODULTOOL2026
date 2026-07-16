#!/usr/bin/env python3
"""Integrationstest für den lokalen Start ohne Browseröffnung."""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "start-local.sh"
APP = "dashboard-studio-ultimate-pro-v3.1.0.html"
PORT = 48731
FALLBACK_PORT = PORT + 1


def reserve_port(port: int) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", port))
    sock.listen(1)
    return sock


def main() -> int:
    env = os.environ.copy()
    env["MULTIMODULTOOL_PORT"] = str(PORT)
    env["MULTIMODULTOOL_NO_BROWSER"] = "1"
    occupied_port = reserve_port(PORT)
    process = subprocess.Popen(
        ["sh", str(SCRIPT)], cwd=ROOT, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, start_new_session=True,
    )
    try:
        deadline = time.monotonic() + 12
        url = f"http://127.0.0.1:{FALLBACK_PORT}/{APP}"
        while time.monotonic() < deadline:
            if process.poll() is not None:
                break
            try:
                with urllib.request.urlopen(url, timeout=0.5) as response:
                    body = response.read(512).decode("utf-8", errors="replace")
                    if response.status == 200 and "<!DOCTYPE html>" in body:
                        print("OK: Startskript nutzt bei belegtem Startport einen erreichbaren Alternativport.")
                        return 0
            except Exception:
                time.sleep(0.15)
        output = process.stdout.read() if process.stdout else ""
        print("FEHLER: Startskript wurde nicht rechtzeitig erreichbar.", file=sys.stderr)
        if output:
            print(output.strip(), file=sys.stderr)
        return 1
    finally:
        occupied_port.close()
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
