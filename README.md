# MULTIMODULTOOL2026

> **Entwicklungsfortschritt: 27 %**  
> **Erledigte Punkte: 17**  
> **Offene Punkte: 45**  
> **Gesamtpunkte: 62**  
> **Aktuelle Phase:** startbares Linux-Desktop-Grundgerüst und verbindlicher Projektvertrag  
> **Letzte Fortschrittsprüfung:** 2026-08-04

> **Plattformvertrag:** Dieses Projekt wird ausschließlich für Linux-Desktop-Systeme entwickelt. Primäre Zielsysteme sind Kubuntu 22.04 LTS und Kubuntu 24.04 LTS. Windows, macOS, Android und iOS gehören nicht zum Entwicklungs-, Test- oder Releaseumfang.

MULTIMODULTOOL2026 ist ein lokal arbeitendes Linux-Desktop-Werkzeug zur sicheren Analyse, Organisation, Benennung und Wiederauffindbarkeit großer Dateisammlungen. Die Bedienung soll auch ohne Fachkenntnisse durch Kacheln, Auswahlfenster, Vorschauen, Ampelstatus und klare Rückfallwege funktionieren.

## Aktuell startbarer Stand

Das Repository enthält ein minimales PySide6-Grundgerüst, das alle neun verbindlichen Layoutzonen sichtbar abbildet:

1. Kopfbereich
2. linke Hauptnavigation
3. obere Übersichtskarten
4. primäre Funktionskacheln
5. Prozess- und Fortschrittsanzeige
6. zentraler Arbeitsbereich
7. rechte Kontext- und Diagnoseleiste
8. Aktions- und Statusleiste
9. abschließender Sicherheitsstatus

Vor jedem grafischen Start werden Linux-Plattform und `layout-manifest.json` automatisch geprüft. Auf Nicht-Linux-Systemen oder bei einem ungültigen Manifest startet die Oberfläche nicht und es werden keine Projektdaten verändert.

## Schnellstart unter Kubuntu

```bash
chmod +x start.sh
./start.sh
```

Fehlt PySide6, zeigt die Startroutine die einmalig erforderlichen Befehle. Eine manuelle Installation ist ebenfalls möglich:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
./start.sh
```

Nur den Projektvertrag prüfen:

```bash
python3 -m src.main --validate-only
python3 tools/validate_repository.py
python3 -m unittest discover -s tests -v
```

## Linux-Zielumfang

Unterstützt und verpflichtend zu testen:

- Kubuntu 22.04 LTS, x86-64
- Kubuntu 24.04 LTS, x86-64
- KDE Plasma unter X11 und Wayland
- übliche Linux-Fenstergrößen von 1024 × 680 bis 4K
- lokale Dateisysteme und eingehängte Linux-Datenträger

Nicht Teil des Projekts:

- Windows-Installer oder Windows-spezifische Pfade
- macOS-App-Bundles
- Android- oder iOS-Versionen
- Browser-, PWA- oder Web-App-Ausgabe
- plattformübergreifende Kompatibilitätsschichten ohne ausdrückliche spätere Freigabe

## Visuelle Leitvorlage

![Visuelle Layout- und Orientierungsvorlage](assets/ui-reference/multimodultool2026-ui-layout-reference-2026.webp)

Die Abbildung bleibt die primäre grafische Orientierung. Projektname, Texte, Icons, Farben, Funktionen und Kachelinhalte dürfen angepasst werden. Grundaufbau, Zonenfolge und räumliche Logik bleiben bestehen, solange keine ausdrückliche Änderung verlangt wird.

Verbindliche Quellen:

- [`docs/UI_BASISVORLAGE.md`](docs/UI_BASISVORLAGE.md)
- [`standards/UI_LAYOUT_STANDARD_2026.md`](standards/UI_LAYOUT_STANDARD_2026.md)
- [`layout-manifest.json`](layout-manifest.json)
- [`AGENTS.md`](AGENTS.md)

## Automatische Prüfung bei jedem Commit

Der Workflow `.github/workflows/repository-contract.yml` läuft auf Ubuntu bei jedem Push und Pull Request. Er prüft:

- Linux-Plattformvertrag
- Pflichtdateien und Dokumentationsvertrag
- neun Layoutzonen und deren Reihenfolge
- Referenzbild und Manifest
- Übereinstimmung der Fortschrittswerte mit `TODO.md`
- Python-Syntax und Unit-Tests
- Manifestprüfung im startfreien Modus

## Pflichtdokumente

| Datei | Zweck |
|---|---|
| [`CHANGELOG.md`](CHANGELOG.md) | nachvollziehbare Änderungen je Iteration |
| [`ANLEITUNG_TOOL.md`](ANLEITUNG_TOOL.md) | Installation und Bedienung für Linux-Nutzer |
| [`TODO.md`](TODO.md) | priorisierte, prüfbare Entwicklungsaufgaben |
| [`SCHWACHSTELLEN.md`](SCHWACHSTELLEN.md) | bekannte Risiken, Grenzen und Gegenmaßnahmen |
| [`UPGRADE_POOL.md`](UPGRADE_POOL.md) | bewertete Linux-Erweiterungsideen außerhalb des Pflichtumfangs |
| [`ENTWICKLERDOKU.md`](ENTWICKLERDOKU.md) | Architektur, Startfluss, Prüfungen und Entwicklungsregeln |

## Projektstruktur

```text
/
├── .github/workflows/repository-contract.yml
├── AGENTS.md
├── ANLEITUNG_TOOL.md
├── CHANGELOG.md
├── ENTWICKLERDOKU.md
├── README.md
├── SCHWACHSTELLEN.md
├── TODO.md
├── UPGRADE_POOL.md
├── layout-manifest.json
├── requirements.txt
├── start.sh
├── assets/ui-reference/
├── docs/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── manifest_validator.py
│   └── theme.qss
├── standards/
├── tests/
└── tools/
```

## Aktuelle Grenze

Das Grundgerüst zeigt Navigation, Status, Kacheln und Arbeitsbereiche, führt aber noch keine echten Dateioperationen aus. Produktive Funktionen folgen erst nach sicherer Linux-Datenpfad-, Backup-, Papierkorb-, Undo- und Fehlerarchitektur. Der verbindliche Arbeitsplan steht in [`TODO.md`](TODO.md).
