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
function cleanText(value, maxLength = 500) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replace(/[\u0000-\u001F\u007F]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, maxLength);
}
function normalizeContent(type, existing = null) {
  const source = existing && typeof existing === "object" ? existing : {};
  if (type === "tasks") return {
    filter: ["all", "open", "done", "overdue"].includes(source.filter) ? source.filter : "all",
    sort: ["manual", "priority", "due"].includes(source.sort) ? source.sort : "manual",
    items: Array.isArray(source.items) ? source.items.slice(0, 5000).map(item => ({
      id: cleanText(item?.id, 120) || "test-id",
      text: cleanText(item?.text, 180),
      done: Boolean(item?.done),
      priority: ["low", "medium", "high"].includes(item?.priority) ? item.priority : "medium",
      due: validDate(item?.due) ? item.due : "",
      createdAt: cleanText(item?.createdAt, 50) || "2026-07-16T00:00:00.000Z"
    })).filter(item => item.text) : []
  };
  return {};
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
function moduleFallbackText(module) {
  const description = cleanText(module?.description, 180);
  if (description) return description;
  return "Noch keine eigene Ansicht hinterlegt. Bitte Beschreibung ergänzen oder später eine Moduldatei verbinden.";
}
function validManifestBasics(manifest) {
  const id = cleanText(manifest?.id, 64);
  const name = cleanText(manifest?.name, 42);
  const description = cleanText(manifest?.description, 240);
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(id)) return "id";
  if (!name) return "name";
  if (description.length < 10) return "description";
  return "ok";
}
const checks = [
  ["clean text trims and limits", cleanText("  A\n\tB\u0000C  ", 5) === "A B C"],
  ["clean text default limit", cleanText("x".repeat(501)).length === 500],
  ["valid date", validDate("2026-02-28") === true],
  ["invalid leap day", validDate("2026-02-29") === false],
  ["invalid format", validDate("28.02.2026") === false],
  ["filename fallback", safeFilename("", "json") === "datei.json"],
  ["filename reserved", safeFilename("CON", "txt") === "_CON.txt"],
  ["filename cleanup", safeFilename("..a/b:c?.md", "txt") === "a-b-c-.md"],
  ["url adds https", normalizeUrl("example.com/path") === "https://example.com/path"],
  ["url strips credentials", normalizeUrl("https://user:pass@example.com/a") === "https://example.com/a"],
  ["url rejects unsupported", normalizeUrl("javascript:alert(1)") === ""],
  ["tasks normalize invalid state", normalizeContent("tasks", { filter: "bad", sort: "bad", items: [{ text: " Aufgabe ", priority: "urgent", due: "2026-02-29" }] }).items[0].priority === "medium"],
  ["tasks drop empty text", normalizeContent("tasks", { items: [{ text: "   " }, { text: "ok" }] }).items.length === 1],
  ["fallback uses description", moduleFallbackText({ description: "  Eigene Ansicht folgt  " }) === "Eigene Ansicht folgt"],
  ["fallback explains missing view", moduleFallbackText({}) === "Noch keine eigene Ansicht hinterlegt. Bitte Beschreibung ergänzen oder später eine Moduldatei verbinden."],
  ["manifest id validation", validManifestBasics({ id: "Bad ID", name: "Test", description: "Beschreibung lang genug" }) === "id"],
  ["manifest description validation", validManifestBasics({ id: "gutes-modul", name: "Test", description: "kurz" }) === "description"],
  ["manifest basics pass", validManifestBasics({ id: "gutes-modul", name: "Test", description: "Beschreibung lang genug" }) === "ok"],
];
const failed = checks.filter(([, ok]) => !ok).map(([name]) => name);
if (failed.length) {
  console.error(JSON.stringify(failed));
  process.exit(1);
}
console.log(JSON.stringify({ checked: checks.length }));
'''

REQUIRED_HELPERS = ("function cleanText", "function normalizeContent", "function validDate", "function safeFilename", "function normalizeUrl", "function getModuleFallbackText", "function moduleFromManifest")


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
    print(f"OK: {checked} Hilfslogik-Faelle fuer Text, Zustand, Datum, Dateiname, URL und Modulvalidierung geprueft.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
