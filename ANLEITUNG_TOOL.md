# ANLEITUNG_TOOL

## 1. Zweck des aktuellen Stands

Der aktuelle Stand ist ein startbares Linux-Desktop-Grundgerüst mit geführter Ersteinrichtung. Echte Dateioperationen sind weiterhin deaktiviert.

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

Ampel: **GRÜN** bereit, **GELB** Hinweis oder unvollständig, **ROT** sicherheitsrelevante Blockade.

## 5. Bestätigungen

Maximal zwei bestätigende Schritte können nötig sein:

1. fehlende Ubuntu-Systempakete installieren,
2. lokale Projektumgebung `.venv` erstellen.

Vor jeder Bestätigung werden Befehle und Auswirkungen angezeigt. Abbrechen lässt bestehende Projektdaten unverändert.

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

Ausdrücklich bestätigter Lauf:

```bash
./setup.sh --yes --no-gui-dialogs
```

## 7. Sicherheitsprinzip der `.venv`

Die neue Umgebung wird zunächst als `.venv.setup-...` erstellt. Danach werden pip und `requirements.txt` installiert und PySide6 importiert. Erst bei grünem Ergebnis wird sie als `.venv` aktiviert. Eine bestehende `.venv` wird nicht vorher gelöscht. Symbolische Links an `.venv` werden blockiert.

## 8. Typische Fehler

### Python fehlt

Unter Ubuntu/Kubuntu bietet der Assistent nach Bestätigung an:

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

## 9. Diagnose und Tests

```bash
python3 -m src.main --validate-only
python3 tools/validate_repository.py
python3 -m unittest discover -s tests -v
```

## 10. GitHub-Rechte

GitHub-Schreibrechte werden nicht im Projekt gespeichert. Keine Tokens in Dateien eintragen. Der aktuelle Zugriffsvertrag steht in `docs/GITHUB_ZUGRIFF.md`.

## 11. Aktuelle Grenze

Noch keine privaten oder unersetzlichen Dateibestände bearbeiten. Produktive Dateiaktionen folgen erst nach XDG-Pfaden, Einstellungen mit Rollback, Fehlerzentrale, Papierkorb, Undo und Abbruchschutz.
