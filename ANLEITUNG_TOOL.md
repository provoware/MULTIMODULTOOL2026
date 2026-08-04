# ANLEITUNG_TOOL

## Unterstützte Systeme

Kubuntu 22.04/24.04, KDE Plasma, X11 oder Wayland, x86-64. Andere Systeme werden kontrolliert blockiert.

## Start

```bash
chmod +x start.sh setup.sh
./start.sh
```

Beim Start werden Linux, Python, PySide6, XDG-Pfade, Einstellungen, Ereignisjournal und Single-Instance-Laufzeitpfad geprüft.

## Sicherer langer Lauf

Der technische Laufkern ist entwickelt und automatisiert geprüft. Der spätere Nutzerworkflow verwendet:

1. Projektordner sicher auswählen.
2. Quellen prüfen und einen unveränderlichen Laufplan erzeugen.
3. Lauf-ID und Planhash anzeigen.
4. Vor dem ersten Intent einen atomaren Checkpoint speichern.
5. Jeden Schritt über Papierkorbmanifest und Undo-/Redo-Journal ausführen.
6. Abbruchanforderungen nur an sicheren Grenzen bestätigen.
7. Nach Neustart den gespeicherten Zustand eindeutig fortsetzen oder blockieren.

Interner Speicherort:

```text
<Projekt>/.multimodultool2026/runs/<MMTRUN-ID>/
├── plan.json
├── checkpoint.json
├── run.lock
└── cancel.request
```

## Abbruch

Eine Abbruchanforderung stoppt nicht mitten in einer atomaren Dateioperation. Sie wird vor dem nächsten Intent oder nach einem vollständig bestätigten Schritt übernommen. Der Checkpoint nennt anschließend `cancelled` und die Zahl der abgeschlossenen Schritte.

## Fortsetzen

Ein kontrolliert abgebrochener Lauf kann ausdrücklich fortgesetzt werden. Dabei werden weder Plan noch bereits bestätigte Aktionen neu erzeugt. Checkpoint, Journal, Manifest, Originalpfad und Payload werden gemeinsam geprüft.

Mögliche Meldungen:

- **Fortsetzen:** Schritt war noch nicht begonnen.
- **Abschluss ergänzen:** Datei oder Manifest war bereits vollständig.
- **Bereits erledigt:** Nur der Checkpoint fehlte.
- **Blockiert:** Zustände widersprechen sich; keine automatische Reparatur.

## Prozessende

Die Testmatrix beendet den Arbeitsprozess mit echtem Linux-`SIGKILL`. Nach dem Neustart darf genau eine vollständige Transaktion existieren. Die Laufsperre muss erneut verfügbar sein und temporäre Dateien dürfen nicht zurückbleiben.

## Noch bewusst gesperrt

- grafische Projekt- und Dateiauswahl
- produktive Massenläufe
- dauerhaftes Löschen
- automatisches Reparieren widersprüchlicher Checkpoints
- Ändern eines bestehenden Laufplans
- Stromausfall-/Hardwarecache-Freigabe

## Diagnose

```bash
python3 -m src.main --show-diagnostics
```

Keine Sperre, kein Checkpoint, kein Manifest und kein Payload darf manuell überschrieben oder gelöscht werden. Diagnosekennung sichern und den dokumentierten Datenstand prüfen.

## Entwicklerprüfungen

```bash
python3 tools/validate_repository.py
python3 -m unittest tests.test_run_control -v
python3 -m unittest tests.test_run_control_sigkill -v
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_gui_trash_contract -v
```

## Releasekandidat installieren

```bash
./release-manager.sh verify ./multimodultool2026_0.9.0~rc1_amd64.deb
sudo ./release-manager.sh install ./multimodultool2026_0.9.0~rc1_amd64.deb --yes
multimodultool2026 --verify-installation
```

Upgrade und Rollback:

```bash
sudo ./release-manager.sh upgrade ./multimodultool2026_0.9.0~rc1_amd64.deb --yes
sudo ./release-manager.sh rollback --yes
```

Normale Entfernung bewahrt XDG-Nutzerdaten. Der vollständige Purge benötigt zusätzlich `--purge-system-state --purge-current-user-data --yes` und wird bei Symlinks oder unklarer Nutzerzuordnung blockiert.
