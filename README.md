# MULTIMODULTOOL2026

> **Entwicklungsfortschritt: 29 %**  
> **Erledigte Punkte: 18**  
> **Offene Punkte: 44**  
> **Gesamtpunkte: 62**  
> **Aktuelle Phase:** geführte, sichere Linux-Ersteinrichtung abgeschlossen  
> **Letzte Fortschrittsprüfung:** 2026-08-04

> **Plattformvertrag:** Dieses Projekt wird ausschließlich für Linux-Desktop-Systeme entwickelt. Primäre Zielsysteme sind Kubuntu 22.04 LTS und Kubuntu 24.04 LTS. Windows, macOS, Android und iOS gehören nicht zum Entwicklungs-, Test- oder Releaseumfang.

MULTIMODULTOOL2026 ist ein lokal arbeitendes Linux-Desktop-Werkzeug zur sicheren Analyse, Organisation, Benennung und Wiederauffindbarkeit großer Dateisammlungen.

## Schnellstart unter Kubuntu

```bash
chmod +x start.sh setup.sh
./start.sh
```

Fehlen Python-Komponenten, `.venv` oder PySide6, startet automatisch der geführte Einrichtungsassistent. Er prüft Linux, Python 3.10+, `python3-venv`, KDE Plasma, X11/Wayland, Schreibrechte, `.venv` und PySide6.

Unter KDE verwendet er nach Möglichkeit KDialog mit Schaltflächen; andernfalls einen klaren Terminaldialog. Systempakete und Projektumgebung benötigen jeweils eine ausdrückliche Bestätigung. Die neue `.venv` wird vollständig in einem temporären Ordner aufgebaut, geprüft und erst danach atomar aktiviert.

Nur prüfen:

```bash
./setup.sh --check-only
```

Ausdrücklich bestätigte Terminaleinrichtung:

```bash
./setup.sh --yes --no-gui-dialogs
```

## Aktuell startbarer Stand

Das PySide6-Grundgerüst bildet alle neun verbindlichen Layoutzonen sichtbar ab. Vor dem GUI-Start werden Linux-Plattform, lokale Umgebung und `layout-manifest.json` geprüft. Produktive Dateioperationen sind bis zur sicheren XDG-, Backup-, Papierkorb-, Undo- und Recovery-Architektur deaktiviert.

## Linux-Zielumfang

Unterstützt und verpflichtend zu testen:

- Kubuntu 22.04 LTS, x86-64
- Kubuntu 24.04 LTS, x86-64
- KDE Plasma unter X11 und Wayland
- Fenstergrößen von 1024 × 680 bis 4K
- lokale Dateisysteme und eingehängte Linux-Datenträger

Nicht Teil des Projekts:

- Windows-Installer oder Windows-spezifische Pfade
- macOS-App-Bundles
- Android- oder iOS-Versionen
- Browser-, PWA- oder Web-App-Ausgabe

## GitHub-Zugriff

Der aktuell verbundene GitHub-Nutzer `provoware` besitzt Admin-Rechte. Diese Rechte werden durch GitHub und die installierte GitHub-App bereitgestellt, nicht durch Repository-Dateien. Tokens oder andere Geheimnisse werden niemals committed. Details: [`docs/GITHUB_ZUGRIFF.md`](docs/GITHUB_ZUGRIFF.md).

## Visuelle Leitvorlage

![Visuelle Layout- und Orientierungsvorlage](assets/ui-reference/multimodultool2026-ui-layout-reference-2026.webp)

Die Abbildung bleibt die primäre grafische Orientierung. Grundaufbau, Zonenfolge und räumliche Logik bleiben bestehen, solange keine ausdrückliche Änderung verlangt wird.

Verbindliche Quellen:

- [`docs/UI_BASISVORLAGE.md`](docs/UI_BASISVORLAGE.md)
- [`standards/UI_LAYOUT_STANDARD_2026.md`](standards/UI_LAYOUT_STANDARD_2026.md)
- [`layout-manifest.json`](layout-manifest.json)
- [`AGENTS.md`](AGENTS.md)

## Prüfungen

```bash
python3 -m src.main --validate-only
python3 tools/validate_repository.py
python3 -m unittest discover -s tests -v
```

Der GitHub-Workflow `.github/workflows/repository-contract.yml` prüft Plattformvertrag, Pflichtdateien, Manifest, Fortschritt, Einrichtungsassistent, Python-Syntax und Unit-Tests.

## Pflichtdokumente

| Datei | Zweck |
|---|---|
| [`CHANGELOG.md`](CHANGELOG.md) | Änderungen je Iteration |
| [`ANLEITUNG_TOOL.md`](ANLEITUNG_TOOL.md) | Installation und Bedienung |
| [`TODO.md`](TODO.md) | priorisierte Entwicklungsaufgaben |
| [`SCHWACHSTELLEN.md`](SCHWACHSTELLEN.md) | bekannte Risiken und Gegenmaßnahmen |
| [`UPGRADE_POOL.md`](UPGRADE_POOL.md) | bewertete spätere Linux-Ideen |
| [`ENTWICKLERDOKU.md`](ENTWICKLERDOKU.md) | Architektur und Prüfungen |
| [`docs/GITHUB_ZUGRIFF.md`](docs/GITHUB_ZUGRIFF.md) | Berechtigungs- und Geheimnisvertrag |

## Projektstruktur

```text
/
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
├── setup.sh
├── start.sh
├── docs/GITHUB_ZUGRIFF.md
├── src/
├── tests/test_setup_assistant.py
└── tools/setup_assistant.py
```

## Aktuelle Grenze

Die Einrichtung ist automatisiert, aber der Download von PySide6 benötigt derzeit Internetzugang. Eine physische Erstinstallationsabnahme auf frischen Kubuntu-22.04- und 24.04-Systemen bleibt offen. Der direkt folgende Schritt ist `P0-002`: XDG-konforme Trennung von Programm-, Konfigurations-, Daten-, Cache- und Statuspfaden.
