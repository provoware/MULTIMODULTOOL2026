# MULTIMODULTOOL2026

> **Entwicklungsfortschritt: 31 %**  
> **Erledigte Punkte: 19**  
> **Offene Punkte: 43**  
> **Gesamtpunkte: 62**  
> **Aktuelle Phase:** sichere XDG-Pfadtrennung und workflow-fokussiertes Grundlayout  
> **Letzte Fortschrittsprüfung:** 2026-08-04

> **Plattformvertrag:** Dieses Projekt wird ausschließlich für Linux-Desktop-Systeme entwickelt. Primäre Zielsysteme sind Kubuntu 22.04 LTS und Kubuntu 24.04 LTS. Windows, macOS, Android und iOS gehören nicht zum Entwicklungs-, Test- oder Releaseumfang.

MULTIMODULTOOL2026 ist ein lokal arbeitendes Linux-Desktop-Werkzeug zur sicheren Analyse, Organisation, Benennung und Wiederauffindbarkeit großer Dateisammlungen.

## Schnellstart unter Kubuntu

```bash
chmod +x start.sh setup.sh
./start.sh
```

Fehlen Python-Komponenten, `.venv` oder PySide6, startet automatisch der geführte Einrichtungsassistent. Er prüft:

- Linux und Python 3.10+
- Verfügbarkeit von `python3-venv`
- KDE Plasma sowie X11 oder Wayland
- Schreibrecht im Projektordner
- lokale `.venv`
- PySide6-Import

Unter KDE verwendet er nach Möglichkeit KDialog mit Schaltflächen; andernfalls einen klaren Terminaldialog. Systempakete und Projektumgebung benötigen jeweils eine ausdrückliche Bestätigung. Die neue `.venv` wird vollständig in einem temporären Ordner aufgebaut, geprüft und erst danach atomar aktiviert.

Einrichtung nur prüfen:

```bash
./setup.sh --check-only
```

Nichtinteraktive, ausdrücklich bestätigte Einrichtung:

```bash
./setup.sh --yes --no-gui-dialogs
```

## Aktuell startbarer Stand

Das PySide6-Grundgerüst bildet alle neun verbindlichen Layoutzonen sichtbar ab. Vor dem GUI-Start werden Linux-Plattform, lokale Umgebung, `layout-manifest.json` und der XDG-Pfadvertrag geprüft.

Die Oberfläche wurde workflow-fokussiert überarbeitet: klare nummerierte Arbeitsschritte, sichtbare Sicherheitsgrenzen, ein hervorgehobener nächster Schritt und eine rechte Speicher-/Diagnoseleiste. Noch nicht freigegebene Dateiaktionen bleiben sichtbar gesperrt statt scheinbar funktionsfähig zu wirken.

## Sichere XDG-Speichertrennung

Beim normalen Start werden sechs private Linux-Benutzerbereiche mit Modus `0700` vorbereitet und mit einer temporären Schreibprobe nachvalidiert:

| Bereich | Standardpfad |
|---|---|
| Konfiguration | `~/.config/multimodultool2026` |
| Nutzerdaten | `~/.local/share/multimodultool2026` |
| Cache | `~/.cache/multimodultool2026` |
| Status | `~/.local/state/multimodultool2026` |
| Protokolle | `~/.local/state/multimodultool2026/logs` |
| Sicherungen | `~/.local/share/multimodultool2026/backups` |

Vor der Anlage werden absolute Pfade, XDG-Grenzen, Überschneidungen mit dem Programmverzeichnis, doppelte Ziele, vorhandene Dateitypen und Symlinks geprüft. Nach der Anlage werden Existenz, Schreibbarkeit, Verzeichnisrechte und rückstandsfreie Schreibproben erneut geprüft.

Nur den Pfadplan anzeigen:

```bash
python3 -m src.main --paths-only
```

`--validate-only` prüft den Pfadplan rein lesend und legt keine Verzeichnisse an. Details: [`docs/XDG_PFADVERTRAG.md`](docs/XDG_PFADVERTRAG.md).

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

Der GitHub-Workflow `.github/workflows/repository-contract.yml` prüft bei Push und Pull Request Plattformvertrag, Pflichtdateien, Manifest, Fortschritt, Einrichtungsassistent, XDG-Pfadvertrag, Python-Syntax und Unit-Tests.

## Pflichtdokumente

| Datei | Zweck |
|---|---|
| [`CHANGELOG.md`](CHANGELOG.md) | Änderungen je Iteration |
| [`ANLEITUNG_TOOL.md`](ANLEITUNG_TOOL.md) | Installation und Bedienung |
| [`TODO.md`](TODO.md) | priorisierte Entwicklungsaufgaben |
| [`SCHWACHSTELLEN.md`](SCHWACHSTELLEN.md) | bekannte Risiken und Gegenmaßnahmen |
| [`UPGRADE_POOL.md`](UPGRADE_POOL.md) | bewertete spätere Linux-Ideen |
| [`ENTWICKLERDOKU.md`](ENTWICKLERDOKU.md) | Architektur und Prüfungen |
| [`docs/GITHUB_ZUGRIFF.md`](docs/GITHUB_ZUGRIFF.md) | externer Berechtigungs- und Geheimnisvertrag |
| [`docs/XDG_PFADVERTRAG.md`](docs/XDG_PFADVERTRAG.md) | Speicherorte, Grenzen, Rechte und Fehlerverhalten |

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
├── setup.sh
├── start.sh
├── docs/GITHUB_ZUGRIFF.md
├── docs/XDG_PFADVERTRAG.md
├── src/
│   └── xdg_paths.py
├── tests/
│   ├── test_setup_assistant.py
│   └── test_xdg_paths.py
└── tools/setup_assistant.py
```

## Aktuelle Grenze

Die Linux-Ersteinrichtung und XDG-Speichertrennung sind umgesetzt. Eine physische Erstinstallationsabnahme auf frischen Kubuntu-22.04- und 24.04-Systemen bleibt offen. Der direkt folgende Schritt ist `P0-003`: transaktionale Einstellungen mit Schema, Backup und Rollback.
