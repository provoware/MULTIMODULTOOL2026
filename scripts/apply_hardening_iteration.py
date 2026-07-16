#!/usr/bin/env python3
"""Apply the focused manifest, import and keyboard hardening iteration once."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "dashboard-studio-ultimate-pro-v3.1.0.html"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"Expected exactly one match in {path}: {old[:80]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# Preserve the stable manifest identity across save, reload, backup and import.
replace_once(
    APP,
    """          return {
            id,
            name: cleanText(raw.name, 80) || typeLabel(type),""",
    """          const manifestId = cleanText(raw.manifestId, 64);
          return {
            id,
            manifestId: /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(manifestId) ? manifestId : "",
            name: cleanText(raw.name, 80) || typeLabel(type),""",
)

# Never identify a manifest module by name alone. A guarded legacy match migrates old saved states.
replace_once(
    APP,
    """        const existing = state.modules.find(item => item.manifestId === manifest.id || item.name === module.name);""",
    """        const existing = state.modules.find(item => item.manifestId === manifest.id)
          || state.modules.find(item => !item.manifestId && item.name === module.name && item.type === module.type && item.description === module.description);""",
)

# Use actual UTF-8 byte size for pasted imports, not JavaScript character count.
replace_once(
    APP,
    """        if (new Blob([value]).size > MAX_IMPORT_BYTES) return toast(feedbackText({""",
    """        const importBytes = new Blob([value]).size;
        if (importBytes > MAX_IMPORT_BYTES) return toast(feedbackText({""",
)
replace_once(
    APP,
    """          if (!(await applyImportedState(parsed, value.length))) return;""",
    """          if (!(await applyImportedState(parsed, importBytes))) return;""",
)

# Persist an imported state before switching the live UI to it.
old_import = """      async function applyImportedState(parsed, importSize = 0) {
        if (state.confirmDestructive && !confirm("Aktuelle Konfiguration durch den Import ersetzen? Vorher wird ein lokales Backup erstellt.")) return false;
        if (!(await hasEnoughStorageForImport(importSize))) {
          toast(feedbackText({
            title: "Import abgebrochen: Browser-Speicher wirkt knapp.",
            cause: "Für Import und Sicherheitskopie ist wahrscheinlich nicht genug freier Speicher vorhanden.",
            solution: "Bitte zuerst Konfiguration exportieren oder Browser-Speicher freigeben.",
            changed: "Nichts importiert; aktuelle Konfiguration bleibt unverändert.",
            level: "warning"
          }));
          return false;
        }
        pushHistory("Konfiguration importieren");
        if (!createLocalBackup(false)) {
          toast(feedbackText({
            title: "Import abgebrochen: Vorheriges Backup konnte nicht erstellt werden.",
            cause: "Der Browser-Speicher ist nicht verfügbar, voll oder gesperrt.",
            solution: "Bitte Speicherrechte prüfen oder die Konfiguration als Datei exportieren.",
            changed: "Nichts importiert; aktuelle Konfiguration bleibt unverändert.",
            level: "error"
          }));
          return false;
        }
        state = normalizeState(parsed);
        logAction("Konfiguration geprüft und importiert", "Datei");
        applyVisualSettings();
        saveState("Import gespeichert");
        renderAll();
        toast(feedbackText({
          title: "Konfiguration geprüft und importiert.",
          cause: "Die JSON-Daten waren gültig und ein lokales Backup wurde vorher erstellt.",
          solution: "Bitte kurz prüfen, ob Module und Daten wie erwartet angezeigt werden.",
          changed: "Import gespeichert; vorheriger Stand liegt als lokales Backup vor.",
          level: "success"
        }));
        return true;
      }"""
new_import = """      async function applyImportedState(parsed, importSize = 0) {
        if (state.confirmDestructive && !confirm("Aktuelle Konfiguration durch den Import ersetzen? Vorher wird ein lokales Backup erstellt.")) return false;
        if (!(await hasEnoughStorageForImport(importSize))) {
          toast(feedbackText({
            title: "Import abgebrochen: Browser-Speicher wirkt knapp.",
            cause: "Für Import und Sicherheitskopie ist wahrscheinlich nicht genug freier Speicher vorhanden.",
            solution: "Bitte zuerst Konfiguration exportieren oder Browser-Speicher freigeben.",
            changed: "Nichts importiert; aktuelle Konfiguration bleibt unverändert.",
            level: "warning"
          }));
          return false;
        }
        pushHistory("Konfiguration importieren");
        if (!createLocalBackup(false)) {
          toast(feedbackText({
            title: "Import abgebrochen: Vorheriges Backup konnte nicht erstellt werden.",
            cause: "Der Browser-Speicher ist nicht verfügbar, voll oder gesperrt.",
            solution: "Bitte Speicherrechte prüfen oder die Konfiguration als Datei exportieren.",
            changed: "Nichts importiert; aktuelle Konfiguration bleibt unverändert.",
            level: "error"
          }));
          return false;
        }
        try {
          const importedState = normalizeState(parsed);
          importedState.updatedAt = new Date().toISOString();
          importedState.saveCount = (Number(importedState.saveCount) || 0) + 1;
          const serialized = JSON.stringify(importedState);
          if (new Blob([serialized]).size > MAX_STORAGE_BYTES) throw new Error("Import überschreitet den sicheren lokalen Speicherumfang");
          clearTimeout(pendingSaveTimer);
          storageService.writePrimary(serialized);
          state = importedState;
        } catch (error) {
          handleAppError(error, {
            area: "Import",
            userMessage: "Import konnte nicht sicher gespeichert werden.",
            cause: "Der geprüfte Import ist zu groß oder der Browser-Speicher hat das Schreiben abgelehnt.",
            solution: "Bitte Daten verkleinern, Speicher freigeben oder die bisherige Konfiguration weiterverwenden.",
            changed: "Import verworfen; aktuelle Konfiguration bleibt unverändert. Das Sicherheitsbackup wurde erstellt."
          });
          return false;
        }
        logAction("Konfiguration geprüft, gespeichert und importiert", "Datei");
        applyVisualSettings();
        saveStatus.textContent = `Import gespeichert · ${new Date().toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" })}`;
        renderAll();
        toast(feedbackText({
          title: "Konfiguration geprüft und importiert.",
          cause: "Die JSON-Daten waren gültig, wurden sofort gespeichert und vorher lokal gesichert.",
          solution: "Bitte kurz prüfen, ob Module und Daten wie erwartet angezeigt werden.",
          changed: "Import gespeichert; vorheriger Stand liegt als lokales Backup vor.",
          level: "success"
        }));
        return true;
      }"""
replace_once(APP, old_import, new_import)

# Treat zero storage usage as a valid estimate.
replace_once(
    APP,
    """          if (!estimate.quota || !estimate.usage) return true;""",
    """          if (!Number.isFinite(estimate.quota) || !Number.isFinite(estimate.usage)) return true;""",
)

# Make module cards operable without mouse or drag-and-drop.
replace_once(
    APP,
    """        card.draggable = module.active;
        card.dataset.moduleId = module.id;""",
    """        card.draggable = module.active;
        card.tabIndex = 0;
        card.setAttribute("role", "button");
        card.setAttribute("aria-label", `${module.name}: ${module.active ? "aktiv, mit Enter öffnen" : "inaktiv, mit Enter aktivieren"}`);
        card.dataset.moduleId = module.id;""",
)
replace_once(
    APP,
    """        card.addEventListener("dblclick", () => {
          if (!module.active) setModuleActive(module.id, true);
          else placeModuleInFirstFreeCell(module.id);
        });

        card.addEventListener("dragstart", event => {""",
    """        const openModuleCard = () => {
          if (!module.active) setModuleActive(module.id, true);
          else placeModuleInFirstFreeCell(module.id);
        };
        card.addEventListener("dblclick", openModuleCard);
        card.addEventListener("keydown", event => {
          if (event.target !== card || !["Enter", " "].includes(event.key)) return;
          event.preventDefault();
          openModuleCard();
        });

        card.addEventListener("dragstart", event => {""",
)

# Add a focused static regression guard that requires no external dependency.
test = ROOT / "tests/test_hardening_guards.py"
test.write_text('''#!/usr/bin/env python3
"""Regression guards for manifest identity, import persistence and keyboard access."""
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "dashboard-studio-ultimate-pro-v3.1.0.html"
source = APP.read_text(encoding="utf-8")
checks = {
    "manifest identity is normalized": "manifestId: /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(manifestId)" in source,
    "loader does not match name alone": "item.manifestId === manifest.id || item.name === module.name" not in source,
    "pasted import uses UTF-8 bytes": "applyImportedState(parsed, importBytes)" in source,
    "import writes before state switch": source.index("storageService.writePrimary(serialized);") < source.index("state = importedState;"),
    "storage estimate accepts zero usage": "Number.isFinite(estimate.usage)" in source,
    "module cards expose keyboard access": "card.addEventListener(\"keydown\"" in source and "card.tabIndex = 0" in source,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("FEHLER: " + ", ".join(failed))
print(f"OK: {len(checks)} Hardening-Regressionspruefungen bestanden.")
''', encoding="utf-8")

# Keep the progress source consistent.
replace_once(ROOT / "README.md", "Entwicklungsfortschritt: 57 %", "Entwicklungsfortschritt: 59 %")
replace_once(ROOT / "todo.txt", "Fortschritt gesamt: 55 %", "Fortschritt gesamt: 59 %")
replace_once(
    ROOT / "todo.txt",
    "- Export- und Backup-Meldungen wurden strukturierter formuliert: Ereignis, Grund, Lösung und Speicherstatus werden nun bei den direkt betroffenen Hinweisen angezeigt.\n",
    "- Export- und Backup-Meldungen wurden strukturierter formuliert: Ereignis, Grund, Lösung und Speicherstatus werden nun bei den direkt betroffenen Hinweisen angezeigt.\n- Manifest-Identitäten bleiben nach Speichern, Backup und Import erhalten; gleichnamige eigene Module werden nicht mehr allein über ihren Namen zugeordnet.\n- Eingefügte JSON-Daten werden nach tatsächlicher UTF-8-Bytegröße geprüft und erst nach erfolgreicher direkter Speicherung in die laufende Oberfläche übernommen.\n- Modulkarten können per Tab fokussiert und mit Enter oder Leertaste aktiviert beziehungsweise geöffnet werden.\n- Sechs statische Hardening-Regressionsprüfungen sichern diese Daten- und Tastaturpfade ab.\n",
)
replace_once(
    ROOT / "todo.txt",
    "- Vor großen Importen prüfen, ob Browser-Speicherplatz ausreicht, damit ein Import nicht erst beim späteren Speichern scheitert.\n",
    "- Erledigt: Vor großen Importen wird verfügbarer Browser-Speicher geprüft; der normalisierte Import wird vor dem UI-Wechsel direkt gespeichert.\n",
)

# Required useful text block per category for this iteration.
quick = ROOT / "modules/schnell-text-speicher/README.md"
text = quick.read_text(encoding="utf-8")
additions = {
    "### Coding": "\nSichere Importlogik transaktional ab: erst Eingabe und Bytegröße prüfen, dann Backup erstellen, danach vollständig speichern und erst bei Erfolg den sichtbaren Zustand wechseln.\n",
    "### Prompting": "\nBitte suche gezielt nach Identitätsverlusten beim Speichern und Laden: Welche stabilen Schlüssel müssen erhalten bleiben, welche Fallback-Zuordnung ist vertretbar und welche Namensvergleiche könnten fremde Daten treffen?\n",
    "### Vibecoding": "\nOptimiere nicht nach Eindruck, sondern nach Schadenspotenzial: Datenverlust und falsche Zuordnung zuerst, Tastaturzugang danach, kosmetische Details zuletzt.\n",
    "### KI-Bildgenerierung": "\nErzeuge ein technisches Sicherheitsmotiv für einen Datenimport: zwei klar getrennte Zustände, links geprüfte Datei und Backup, rechts erfolgreich gespeichertes Dashboard, deutliche Flussrichtung, dunkle Oberfläche, keine Warnpanik.\n",
    "### KI-Musikgenerierung": "\nErstelle einen präzisen 60-Sekunden-Hardtechno-Loop für einen sicheren Systemwechsel: kontrollierter Aufbau, kurzer Prüfimpuls, trockener Bestätigungs-Drop, 155 BPM, keine Vocals, sauberer Endpunkt.\n",
    "### KI-Contentcreation": "\nFormuliere eine technische Nutzerinfo zu einem sicheren Import: Daten werden geprüft, vorher gesichert, vollständig gespeichert und erst danach sichtbar übernommen; bei einem Fehler bleibt der bisherige Stand aktiv.\n",
}
headings = list(additions)
for index, heading in enumerate(headings):
    start = text.index(heading) + len(heading)
    end = text.find("\n### ", start)
    if end < 0:
        end = len(text)
    text = text[:end].rstrip() + additions[heading] + "\n" + text[end:].lstrip("\n")
quick.write_text(text.rstrip() + "\n", encoding="utf-8")

print("Hardening iteration applied.")
