#!/usr/bin/env python3
"""Prueft reine Hilfslogik aus der HTML-App mit kleinen Eingabe-Ausgabe-Faellen."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "dashboard-studio-ultimate-pro-v3.1.0.html"

NODE_SCRIPT = r'''
function cleanText(value, maxLength = 200) {
  if (value === null || value === undefined) return "";
  return String(value).replace(/\u0000/g, "").replace(/\s+/g, " ").trim().slice(0, maxLength);
}
function validDate(value) {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const [year, month, day] = value.split("-").map(Number);
  const date = new Date(year, month - 1, day);
  return date.getFullYear() === year && date.getMonth() === month - 1 && date.getDate() === day;
}
function safeFilename(value, fallbackExt = "txt") {
  const extension = cleanText(fallbackExt, 12).replace(/[^a-z0-9]/gi, "").toLowerCase() || "txt";
  let filename = String(value || "datei")
    .replace(/[\u0000-\u001F\u007F]/g, "")
    .replace(/[\\/:*?"<>|]+/g, "-")
    .replace(/\s+/g, " ")
    .replace(/^\.+|[. ]+$/g, "")
    .slice(0, 160);
  if (!filename) filename = "datei";
  if (/^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)/i.test(filename)) filename = `_${filename}`;
  if (!/\.[a-z0-9]{1,12}$/i.test(filename)) filename += `.${extension}`;
  return filename;
}
function normalizeUrl(value) {
  try {
    const raw = String(value || "").trim();
    if (!raw) return "";
    const url = new URL(/^https?:\/\//i.test(raw) ? raw : `https://${raw}`);
    if (!['http:', 'https:'].includes(url.protocol)) return "";
    url.username = "";
    url.password = "";
    return url.href;
  } catch (_) {
    return "";
  }
}
const checks = [
  ["valid date", validDate("2026-02-28") === true],
  ["invalid leap day", validDate("2026-02-29") === false],
  ["invalid format", validDate("28.02.2026") === false],
  ["filename fallback", safeFilename("", "json") === "datei.json"],
  ["filename reserved", safeFilename("CON", "txt") === "_CON.txt"],
  ["filename cleanup", safeFilename("..a/b:c?.md", "txt") === "a-b-c-.md"],
  ["url adds https", normalizeUrl("example.com/path") === "https://example.com/path"],
  ["url strips credentials", normalizeUrl("https://user:pass@example.com/a") === "https://example.com/a"],
  ["url rejects unsupported", normalizeUrl("javascript:alert(1)") === ""],
];
const failed = checks.filter(([, ok]) => !ok).map(([name]) => name);
if (failed.length) {
  console.error(JSON.stringify(failed));
  process.exit(1);
}
console.log(JSON.stringify({ checked: checks.length }));
'''

REQUIRED_HELPERS = ("function validDate", "function safeFilename", "function normalizeUrl")


def main() -> int:
    source = APP.read_text(encoding="utf-8")
    missing = [helper for helper in REQUIRED_HELPERS if helper not in source]
    if missing:
        print("FEHLER: Hilfsfunktion fehlt in der HTML-App: " + ", ".join(missing))
        return 1

    result = subprocess.run(["node", "-e", NODE_SCRIPT], text=True, capture_output=True, check=False)
    if result.returncode != 0:
        print("FEHLER: Hilfslogik-Test fehlgeschlagen")
        print(result.stderr.strip() or result.stdout.strip())
        return 1

    checked = json.loads(result.stdout)["checked"]
    print(f"OK: {checked} Hilfslogik-Faelle fuer Datum, Dateiname und URL geprueft.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
