#!/usr/bin/env python3
"""Browser-Smoke-Prüfung für Start, Speicherinitialisierung und Export."""
from __future__ import annotations
import argparse, http.server, socketserver, sys, tempfile, threading
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
APP_FILE="dashboard-studio-ultimate-pro-v3.1.0.html"
APP_URL=f"http://127.0.0.1:{{port}}/{APP_FILE}"
STORAGE_KEY="dashboard-studio-ultimate-pro-v3-1"
BROWSERS=("chromium","firefox")
class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object)->None: return

def start_server():
    handler=lambda *args,**kwargs: QuietHandler(*args,directory=ROOT,**kwargs)
    server=socketserver.TCPServer(("127.0.0.1",0),handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    return server,int(server.server_address[1])

def import_playwright(required):
    try: from playwright.sync_api import sync_playwright
    except ModuleNotFoundError:
        if required: raise RuntimeError("Playwright ist nicht installiert.")
        print("SKIP: Playwright ist nicht installiert."); return None
    return sync_playwright

def exercise(playwright,name,port,required):
    try: browser=getattr(playwright,name).launch(headless=True)
    except Exception as exc:
        if required: raise RuntimeError(f"{name} konnte nicht gestartet werden: {exc}") from exc
        print(f"SKIP: {name} nicht startbar: {exc}"); return False
    try:
        with tempfile.TemporaryDirectory(prefix=f"mmt-{name}-") as download_dir:
            context=browser.new_context(accept_downloads=True)
            page=context.new_page()
            page.goto(APP_URL.format(port=port),wait_until="domcontentloaded")
            page.locator("#app").wait_for(timeout=7000)
            page.wait_for_function("key => Boolean(localStorage.getItem(key))",arg=STORAGE_KEY)
            page.wait_for_function("() => Boolean(window.MULTIMODULTOOL2026?.exportConfig)")
            with page.expect_download(timeout=7000) as info:
                page.evaluate("() => window.MULTIMODULTOOL2026.exportConfig()")
            download=info.value
            target=Path(download_dir)/download.suggested_filename
            download.save_as(target)
            if target.suffix.lower()!=".json" or target.stat().st_size<=0:
                raise RuntimeError("Exportdatei fehlt oder ist leer.")
            context.close()
            print(f"OK: {name} Browser-Smoke-Test bestanden.")
            return True
    finally: browser.close()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--browser",choices=BROWSERS,action="append")
    parser.add_argument("--require-browser",action="store_true")
    args=parser.parse_args()
    try: imported=import_playwright(args.require_browser)
    except RuntimeError as exc: print(f"FEHLER: {exc}",file=sys.stderr); return 1
    if imported is None: return 0
    server,port=start_server(); tried=False
    try:
        with imported() as playwright:
            for name in args.browser or BROWSERS: tried=exercise(playwright,name,port,args.require_browser) or tried
    except Exception as exc: print(f"FEHLER: {exc}",file=sys.stderr); return 1
    finally: server.shutdown(); server.server_close()
    if not tried and args.require_browser: return 1
    return 0
if __name__=="__main__": raise SystemExit(main())
