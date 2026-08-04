# MULTIMODULTOOL2026

> **Entwicklungsfortschritt: 41 %**  
> **Erledigte Punkte: 27**  
> **Offene Punkte: 39**  
> **Gesamtpunkte: 66**  
> **Aktuelle Phase:** atomarer Projektpapierkorb und Parallelstart-Stresstest  
> **Letzte Fortschrittsprüfung:** 2026-08-04

> **Plattformvertrag:** Ausschließlich Linux-Desktop. Primäre Zielsysteme sind Kubuntu 22.04 LTS und Kubuntu 24.04 LTS unter KDE Plasma, X11 oder Wayland auf x86-64.

MULTIMODULTOOL2026 ist ein lokal arbeitendes Linux-Desktop-Werkzeug zur sicheren Analyse und Organisation großer Dateisammlungen. Produktive Dateiworkflows bleiben gesperrt, bis Undo/Redo und Wiederanlauf vollständig geprüft sind.

## Schnellstart und Diagnose

```bash
chmod +x start.sh setup.sh
./start.sh
python3 -m src.main --validate-only
python3 -m src.main --show-diagnostics
```

## Projektbezogener Papierkorb

Der neue Kernvertrag verschiebt reguläre Dateien und Verzeichnisse ausschließlich per atomarem `os.replace` innerhalb desselben Dateisystems:

```text
<Projekt>/.multimodultool2026/trash/transactions/<MMTTRASH-ID>/
├── manifest.json   # 0600
└── payload
```

Vor jeder Transaktion werden Projektgrenze, Mountstatus, Symlinks, Hardlinks, Namenskonflikte, freier Speicher, Quellfingerabdruck und Wiederherstellbarkeit geprüft. Die Vorschau ist rein lesend. Kopieren mit anschließendem Löschen und dauerhafte Papierkorbleerung sind nicht implementiert.

Wiederherstellung ist nur mit gültigem Manifest, unverändertem Payload, sicherem Elternordner und freiem Originalpfad möglich. Beschädigte oder zweifelhafte Zustände bleiben unverändert und werden über den zentralen Sechs-Felder-Fehlervertrag erklärt.

## Single-Instance und Parallelstart

Normale GUI-Starts verwenden einen privaten Unix-Domain-Socket unter `$XDG_RUNTIME_DIR`. Weitere Starts dürfen nur `activate` oder `show-diagnostics` übergeben und werden über Linux `SO_PEERCRED` dem aktuellen Nutzer zugeordnet.

Der Stresstest simuliert **20 nahezu gleichzeitige Zweitstarts** und verlangt:

- genau eine Primärinstanz,
- jede gültige Aktivierung höchstens einmal,
- keine verlorene oder doppelte Kennung,
- keine Socket- oder Metadatenreste nach dem Schließen.

## Rein lesende Diagnosezentrale

Lokale bereinigte Ereignisse können nach Schweregrad und Diagnosekennung gefiltert und einzeln kopiert werden. Löschen, Upload, automatische Reparatur und Auto-Export sind nicht vorhanden.

## Automatische Prüfungen

```bash
python3 tools/validate_repository.py
python3 -m unittest discover -s tests -p "test_*.py" -v
python3 -m unittest tests.test_project_trash -v
python3 -m unittest tests.test_single_instance_stress -v
python3 -m unittest tests.test_settings_failpoints -v
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_gui_offscreen -v
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_gui_trash_contract -v
```

## Verbindliche Dokumente

- [`TODO.md`](TODO.md)
- [`AGENTS.md`](AGENTS.md)
- [`ANLEITUNG_TOOL.md`](ANLEITUNG_TOOL.md)
- [`ENTWICKLERDOKU.md`](ENTWICKLERDOKU.md)
- [`SCHWACHSTELLEN.md`](SCHWACHSTELLEN.md)
- [`UPGRADE_POOL.md`](UPGRADE_POOL.md)
- [`docs/XDG_PFADVERTRAG.md`](docs/XDG_PFADVERTRAG.md)
- [`docs/EINSTELLUNGSVERTRAG.md`](docs/EINSTELLUNGSVERTRAG.md)
- [`docs/FEHLER_UND_EREIGNISVERTRAG.md`](docs/FEHLER_UND_EREIGNISVERTRAG.md)
- [`docs/SINGLE_INSTANCE_UND_DIAGNOSEVERTRAG.md`](docs/SINGLE_INSTANCE_UND_DIAGNOSEVERTRAG.md)
- [`docs/PAPIERKORBVERTRAG.md`](docs/PAPIERKORBVERTRAG.md)
