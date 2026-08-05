# ANLEITUNG_TOOL

## Unterstützte Systeme

Kubuntu 22.04/24.04, KDE Plasma, X11 oder Wayland, x86-64. Andere Systeme werden vor produktiven Zugriffen kontrolliert blockiert.

## Start

```bash
chmod +x start.sh setup.sh
./start.sh
```

Beim Start werden Linux, Python, PySide6, Manifest, XDG-Pfade, Einstellungen, Ereignisjournal und Single-Instance-Laufzeitpfad geprüft.

Rein lesende Prüfungen:

```bash
python3 -m src.main --validate-only
python3 -m src.main --paths-only
python3 -m src.main --settings-only
python3 -m src.main --show-diagnostics
python3 -m src.main --help
```

## Hilfe und Tooltips

Der Menüpunkt **Hilfe** öffnet ein rein lesendes Fenster. Es erklärt:

- welche Funktionen bereits freigegeben sind,
- warum einzelne Bereiche weiterhin gesperrt sind,
- welche Prüfung als Nächstes fehlt,
- wie Diagnose, Abbruch und Wiederanlauf funktionieren,
- wann Releaseartefakte den Zusatz `_save_` erhalten.

Deaktivierte Schaltflächen bleiben absichtlich sichtbar. Ihr Tooltip nennt den konkreten Blocker. Eine Sperre darf nicht durch manuelle Datei-, Manifest- oder Einstellungsänderung umgangen werden.

## Sicherer langer Lauf

Der technische Laufkern arbeitet in dieser Reihenfolge:

1. Projektgrenze und Quellen prüfen.
2. Unveränderlichen Laufplan mit Planhash erzeugen.
3. Vor dem ersten Intent einen atomaren Checkpoint schreiben.
4. Jeden Schritt über Papierkorbmanifest und Undo-/Redo-Journal bestätigen.
5. Abbruch nur vor einem neuen Intent oder nach einem vollständig bestätigten Schritt übernehmen.
6. Nach Neustart Checkpoint, Journal, Manifest, Originalpfad und Payload gemeinsam abgleichen.

Interner Speicherort:

```text
<Projekt>/.multimodultool2026/runs/<MMTRUN-ID>/
├── plan.json
├── checkpoint.json
├── run.lock
└── cancel.request
```

Produktive Projektwahl und Massenoperationen sind noch nicht freigegeben. Der technische Kern darf deshalb nicht durch selbst erzeugte Laufdateien manuell gestartet werden.

## Diagnose

```bash
python3 -m src.main --show-diagnostics
```

Die Diagnose zeigt bereinigte lokale Ereignisse. Erlaubt sind Filtern und Kopieren eines einzelnen sicheren Berichts. Nicht vorhanden sind Löschen, Upload, automatische Reparatur oder automatischer Export.

## Releasekandidat bauen und prüfen

```bash
python3 tools/build_deb_release.py \
  --wheelhouse dist/wheelhouse \
  --output dist/release
```

Die Rohartefakte sind noch keine final freigegebenen Dateien. Zuerst müssen Kubuntu 22.04 und 24.04 vollständig grün sein. Jeder Kubuntu-Job sichert unabhängig vom Ergebnis:

- vollständiges Rohprotokoll,
- letzte erreichte Phase,
- inneren und äußeren ursprünglichen Exit-Code,
- vorhandenen JSON-Abnahmebericht.

## Fertige `_save_`-Dateien erzeugen

Nur nach erfolgreicher Matrix:

```bash
python3 tools/finalize_release_artifacts.py \
  --source dist/release-artifacts \
  --output dist/release-ready \
  --policy release/release-status.json
```

Erzeugt werden ausschließlich:

```text
multimodultool2026_<version>_amd64_save_.deb
multimodultool2026_<version>_amd64_save_.deb.sha256
multimodultool2026-<version>-amd64_save_.tar.gz
release-manager_save_.sh
CANDIDATE_BUILD_RESULT_save_.json
RELEASE_STATUS_save_.json
```

Der Finalizer prüft Paket- und Bundlehash, Sidecar-Dateibindung, Symlinks, Dateirechte, Zielpfad und Namensschema. Ein vorhandener generierter Ausgabeordner wird erst nach vollständig erfolgreicher Vorvalidierung atomar ersetzt. Alte generierte Reste werden nicht übernommen.

## Installation

```bash
./release-manager_save_.sh verify ./multimodultool2026_<version>_amd64_save_.deb
sudo ./release-manager_save_.sh install ./multimodultool2026_<version>_amd64_save_.deb --yes
multimodultool2026 --verify-installation
```

Upgrade und Rollback:

```bash
sudo ./release-manager_save_.sh upgrade ./multimodultool2026_<version>_amd64_save_.deb --yes
sudo ./release-manager_save_.sh rollback --yes
```

Normale Entfernung bewahrt XDG-Nutzerdaten. Der vollständige Purge benötigt zusätzlich `--purge-system-state --purge-current-user-data --yes` und wird bei Symlinks oder unklarer Nutzerzuordnung blockiert.

## Entwicklerprüfungen

```bash
python3 tools/validate_repository.py
python3 -m unittest tests.test_finalize_release_artifacts -v
python3 -m unittest tests.test_run_control -v
python3 -m unittest tests.test_run_control_sigkill -v
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_gui_offscreen -v
bash -n tests/helpers/kubuntu_release_lifecycle.sh
```
