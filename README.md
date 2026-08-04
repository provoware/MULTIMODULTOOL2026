# MULTIMODULTOOL2026

> **Entwicklungsfortschritt: 33 %**  
> **Erledigte Punkte: 21**  
> **Offene Punkte: 42**  
> **Gesamtpunkte: 63**  
> **Aktuelle Phase:** transaktionale Einstellungen und automatisierter Offscreen-GUI-Vertrag  
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

Das PySide6-Grundgerüst bildet alle neun verbindlichen Layoutzonen sichtbar ab. Vor dem GUI-Start werden Linux-Plattform, lokale Umgebung, `layout-manifest.json`, XDG-Pfade und das versionierte Einstellungsformat geprüft. Beschädigte Einstellungen werden isoliert und automatisch aus der letzten gültigen Sicherung oder sicheren Standardwerten wiederhergestellt. Produktive Dateioperationen bleiben bis Fehlerzentrale, Papierkorb, Undo und Recovery-Worker deaktiviert.


## Sichere XDG-Pfade und Einstellungen

Private Laufzeitdaten liegen ausschließlich in Linux-Benutzerverzeichnissen:

- Konfiguration: `~/.config/multimodultool2026`
- Nutzerdaten und Sicherungen: `~/.local/share/multimodultool2026`
- Cache: `~/.cache/multimodultool2026`
- Status und Logs: `~/.local/state/multimodultool2026`

Aktive Einstellungen liegen als `settings.json` mit Modus `0600` im XDG-Konfigurationspfad. Vor jedem Speichern erfolgen Schema-, Feld-, Typ-, Wertebereichs-, Pfad- und Symlinkprüfung. Geschrieben wird über eine temporäre Datei mit `fsync` und atomarem `os.replace`. Die vorherige gültige Version bleibt als `settings.last-valid.json` erhalten.

Rein lesende Diagnose:

```bash
python3 -m src.main --validate-only
python3 -m src.main --paths-only
python3 -m src.main --settings-only
```

Verträge:

- [`docs/XDG_PFADVERTRAG.md`](docs/XDG_PFADVERTRAG.md)
- [`docs/EINSTELLUNGSVERTRAG.md`](docs/EINSTELLUNGSVERTRAG.md)
- [`standards/settings-schema-v1.json`](standards/settings-schema-v1.json)

## Automatische GUI-Prüfung

GitHub Actions installiert PySide6 und startet die Oberfläche mit `QT_QPA_PLATFORM=offscreen`. Der Smoke-Test prüft ohne Zugriff auf private Nutzerdaten:

- alle neun Layoutzonen,
- sichtbare textuelle Sicherheitszustände,
- Scrollbarkeit von Arbeits- und Kontextbereich,
- deaktivierte, noch nicht freigegebene Aktionen,
- keine Dateianlage allein durch den Fensteraufbau.

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

Der GitHub-Workflow `.github/workflows/repository-contract.yml` prüft bei Push und Pull Request Plattformvertrag, Pflichtdateien, Manifest, Fortschritt, Einrichtungsassistent, Python-Syntax und Unit-Tests.

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
├── src/
├── tests/test_setup_assistant.py
└── tools/setup_assistant.py
```

## Aktuelle Grenze

Die Einrichtung ist automatisiert, aber der Download von PySide6 benötigt derzeit Internetzugang. Eine physische Erstinstallationsabnahme auf frischen Kubuntu-22.04- und 24.04-Systemen bleibt offen. Der direkt folgende Schritt ist `P0-002`: XDG-konforme Trennung von Programm-, Konfigurations-, Daten-, Cache- und Statuspfaden.

## Prüfungen

- Repository-Vertrag
- Linux-, Manifest-, XDG- und Einstellungsprüfung
- Unit-Tests
- Offscreen-GUI-Smoke-Test
