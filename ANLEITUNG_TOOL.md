# ANLEITUNG_TOOL

## 1. Zweck des aktuellen Stands

MULTIMODULTOOL2026 ist aktuell ein startbares Linux-Desktop-Grundgerüst mit:

- geführter Ersteinrichtung,
- sicherer XDG-Speichertrennung,
- versionierten, transaktionalen Einstellungen,
- sichtbaren Sicherheitszuständen,
- automatischem Qt-Offscreen-GUI-Smoke-Test.

Produktive Dateioperationen bleiben deaktiviert, bis Fehlerzentrale, Papierkorb, Undo und Abbruchschutz vollständig umgesetzt sind.

## 2. Unterstützte Systeme

- Kubuntu 22.04 LTS, x86-64
- Kubuntu 24.04 LTS, x86-64
- KDE Plasma unter X11 oder Wayland
- Python 3.10 oder neuer

Nicht unterstützt: Windows, macOS, Android, iOS, Browser und PWA.

## 3. Einfachster Start

```bash
chmod +x start.sh setup.sh
./start.sh
```

Fehlen Python-Komponenten, `.venv` oder PySide6, startet der geführte Einrichtungsassistent.

## 4. Sichere Einrichtung

```bash
./setup.sh
```

Nur prüfen:

```bash
./setup.sh --check-only
```

Terminal statt KDialog:

```bash
./setup.sh --no-gui-dialogs
```

Ausdrücklich bestätigter nichtinteraktiver Lauf:

```bash
./setup.sh --yes --no-gui-dialogs
```

Der Assistent prüft Linux, Python, `venv`, KDE, X11/Wayland, Schreibrechte, `.venv` und PySide6. Die neue Umgebung wird zunächst unter `.venv.setup-*` aufgebaut, geprüft und erst danach aktiviert.

## 5. Sichere Speicherorte

Beim normalen Start werden private App-Verzeichnisse außerhalb des Programmordners verwendet:

- Konfiguration: `~/.config/multimodultool2026`
- Nutzerdaten: `~/.local/share/multimodultool2026`
- Cache: `~/.cache/multimodultool2026`
- Status: `~/.local/state/multimodultool2026`
- Logs: `~/.local/state/multimodultool2026/logs`
- Sicherungen: `~/.local/share/multimodultool2026/backups`

App-Verzeichnisse erhalten Modus `0700`. Relative Pfade, Ziele im Quellbaum, Symlinks, doppelte Ziele und unbeschreibbare Ziele blockieren den Start.

Pfade rein lesend anzeigen:

```bash
python3 -m src.main --paths-only
```

## 6. Versionierte Einstellungen

Aktive Einstellungen:

```text
~/.config/multimodultool2026/settings.json
```

Letzte gültige Sicherung:

```text
~/.config/multimodultool2026/settings.last-valid.json
```

Beide Dateien verwenden Modus `0600`.

Vor jedem Speichern werden geprüft:

1. `schemaVersion`,
2. erlaubte Felder,
3. Datentypen,
4. Wertebereiche,
5. unveränderliche Sicherheitswerte,
6. Dateipfad und Symlinkfreiheit,
7. private Dateirechte.

Danach wird in eine temporäre Datei geschrieben, mit `fsync` bestätigt, erneut validiert und atomar mit `os.replace` aktiviert.

## 7. Automatische Wiederherstellung

Ist `settings.json` beschädigt oder inkompatibel:

1. die defekte Datei wird lokal als `settings.corrupt-<UTC-Zeit>.json` isoliert,
2. `settings.last-valid.json` wird geprüft,
3. eine gültige Sicherung wird atomar wiederhergestellt,
4. ohne gültige Sicherung werden sichere Standardwerte angelegt.

Die Meldung nennt Ursache, verwendete Quelle und unveränderten Datenstand. Es werden keine Einstellungen auf GitHub übertragen.

## 8. Rein lesende Diagnose

Gesamten Startvertrag prüfen:

```bash
python3 -m src.main --validate-only
```

Nur Einstellungen und möglichen Recovery-Weg prüfen:

```bash
python3 -m src.main --settings-only
```

Diese Modi dürfen keine Verzeichnisse oder Dateien anlegen, verändern, umbenennen oder löschen.

## 9. Typische Fehler

### Einstellungsdatei enthält unbekannte Version

**Ursache:** `schemaVersion` wird von dieser Programmversion nicht unterstützt.  
**Folge:** Die Datei wird nicht interpretiert.  
**Datenstand:** Produktive Dateien bleiben unverändert.  
**Lösung:** Gültige Sicherung verwenden oder eine geprüfte Migration durchführen.

### Einstellungsdatei ist beschädigt

**Ursache:** unvollständiges oder ungültiges JSON.  
**Folge:** Der normale Start isoliert die Datei und führt Rollback aus.  
**Datenstand:** Keine privaten Dateibestände werden verändert.

### Symlink oder zu offene Rechte

**Ursache:** Einstellungsdatei ist ein Symlink oder besitzt Gruppen-/Weltzugriff.  
**Folge:** Start wird aus Sicherheitsgründen blockiert.  
**Lösung:** reguläre Datei im XDG-Konfigurationsordner mit Modus `0600` verwenden.

### PySide6-Download scheitert

Internetverbindung prüfen und `./setup.sh` erneut ausführen. Die unvollständige temporäre Umgebung wird entfernt.

## 10. Tests

```bash
python3 tools/validate_repository.py
python3 -m unittest discover -s tests -v
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_gui_offscreen -v
```

GitHub Actions installiert PySide6 und prüft automatisiert:

- alle neun Layoutzonen,
- Scrollbarkeit,
- sichtbare Sicherheitsmeldungen,
- gesperrte Aktionen,
- keine Dateianlage allein durch den Fensteraufbau.

## 11. Sicherheitsgrenze

Noch keine privaten oder unersetzlichen Dateibestände bearbeiten. Die XDG- und Einstellungsbasis ist gesichert; produktive Funktionen folgen erst nach P0-004 bis P0-008.

## 12. Verbindliche Dokumente

- `docs/XDG_PFADVERTRAG.md`
- `docs/EINSTELLUNGSVERTRAG.md`
- `standards/settings-schema-v1.json`
- `AGENTS.md`
