# ANLEITUNG_TOOL

## 1. Aktueller Zweck

Der aktuelle Stand ist ein startbares Linux-Desktop-Grundgerüst. Er zeigt die geplante Oberfläche und prüft beim Start automatisch Betriebssystem und verbindlichen Layoutvertrag. Echte Dateioperationen sind bewusst noch nicht freigeschaltet.

## 2. Unterstützte Systeme

Primär vorgesehen:

- Kubuntu 22.04 LTS, x86-64
- Kubuntu 24.04 LTS, x86-64
- KDE Plasma unter X11 oder Wayland

Nicht unterstützt:

- Windows
- macOS
- Android
- iOS
- Browser oder PWA

Auf Nicht-Linux-Systemen wird der Start verständlich blockiert. Es werden keine Daten verändert.

## 3. Voraussetzungen unter Kubuntu

- Python 3.10 oder neuer
- Internetzugang nur für die einmalige Installation von PySide6
- Schreibrecht im Projektordner für die lokale virtuelle Python-Umgebung

Prüfen:

```bash
python3 --version
```

Fehlen Python-Werkzeuge:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

## 4. Empfohlener Start

Im Projektordner:

```bash
chmod +x start.sh
./start.sh
```

Die Startroutine zeigt verständliche Ampelmeldungen:

- **GRÜN:** Prüfung erfolgreich
- **GELB:** Einrichtung fehlt, Daten wurden nicht verändert
- **ROT:** Start blockiert, konkrete Lösung wird angezeigt

## 5. Einmalige Einrichtung von PySide6

Falls die Startroutine PySide6 vermisst:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
./start.sh
```

Die virtuelle Umgebung `.venv` bleibt lokal und wird nicht auf GitHub übertragen.

## 6. Nur prüfen, ohne Oberfläche zu starten

```bash
python3 -m src.main --validate-only
```

Vollständigen Repository-Vertrag prüfen:

```bash
python3 tools/validate_repository.py
```

Tests:

```bash
python3 -m unittest discover -s tests -v
```

## 7. Oberfläche verstehen

- Links: Hauptnavigation
- Oben: Projekt-, Layout- und Sicherheitsstatus
- Große Kacheln: spätere Hauptfunktionen
- Mitte: geführter Arbeitsablauf aus Auswahl, Vorschau und Ergebnis
- Rechts: Hilfe und Diagnose
- Unten: Rückfall-, Hauptaktions- und Sicherheitsstatus

Die Kacheln sind im Grundgerüst noch Demonstrationselemente. Sie verändern keine Dateien.

## 8. Typische Fehlermeldungen

### „Nur Linux unterstützt“

Ursache: Der Start wurde auf einem Nicht-Linux-System versucht.  
Folge: Die Oberfläche startet nicht.  
Datenstand: Unverändert.  
Lösung: Das Projekt unter einem unterstützten Linux-Desktop-System ausführen.

### „PySide6 fehlt“

Ursache: Die grafische Bibliothek ist noch nicht in `.venv` installiert.  
Folge: Die Oberfläche startet nicht.  
Datenstand: Unverändert.  
Lösung: Befehle aus Abschnitt 5 ausführen.

### „Manifest ungültig“

Ursache: `layout-manifest.json`, seine Zonen, der Linux-Plattformvertrag oder die Referenzdatei sind unvollständig.  
Folge: Der Start wird aus Sicherheitsgründen blockiert.  
Datenstand: Unverändert.  
Lösung: `python3 tools/validate_repository.py` ausführen und die genannten Punkte beheben.

### Datei nicht ausführbar

```bash
chmod +x start.sh
./start.sh
```

## 9. Sicherer aktueller Umgang

Noch keine privaten oder unersetzlichen Dateibestände mit diesem Entwicklungsstand bearbeiten. Produktive Dateiaktionen werden erst freigegeben, wenn Linux-Pfade, Vorschau, Backup, Papierkorb, Undo, Abbruchschutz und Ergebnisprüfung vollständig implementiert und getestet sind.
