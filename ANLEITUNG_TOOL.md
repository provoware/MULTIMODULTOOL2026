# ANLEITUNG_TOOL

## 1. Zweck des aktuellen Stands

Der aktuelle Stand ist ein startbares Linux-Desktop-Grundgerüst mit geführter Ersteinrichtung, sicherer XDG-Speichertrennung und workflow-fokussierter Oberfläche. Echte Dateioperationen sind weiterhin deaktiviert.

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

Die Startroutine prüft die lokale Umgebung. Fehlt etwas, öffnet sie automatisch den Einrichtungsassistenten.

## 4. Was der Assistent prüft

- Linux-Betriebssystem
- Python-Version
- Modul `python3-venv`
- KDE-Plasma-Sitzung
- X11 oder Wayland
- Schreibrecht im Projektordner
- lokale `.venv`
- PySide6

Ampel:

- **GRÜN:** bereit
- **GELB:** noch nicht eingerichtet oder nur Hinweis
- **ROT:** sicherheitsrelevante Blockade

## 5. Bestätigungen

Maximal zwei bestätigende Schritte können nötig sein:

1. fehlende Ubuntu-Systempakete installieren,
2. lokale Projektumgebung `.venv` erstellen.

Vor jeder Bestätigung werden die exakten Befehle und Auswirkungen angezeigt. Abbrechen lässt bestehende Projektdaten unverändert.

## 6. Sichere Einrichtung

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

Automatischer ausdrücklich bestätigter Lauf:

```bash
./setup.sh --yes --no-gui-dialogs
```

`--yes` sollte nur verwendet werden, wenn die angezeigten Installationsschritte vorher verstanden wurden.

## 7. Sicherheitsprinzip der `.venv`

Die neue Umgebung wird zunächst als `.venv.setup-...` erstellt. Danach:

1. pip wird aktualisiert,
2. `requirements.txt` wird installiert,
3. PySide6 wird importiert,
4. erst bei grünem Ergebnis wird die Umgebung als `.venv` aktiviert.

Eine bestehende `.venv` wird nicht vorher gelöscht. Symbolische Links an `.venv` werden blockiert.

## 8. Sichere Speicherorte

Beim normalen Start legt das Tool seine privaten Linux-Benutzerbereiche außerhalb des Programmordners an:

- Konfiguration: `~/.config/multimodultool2026`
- Nutzerdaten: `~/.local/share/multimodultool2026`
- Cache: `~/.cache/multimodultool2026`
- Status: `~/.local/state/multimodultool2026`
- Protokolle: `~/.local/state/multimodultool2026/logs`
- Sicherungen: `~/.local/share/multimodultool2026/backups`

Alle App-Verzeichnisse erhalten Modus `0700`. Vor und nach der Anlage werden absolute Pfade, zulässige Grenzen, Symlinks, Dateitypen, Schreibrechte und eine temporäre Schreibprobe geprüft.

Nur berechnete Pfade anzeigen:

```bash
python3 -m src.main --paths-only
```

Rein lesend prüfen, ohne Verzeichnisse anzulegen:

```bash
python3 -m src.main --validate-only
```

### XDG-Pfadfehler

**Ursache:** Ein XDG-Wert ist relativ, zeigt in den Programmordner, verwendet einen blockierten Symlink, ist doppelt belegt oder nicht beschreibbar.  
**Folge:** Die Oberfläche startet nicht.  
**Datenstand:** Es werden keine produktiven Dateien verändert. Temporäre Schreibtests werden sofort entfernt.  
**Lösung:** Genannten Pfad korrigieren oder die betreffende `XDG_*_HOME`-Variable auf einen absoluten, eigenen Linux-Benutzerpfad setzen.

## 9. Typische Fehler

### Python fehlt

Der Assistent bietet unter Ubuntu/Kubuntu nach Bestätigung an:

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip
```

### Schreibrecht fehlt

Projekt in einen eigenen beschreibbaren Ordner verschieben. Nicht mit `sudo ./start.sh` starten.

### KDE oder X11/Wayland nicht erkannt

Dies ist zunächst eine gelbe Warnung. Der Zielrahmen bleibt KDE Plasma unter X11 oder Wayland.

### PySide6-Download scheitert

Internetverbindung prüfen und `./setup.sh` erneut ausführen. Eine unvollständige temporäre Umgebung wird entfernt.

## 10. Diagnose und Tests

```bash
python3 -m src.main --validate-only
python3 tools/validate_repository.py
python3 -m unittest discover -s tests -v
```

## 11. GitHub-Rechte

GitHub-Schreibrechte werden nicht im Projekt gespeichert. Keine Tokens in Dateien eintragen. Der aktuelle Zugriffsvertrag steht in `docs/GITHUB_ZUGRIFF.md`.

## 12. Aktuelle Grenze

Noch keine privaten oder unersetzlichen Dateibestände bearbeiten. Die XDG-Pfade sind gesichert; produktive Dateiaktionen folgen erst nach transaktionalen Einstellungen, Fehlerzentrale, Papierkorb, Undo und Abbruchschutz.
