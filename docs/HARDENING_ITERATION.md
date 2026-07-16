# Hardening-Iteration: Manifest, Import und Tastatur

## Ziel

Diese Iteration behebt drei konkrete Risiken der Single-File-App, ohne Build-System, Framework oder Datenformat einzuführen:

1. Manifest-Module behalten ihre stabile `manifestId` nach Speichern, Backup und Import.
2. JSON-Importe werden anhand ihrer tatsächlichen UTF-8-Bytegröße geprüft und vor dem sichtbaren Zustandswechsel direkt gespeichert.
3. Modulkarten werden per Tab, Enter und Leertaste bedienbar.

## Erkannte Ursachen

- `normalizeState()` übernahm `manifestId` nicht. Nach einem Neustart konnte der Loader deshalb nur noch über den Namen zuordnen.
- Der Textimport prüfte zwar `Blob.size`, übergab anschließend aber `value.length`; Umlaute und andere Mehrbyte-Zeichen wurden dadurch unterschätzt.
- Der importierte Zustand wurde sichtbar gesetzt, bevor die verzögerte Speicherung sicher abgeschlossen war.
- Modulkarten waren für Maus und Drag-and-drop vorbereitet, aber nicht als fokussierbare Tastaturziele.

## Anwendung

Vom Projektwurzelordner:

```sh
python3 scripts/apply_hardening_iteration.py
python3 tests/validate_module_manifests.py
python3 tests/test_html_helpers.py
python3 tests/test_hardening_guards.py
```

Danach die eingebettete JavaScript-Syntax prüfen:

```sh
python3 - <<'PY'
from pathlib import Path
source = Path('dashboard-studio-ultimate-pro-v3.1.0.html').read_text(encoding='utf-8')
script = source.rsplit('<script>', 1)[1].split('</script>', 1)[0]
Path('/tmp/dashboard-app.js').write_text(script, encoding='utf-8')
PY
node --check /tmp/dashboard-app.js
```

Der Patch bricht sofort ab, wenn ein erwarteter Quellblock fehlt oder mehrfach vorkommt. Dadurch wird kein unbekannter Dateistand blind verändert.

## Abnahme im Browser

- App über `./scripts/start-local.sh` öffnen.
- Manifest-Module zweimal laden, neu starten und erneut laden; es dürfen keine Namenskollisionen oder unnötigen Duplikate entstehen.
- Einen JSON-Export mit Umlauten importieren und danach neu laden.
- Einen absichtlich zu großen Import ablehnen lassen; der bisherige Zustand muss aktiv bleiben.
- Mit Tab eine Modulkarte fokussieren und mit Enter beziehungsweise Leertaste aktivieren oder öffnen.

## Bewusste Grenzen

- Keine optische Massenänderung.
- Keine Änderung des Schemas oder Exportformats.
- Keine automatische Freigabe ohne echte Browserprüfung.
- Das Patchskript ist ein einmaliges, überprüfbares Migrationswerkzeug und soll nach erfolgreicher Anwendung aus dem endgültigen Commit entfernt werden.
