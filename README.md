# MULTIMODULTOOL2026

> **Entwicklungsfortschritt: 49 %**  
> **Erledigte Punkte: 33**  
> **Offene Punkte: 35**  
> **Gesamtpunkte: 68**  
> **Aktuelle Phase:** gehärteter Linux-Releasekern; produktiver Nutzerworkflow weiterhin gesperrt  
> **Letzte Fortschrittsprüfung:** 2026-08-05

> **Plattformvertrag:** ausschließlich Linux-Desktop; primär Kubuntu 22.04 LTS und Kubuntu 24.04 LTS unter KDE Plasma, X11 oder Wayland auf x86-64.

MULTIMODULTOOL2026 ist ein lokal arbeitendes Linux-Desktop-Werkzeug für sichere Dateiorganisation. Der technische Schutzkern für XDG-Pfade, Einstellungen, Fehlerereignisse, Single-Instance, Projektpapierkorb, Undo/Redo, Abbruch, Wiederanlauf und reproduzierbare Debian-Pakete ist implementiert. Produktive Dateiworkflows bleiben sichtbar, aber absichtlich deaktiviert, bis die geführte Projekt- und Ordnerauswahl vollständig geprüft ist.

## Schnellstart

```bash
chmod +x start.sh setup.sh
./start.sh
```

Rein lesende Prüfungen:

```bash
python3 -m src.main --validate-only
python3 -m src.main --paths-only
python3 -m src.main --settings-only
python3 -m src.main --show-diagnostics
python3 -m src.main --help
```

Die grafische Hilfe erklärt freigegebene Funktionen, konkrete Sperrgründe, Diagnose, Abbruch, Wiederanlauf und Releasekennzeichnung. Tooltips nennen bei jeder deaktivierten Aktion den fehlenden Freigabeschritt.

## Release-Dateistatus

Die Kennzeichnung `_save_` wird **ausschließlich auf geprüfte Releaseausgaben** angewendet. Quelldateien werden nicht umbenannt, weil zusätzliche Namensanhänge Python-Imports, Startpfade, Desktopdateien, Paketmanifeste und Wartungsskripte beschädigen würden. Die finalen Dateien entstehen erst, wenn beide Kubuntu-Lebenszyklen erfolgreich abgeschlossen wurden.

| Fertige Dateien nach grüner Kubuntu-Matrix | Unfertig oder nicht freigegeben |
|---|---|
| `multimodultool2026_<version>_amd64_save_.deb` | Geführte Projektwahl und Sicherheitsmodus (`P1-001`) |
| `multimodultool2026_<version>_amd64_save_.deb.sha256` | Linux-Ordnerauswahl mit Rechte-, Mount- und Speicherprüfung (`P1-003`) |
| `multimodultool2026-<version>-amd64_save_.tar.gz` | Produktive Analyse-, Duplikat-, Organisations- und Umbenennungsworkflows (`P1-004` bis `P1-008`) |
| `release-manager_save_.sh` | Produktiver JSON-/Markdown-Ergebnisbericht (`P1-009`) |
| `CANDIDATE_BUILD_RESULT_save_.json` | Journalrotation, Migration, Abdeckungs- und Qualitätsgrenzen (`P3-003`, `P3-005` bis `P3-007`) |
| `RELEASE_STATUS_save_.json` | Kryptografisch signiertes Stable-Gate und physische KDE-/X11-/Wayland-Abnahme (`P3-009`, `P4-009`) |

Nicht fertige Baseline-Pakete, Rohlogs, Phasendateien und Exit-Code-Nachweise bleiben Test- beziehungsweise Diagnoseartefakte und erhalten bewusst **kein** `_save_`.

Verbindliche Klassifikation: [`release/release-status.json`](release/release-status.json)

## Releaseablauf

1. Baseline und Kandidat reproduzierbar bauen.
2. Kandidat zweimal byteidentisch vergleichen.
3. Kubuntu 22.04 und 24.04 vollständig prüfen: Installation, Erststart, Runtime-Recovery, Upgrade, Rollback, normale Entfernung und bestätigter Purge.
4. Für jeden Kubuntu-Job unabhängig vom Ergebnis Rohprotokoll, letzte Phase und ursprünglichen Exit-Code hochladen.
5. Nur nach vollständig grüner Matrix die sechs `_save_`-Dateien atomar erzeugen und erneut hashen.

Lokale Finalisierung bereits geprüfter Rohartefakte:

```bash
python3 tools/finalize_release_artifacts.py \
  --source dist/release-artifacts \
  --output dist/release-ready \
  --policy release/release-status.json
```

Der Finalizer blockiert Symlinks, falsche Sidecar-Bindungen, Hashabweichungen, unsichere Zielpfade und bereits falsch benannte Artefakte. Ein vorhandenes generiertes Ziel wird erst nach vollständiger Vorvalidierung atomar ersetzt; veraltete Ausgabereste bleiben nicht liegen.

## Sicherheitskern

- private XDG-App-Verzeichnisse `0700`, private Dateien `0600`
- eine Primärinstanz über Unix-Domain-Socket und Linux-Peer-UID
- atomarer Projektpapierkorb ohne Copy-delete-Fallback
- append-only Undo-/Redo-Journal mit SHA-256-Hashkette
- unveränderliche Laufpläne, atomare Checkpoints und `flock`
- kontrollierte Abbruchpunkte und idempotenter Wiederanlauf
- rein lesende Diagnose- und Transaktionsansichten
- kein stilles Überschreiben, dauerhaftes Löschen, Diagnoseupload oder automatische Reparatur

Der technische Aufbau liegt unter `<Projekt>/.multimodultool2026/`. Details werden nicht mehrfach in dieser README wiederholt, sondern in den jeweils verbindlichen Vertragsdokumenten gepflegt.

## Automatische Prüfungen

Schnellprüfung:

```bash
python3 -m src.main --validate-only
python3 tools/validate_repository.py
python3 -m unittest tests.test_finalize_release_artifacts -v
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_gui_offscreen -v
bash -n tests/helpers/kubuntu_release_lifecycle.sh
```

Vollständige Suite:

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

Releasebau:

```bash
python3 tools/build_deb_release.py \
  --wheelhouse dist/wheelhouse \
  --output dist/release
```

## Bewusst offene Produktbereiche

Der aktuelle Stand ist ein gehärteter Release- und Transaktionskern, aber noch kein vollständiges Dateiorganisationsprodukt. Offen bleiben insbesondere:

- geführte Projekt- und Ordnerauswahl
- Dateibestandsanalyse und vollständige Vorschau
- Duplikatfinder, Sortieren, Verschieben und Massenumbenennung
- produktive Ergebnisberichte
- weitere Barrierearmut, Responsive-Abnahme und Kontrastautomatisierung
- Journalrotation, Migration, signierte Stable-Releases
- physische KDE-Prüfung unter X11, Wayland und mehreren DPI-Stufen

Die vollständige Priorisierung steht ausschließlich in [`TODO.md`](TODO.md). Optionale spätere Ideen stehen ausschließlich in [`UPGRADE_POOL.md`](UPGRADE_POOL.md).

## Verbindliche Dokumente

- [`TODO.md`](TODO.md) – Pflichtaufgaben und Fortschrittsquelle
- [`AGENTS.md`](AGENTS.md) – Entwicklungs-, Risiko- und Prüfvertrag
- [`ANLEITUNG_TOOL.md`](ANLEITUNG_TOOL.md) – Nutzer- und Releaseanleitung
- [`SCHWACHSTELLEN.md`](SCHWACHSTELLEN.md) – bekannte Grenzen und Gegenmaßnahmen
- [`ENTWICKLERDOKU.md`](ENTWICKLERDOKU.md) – Architektur und Entwicklung
- [`docs/XDG_PFADVERTRAG.md`](docs/XDG_PFADVERTRAG.md)
- [`docs/EINSTELLUNGSVERTRAG.md`](docs/EINSTELLUNGSVERTRAG.md)
- [`docs/FEHLER_UND_EREIGNISVERTRAG.md`](docs/FEHLER_UND_EREIGNISVERTRAG.md)
- [`docs/SINGLE_INSTANCE_UND_DIAGNOSEVERTRAG.md`](docs/SINGLE_INSTANCE_UND_DIAGNOSEVERTRAG.md)
- [`docs/PAPIERKORBVERTRAG.md`](docs/PAPIERKORBVERTRAG.md)
- [`docs/UNDO_REDO_UND_TRANSAKTIONSVERTRAG.md`](docs/UNDO_REDO_UND_TRANSAKTIONSVERTRAG.md)
- [`docs/ABBRUCH_UND_WIEDERANLAUFVERTRAG.md`](docs/ABBRUCH_UND_WIEDERANLAUFVERTRAG.md)
- [`docs/LINUX_RELEASEVERTRAG.md`](docs/LINUX_RELEASEVERTRAG.md)
