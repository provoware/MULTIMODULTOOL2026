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
const fs = require("fs");
const source = fs.readFileSync(process.argv[1], "utf8");

function extractFunction(name) {
  const marker = `function ${name}`;
  const start = source.indexOf(marker);
  if (start === -1) throw new Error(`Funktion fehlt: ${name}`);
  const bodyStart = source.indexOf("{", start);
  if (bodyStart === -1) throw new Error(`Funktionsstart fehlt: ${name}`);
  let depth = 0;
  for (let index = bodyStart; index < source.length; index += 1) {
    const char = source[index];
    if (char === "{") depth += 1;
    if (char === "}") depth -= 1;
    if (depth === 0) return source.slice(start, index + 1);
  }
  throw new Error(`Funktionsende fehlt: ${name}`);
}

const productionFunctions = [
  "cleanText",
  "validDate",
  "safeFilename",
  "normalizeUrl",
  "getModuleFallbackText",
  "formatStorageBytes",
  "moduleFromManifest",
].map(extractFunction).join("\n");

const supportScript = `
const ALLOWED_TYPES = ["overview", "calendar", "notes", "tasks", "projectboard", "quicktext", "editor", "code", "links", "timer", "debug", "modulebuilder", "settings", "custom", "mother", "registry", "debugging"];
function newId() { return "test-id"; }
function colorFromText() { return "#38bdf8"; }
function moduleCategoryId() { return "test"; }
function normalizeContent(type) { return { testType: type }; }
`;

eval(`${supportScript}\n${productionFunctions}`);

function validManifestBasics(manifest) {
  try {
    moduleFromManifest(manifest);
    return "ok";
  } catch (error) {
    if (error.message.includes("Modul-ID")) return "id";
    if (error.message.includes("Modulname")) return "name";
    if (error.message.includes("Modulbeschreibung")) return "description";
    return error.message;
  }
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
  ["fallback uses description", getModuleFallbackText({ description: "  Eigene Ansicht folgt  " }) === "Eigene Ansicht folgt"],
  ["fallback explains missing view", getModuleFallbackText({}) === "Noch keine eigene Ansicht hinterlegt. Bitte Modulbeschreibung ergänzen oder eine geprüfte Moduldatei im Manifest verknüpfen."],
  ["storage bytes formats bytes", formatStorageBytes(999) === "999 B"],
  ["storage bytes formats kilobytes", formatStorageBytes(1530) === "1.5 KB"],
  ["storage bytes formats megabytes", formatStorageBytes(2500000) === "2.5 MB"],
  ["manifest id validation", validManifestBasics({ id: "Bad ID", name: "Test", description: "Beschreibung lang genug" }) === "id"],
  ["manifest name validation", validManifestBasics({ id: "gutes-modul", name: "", description: "Beschreibung lang genug" }) === "name"],
  ["manifest description validation", validManifestBasics({ id: "gutes-modul", name: "Test", description: "kurz" }) === "description"],
  ["manifest basics pass", validManifestBasics({ id: "gutes-modul", name: "Test", description: "Beschreibung lang genug" }) === "ok"],
];
const failed = checks.filter(([, ok]) => !ok).map(([name]) => name);
if (failed.length) {
  console.error(JSON.stringify(failed));
  process.exit(1);
}
console.log(JSON.stringify({ checked: checks.length, extracted: 7 }));
'''

REQUIRED_HELPERS = ("function cleanText", "function validDate", "function safeFilename", "function normalizeUrl", "function getModuleFallbackText", "function formatStorageBytes", "function moduleFromManifest")


def main() -> int:
    source = APP.read_text(encoding="utf-8")
    missing = [helper for helper in REQUIRED_HELPERS if helper not in source]
    if missing:
        print("FEHLER: Hilfsfunktion fehlt in der HTML-App: " + ", ".join(missing))
        return 1

    result = subprocess.run(["node", "-e", NODE_SCRIPT, str(APP)], text=True, capture_output=True, check=False)
    if result.returncode != 0:
        print("FEHLER: Hilfslogik-Test fehlgeschlagen")
        print(result.stderr.strip() or result.stdout.strip())
        return 1

    output = json.loads(result.stdout)
    checked = output["checked"]
    extracted = output["extracted"]
    print(f"OK: {checked} Hilfslogik-Faelle mit {extracted} echten Funktionsbloecken aus der HTML-App geprueft.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
