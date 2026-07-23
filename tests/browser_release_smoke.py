#!/usr/bin/env python3
"""Optionale Browser-Smoke-Prüfung für den Release-Kandidaten."""

from __future__ import annotations

import argparse
import http.server
import socketserver
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_FILE = "dashboard-studio-ultimate-pro-v3.1.0.html"
APP_URL = f"http://127.0.0.1:{{port}}/{APP_FILE}"
STORAGE_KEY = "dashboard-studio-ultimate-pro-v3-1"
BACKUP_KEY = "dashboard-studio-ultimate-pro-v3-1-backup"
BROWSERS = ("chromium", "firefox")


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return


def start_server() -> tuple[socketserver.TCPServer, int]:
    handler = lambda *args, **kwargs: QuietHandler(*args, directory=ROOT, **kwargs)
    server = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, int(server.server_address[1])


def import_playwright(require_browser: bool):
    try:
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError:
        if require_browser:
            raise RuntimeError("Playwright ist nicht installiert; Browser-Smoke-Test nicht ausführbar.")
        print("SKIP: Playwright ist nicht installiert; Browser-Smoke-Test nicht ausgeführt.")
        return None
    return sync_playwright


def exercise_browser(playwright, browser_name: str, port: int, require_browser: bool) -> bool:
    browser_type = getattr(playwright, browser_name)
    try:
        browser = browser_type.launch(headless=True)
    except Exception as exc:
        message = f"SKIP: {browser_name} konnte nicht gestartet werden: {exc}"
        if require_browser:
            raise RuntimeError(message) from exc
        print(message)
        return False

    stage = "Start"
    try:
        with tempfile.TemporaryDirectory(prefix=f"mmt-{browser_name}-") as download_dir:
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()
            page.on("dialog", lambda dialog: dialog.accept())

            stage = "App laden"
            page.goto(APP_URL.format(port=port), wait_until="domcontentloaded")
            page.locator("#app").wait_for(timeout=7000)
            page.wait_for_function("key => Boolean(localStorage.getItem(key))", arg=STORAGE_KEY)
            page.wait_for_function("() => Boolean(window.MULTIMODULTOOL2026)")

            stage = "Speicher prüfen"
            page.evaluate("() => window.MULTIMODULTOOL2026.checkStorageHealth()")
            page.wait_for_timeout(250)

            stage = "Backup erstellen"
            page.evaluate("() => window.MULTIMODULTOOL2026.createLocalBackup(true)")
            page.wait_for_function("key => Boolean(localStorage.getItem(key))", arg=BACKUP_KEY)

            stage = "Backup wiederherstellen"
            page.evaluate("() => window.MULTIMODULTOOL2026.restoreLocalBackup()")
            page.wait_for_function("key => Boolean(localStorage.getItem(key))", arg=STORAGE_KEY)

            stage = "Konfiguration importieren"
            exported_state = page.evaluate("key => localStorage.getItem(key)", STORAGE_KEY)
            if not exported_state:
                raise RuntimeError("Exportierter Zustand ist leer.")
            page.evaluate("() => window.MULTIMODULTOOL2026.executeCommand('importConfig')")
            page.locator("#importData").fill(exported_state)
            page.locator("#confirmImport").click()
            page.wait_for_function("key => Boolean(localStorage.getItem(key))", arg=STORAGE_KEY)

            stage = "Konfiguration exportieren"
            with page.expect_download(timeout=7000) as download_info:
                page.evaluate("() => window.MULTIMODULTOOL2026.exportConfig()")
            download = download_info.value
            target = Path(download_dir) / download.suggested_filename
            download.save_as(target)
            if not target.name.endswith(".json") or target.stat().st_size <= 0:
                raise RuntimeError("Exportdatei fehlt oder ist leer.")

            context.close()
            print(f"OK: {browser_name} Browser-Smoke-Test bestanden.")
            return True
    except Exception as exc:
        raise RuntimeError(f"{browser_name}: Fehler in Phase '{stage}': {exc}") from exc
    finally:
        browser.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Optionale Browser-Smoke-Prüfung für den Release-Kandidaten.")
    parser.add_argument("--browser", choices=BROWSERS, action="append")
    parser.add_argument("--require-browser", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        imported = import_playwright(args.require_browser)
    except RuntimeError as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        return 1
    if imported is None:
        return 0

    server, port = start_server()
    tried = False
    try:
        with imported() as playwright:
            for browser_name in args.browser or BROWSERS:
                tried = exercise_browser(playwright, browser_name, port, args.require_browser) or tried
    except RuntimeError as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        return 1
    finally:
        server.shutdown()
        server.server_close()

    if not tried:
        if args.require_browser:
            print("FEHLER: Kein Browser-Smoke-Test wurde ausgeführt.", file=sys.stderr)
            return 1
        print("SKIP: Kein startbarer Playwright-Browser gefunden; Browser-Freigabe bleibt offen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
