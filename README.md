# MULTIMODULTOOL2026

> **Entwicklungsfortschritt: 38 %**  
> **Erledigte Punkte: 25**  
> **Offene Punkte: 40**  
> **Gesamtpunkte: 65**  
> **Aktuelle Phase:** sicherer Linux-Single-Instance-Schutz und rein lesende Diagnosezentrale  
> **Letzte Fortschrittsprüfung:** 2026-08-04

> **Plattformvertrag:** Ausschließlich Linux-Desktop. Primäre Zielsysteme sind Kubuntu 22.04 LTS und Kubuntu 24.04 LTS unter KDE Plasma, X11 oder Wayland. Windows, macOS, Android, iOS, Browser und PWA sind ausgeschlossen.

MULTIMODULTOOL2026 ist ein lokal arbeitendes Linux-Desktop-Werkzeug zur sicheren Analyse, Organisation, Benennung und Wiederauffindbarkeit großer Dateisammlungen. Produktive Dateioperationen bleiben bis Papierkorb, Undo und Wiederanlauf gesperrt.

## Schnellstart

```bash
chmod +x start.sh setup.sh
./start.sh
```

Nur prüfen:

```bash
python3 -m src.main --validate-only
python3 -m src.main --paths-only
python3 -m src.main --settings-only
```

Bestehende Instanz aktivieren und Diagnose öffnen:

```bash
python3 -m src.main --show-diagnostics
python3 -m src.main --show-diagnostics --diagnostic-id MMT-XDG-20260804-ABCD1234
```

## Sicherer Single-Instance-Schutz

Beim ersten normalen Start wird im privaten Linux-Laufzeitverzeichnis ein Unix-Domain-Socket angelegt. Ein weiterer Start erzeugt keine konkurrierende GUI, sondern sendet ausschließlich eine streng validierte Aktivierungsnachricht an die vorhandene Instanz.

Erlaubt sind nur:

- `activate`
- `show-diagnostics`
- optional eine geprüfte Diagnosekennung

Nicht erlaubt sind Dateipfade, freie Argumentlisten, private Dateiinhalte, Löschaufträge oder beliebige Befehle. Der Server prüft die Linux-Peer-UID des Absenders. Laufzeitverzeichnis, Socket und Metadaten werden auf Eigentümer, Dateityp, Symlinks, Hardlinks und Rechte geprüft.

Veraltete Sperren werden nur entfernt, wenn Socket, Metadaten, Nutzerkennung, Boot-Kennung und Prozesszustand eindeutig belegen, dass keine aktive Instanz mehr besteht. Beschädigte oder zweifelhafte Sperren werden nicht überschrieben, sondern über die zentrale Fehler- und Ereignisschicht erklärt.

## Rein lesende Diagnosezentrale

Die Oberfläche zeigt lokale, bereits bereinigte Ereignisse nach:

- Schweregrad,
- Diagnosekennung,
- Ursache,
- Folge,
- unverändertem Datenstand,
- Lösung und sicherem nächsten Schritt.

Die Diagnosezentrale darf nur lesen und einzelne bereinigte Berichte in die Zwischenablage kopieren. Löschen, Upload und automatischer Export sind nicht vorhanden. Das Journal wird mit Größen- und Datensatzgrenze gelesen; ungültige Zeilen werden übersprungen, aber niemals verändert.

## Sichere Speicherorte

| Bereich | Standardpfad | Rechte |
|---|---|---:|
| Konfiguration | `~/.config/multimodultool2026` | `0700` |
| Nutzerdaten | `~/.local/share/multimodultool2026` | `0700` |
| Cache | `~/.cache/multimodultool2026` | `0700` |
| Status | `~/.local/state/multimodultool2026` | `0700` |
| Logs | `~/.local/state/multimodultool2026/logs` | `0700` |
| Ereignisjournal | `.../logs/events.jsonl` | `0600` |
| Instanzlaufzeit | `$XDG_RUNTIME_DIR/multimodultool2026` | `0700` |
| Instanzmetadaten | `instance.json` | `0600` |
| Instanzsocket | `instance.sock` | `0600` |

## Automatische Prüfungen

```bash
python3 tools/validate_repository.py
python3 -m unittest discover -s tests -v
python3 -m unittest tests.test_single_instance -v
python3 -m unittest tests.test_diagnostics_center -v
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_gui_offscreen -v
```

GitHub Actions prüft bei jedem Push und Pull Request:

- Linux-, Manifest-, XDG-, Einstellungs- und Fehlervertrag,
- Single-Instance-Sicherheit und sichere lokale Nachrichtenübergabe,
- veraltete und beschädigte Sperrzustände,
- rein lesende Diagnosefilter und Kopierfunktion,
- Failpoint-Matrix der Einstellungstransaktionen,
- neun Layoutzonen und globalen Fehlerdialog im Qt-Offscreen-Modus.

## Verbindliche Dokumente

- [`AGENTS.md`](AGENTS.md)
- [`TODO.md`](TODO.md)
- [`ANLEITUNG_TOOL.md`](ANLEITUNG_TOOL.md)
- [`ENTWICKLERDOKU.md`](ENTWICKLERDOKU.md)
- [`SCHWACHSTELLEN.md`](SCHWACHSTELLEN.md)
- [`UPGRADE_POOL.md`](UPGRADE_POOL.md)
- [`docs/XDG_PFADVERTRAG.md`](docs/XDG_PFADVERTRAG.md)
- [`docs/EINSTELLUNGSVERTRAG.md`](docs/EINSTELLUNGSVERTRAG.md)
- [`docs/FEHLER_UND_EREIGNISVERTRAG.md`](docs/FEHLER_UND_EREIGNISVERTRAG.md)
- [`docs/SINGLE_INSTANCE_UND_DIAGNOSEVERTRAG.md`](docs/SINGLE_INSTANCE_UND_DIAGNOSEVERTRAG.md)
