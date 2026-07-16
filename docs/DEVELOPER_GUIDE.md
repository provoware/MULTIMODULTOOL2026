# Entwicklerdokumentation

Stand: 2026-07-16

## Zielbild

MULTIMODULTOOL2026 bleibt kurzfristig eine lokal nutzbare Single-File-HTML-App. Neue Strukturdateien bereiten nur sichere Schritte in Richtung manifestbasierter Module vor.

## Lokaler Start

Empfohlen:

```sh
./scripts/start-local.sh
```

Alternativ kann `dashboard-studio-ultimate-pro-v3.1.0.html` direkt im Browser geöffnet werden. Das ist nur ein eingeschränkter Rückfall, weil Browser beim Datei-Start ausgelagerte Manifest-, Modul- und Startdaten-Dateien blockieren können. Es gibt keinen Build-Schritt und keine Paketinstallation.

## Entwicklungsorganisation

1. Änderung klein planen: Ziel, Dateien, Blöcke, Grund, Risiko und Nicht-Ziele notieren.
2. Nur betroffene Stellen ändern.
3. Keine neuen Abhängigkeiten einführen, wenn die Aufgabe auch mit Browser- oder Standardshell-Mitteln lösbar ist.
4. Nach Änderungen nur passende Prüfungen ausführen.
5. Offene Folgearbeiten in `todo.txt` dokumentieren.

## Struktur

- `dashboard-studio-ultimate-pro-v3.1.0.html`: aktueller lauffähiger Einstiegspunkt.
- `manifests/`: App-Manifest, Modul-Schema und Beispiele.
- `modules/`: künftige Modulordner. Jeder echte Modulordner braucht ein Manifest.
- `modules/systemmodule-buendel/`: Übergangsbeschreibung für vorhandene Systemmodule.
- `scripts/`: kleine lokale Hilfsskripte ohne Build-System.
- `tests/`: gezielte Prüfungen für Manifestvalidierung, Startweg, Hilfslogik, Modul-Previews und Performance-Hotspots.

## Barrierefreiheit: aktueller Stand und Verbesserungsfelder

- Modale Fenster setzen beim Öffnen einen sichtbaren Fokus und geben ihn beim Schließen an den Auslöser zurück.
- Das 3-mal-3-Arbeitsraster unterstützt Tastaturbedienung: aktive Module lassen sich einblenden und platzierte Module mit Pfeiltasten, Pos1 und Ende verschieben.
- Schalter und Menüknöpfe sollten durchgängig `aria-expanded`, `aria-controls` und klare Zustände setzen.
- Statusmeldungen sollten wichtige Speicher-, Import- und Fehlerereignisse zusätzlich über die Live-Region melden.
- Farbige Modulkennzeichnungen sollten immer durch Text ergänzt bleiben, damit Farbe nie die einzige Information ist.

## Geplante Modul-Loader-Schritte

1. Loader-Konzept dokumentieren: Manifestpfade lesen, Pflichtfelder prüfen und ungültige Module verständlich ablehnen.
2. Systemmodule-Bündel als erste Testgruppe verwenden, ohne bestehende HTML-Laufzeit zu brechen.
3. Erst danach kleine, unabhängige Systembereiche in echte `module.html`, `module.css` oder `module.js` Dateien auslagern.

## Effizienzregeln

- Wiederholte Modulsuchen in Renderpfaden bei Bedarf über eine Map bündeln.
- Timer- und Autosave-Schreibvorgänge drosseln.
- Große Listen wie Aktivitätsprotokoll und Debugging begrenzen oder später seitenweise anzeigen.
- Dokumentation nur bei echter Struktur- oder Verhaltensänderung erweitern.

## Relevante Prüfungen

Nur direkt betroffene Prüfungen ausführen. Häufige Einzelprüfungen sind:

```sh
python3 tests/validate_module_manifests.py
python3 tests/validate_progress_consistency.py
python3 tests/validate_module_previews.py
python3 tests/test_start_local.py
python3 -m json.tool manifests/MULTIMODULTOOL2026_02_AppManifest.json >/dev/null
```
