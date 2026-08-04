# ENTWICKLERDOKU

## 1. Technischer Stand

- ausschließlich Linux-Desktop
- Kubuntu 22.04/24.04, KDE Plasma, X11/Wayland, x86-64
- Python 3.10+
- PySide6 / Qt Widgets
- Standardbibliothek für Setup, Manifest, XDG, Einstellungen und Repository-Prüfung
- Start: `./start.sh`
- Einrichtung: `./setup.sh`
- Einstellungsformat: `schemaVersion` 1

## 2. Startfluss

```text
start.sh
  ├─ Linux, Python, .venv und PySide6 prüfen
  ├─ bei Bedarf setup.sh / tools/setup_assistant.py
  ├─ python -m src.main --validate-only
  │    ├─ Linux-Plattform prüfen
  │    ├─ layout-manifest.json prüfen
  │    ├─ XDG-Pfadplan rein lesend prüfen
  │    └─ Einstellungen und Recovery-Möglichkeit rein lesend prüfen
  └─ python -m src.main
       ├─ XDG-Verzeichnisse vor-/nachvalidieren und mit 0700 vorbereiten
       ├─ settings.json laden
       ├─ bei Defekt Backup oder Standardwerte atomar aktivieren
       └─ Qt-Oberfläche mit Z01–Z09 starten
```

## 3. Einstellungsarchitektur

### Dateien

| Datei | Aufgabe |
|---|---|
| `src/settings_manager.py` | Validierung, Lesen, atomarer Schreibweg, Sicherung, Quarantäne und Recovery |
| `standards/settings-schema-v1.json` | maschinenlesbarer Strukturvertrag |
| `docs/EINSTELLUNGSVERTRAG.md` | Sicherheits- und Betriebsvertrag |
| `tests/test_settings_manager.py` | 15 transaktionale Regressionstests |

### Datenmodell

```json
{
  "schemaVersion": 1,
  "ui": {
    "theme": "dark",
    "fontScalePercent": 100,
    "showTooltips": true
  },
  "safety": {
    "defaultDryRun": true,
    "confirmDestructiveActions": true
  },
  "workflow": {
    "startArea": "start",
    "showAdvancedOptions": false
  }
}
```

Unbekannte Felder sind verboten. Sicherheitswerte `defaultDryRun` und `confirmDestructiveActions` müssen im aktuellen Entwicklungsstand `true` bleiben.

## 4. Transaktionaler Schreibalgorithmus

1. Python-Datenmodell vollständig validieren.
2. XDG-Konfigurationspfad und Zieldateien prüfen.
3. Temporäre Datei im selben Verzeichnis mit `0600` erzeugen.
4. vollständiges JSON schreiben und Dateideskriptor mit `fsync` bestätigen.
5. temporäre Datei erneut einlesen und validieren.
6. aktive gültige Datei atomar als `settings.last-valid.json` sichern.
7. temporäre Datei per `os.replace` aktivieren.
8. aktive Datei und Verzeichnis nachvalidieren und mit `fsync` bestätigen.
9. bei Fehler temporäre Reste entfernen und vorhandene aktive Datei erhalten.
10. schlägt eine Nachvalidierung nach Austausch fehl, Rollback aus Sicherung ausführen.

## 5. Recovery

```text
settings.json gültig
  └─ normal laden

settings.json beschädigt
  ├─ als settings.corrupt-<UTC>.json isolieren
  ├─ settings.last-valid.json prüfen
  ├─ gültig: atomar wiederherstellen
  └─ ungültig/fehlend: sichere Standardwerte atomar schreiben
```

Rein lesende Modi melden den geplanten Recovery-Weg, führen ihn aber nicht aus.

## 6. GUI-Zonenvertrag

`src.main.ZONE_OBJECT_NAMES` enthält exakt:

1. `header`
2. `navigation`
3. `summaryCards`
4. `primaryActionTiles`
5. `workflowPanel`
6. `workspaceScroll`
7. `contextRail`
8. `actionBar`
9. `footer`

Jede Zone besitzt zusätzlich `zoneId` von `Z01` bis `Z09`.

## 7. Offscreen-GUI-Smoke-Test

`tests/test_gui_offscreen.py` verwendet `QT_QPA_PLATFORM=offscreen` und prüft:

- neun vorhandene und sichtbare Zonen,
- korrekte Zonen-IDs,
- scrollbaren Haupt- und Kontextbereich,
- textuell sichtbare Sicherheitszustände,
- sechs deaktivierte Hauptaktionen mit Tooltip,
- keine Anlage der übergebenen Nutzerdatenpfade.

GitHub Actions installiert PySide6 erst nach den Standardbibliotheksprüfungen und führt den Test separat aus.

## 8. Rückgabecodes von `src.main`

- `0`: Prüfung erfolgreich oder GUI regulär beendet
- `2`: Manifest ungültig
- `3`: PySide6 fehlt
- `4`: Nicht-Linux-System
- `5`: XDG-Pfadprüfung blockiert
- `6`: Einstellungsprüfung oder Recovery blockiert

## 9. Lokale Prüfungen

```bash
python3 -m src.main --validate-only
python3 -m src.main --settings-only
python3 tools/validate_repository.py
python3 -m unittest tests.test_settings_manager -v
python3 -m unittest discover -s tests -v
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_gui_offscreen -v
python3 -m py_compile src/main.py src/settings_manager.py tests/test_settings_manager.py tests/test_gui_offscreen.py
```

## 10. Sicherheitsregeln

- keine Einstellungen, Logs oder Nutzerdaten im Quellbaum
- keine Symlinks für App-Konfigurationsdateien
- keine unbekannten Felder oder stillen Versionsannahmen
- keine Passwörter, Tokens oder privaten Schlüssel in Einstellungen
- keine produktive Dateiaktion ohne Vorschau und Recovery-Pfad
- Geschäftslogik bleibt von Widgets getrennt
- Prüfmodi bleiben ohne PySide6 und ohne Schreibzugriff nutzbar

## 11. Nächste Architekturgrenze

P0-004 führt einen globalen Fehlerdialog und ein zentrales Ereignismodell ein. Er muss Einstellungs-Recovery, XDG-Fehler und unerwartete GUI-Ausnahmen in einfacher Sprache mit Ursache, Folge, Lösung und unverändertem Datenstand darstellen.
