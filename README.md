# MULTIMODULTOOL2026

> **Entwicklungsfortschritt: 47 %**  
> **Erledigte Punkte: 32**  
> **Offene Punkte: 36**  
> **Gesamtpunkte: 68**  
> **Aktuelle Phase:** installierbarer Linux-Releasekandidat mit Upgrade und Rollback  
> **Letzte Fortschrittsprüfung:** 2026-08-04

> **Plattformvertrag:** Ausschließlich Linux-Desktop. Primäre Zielsysteme sind Kubuntu 22.04 LTS und Kubuntu 24.04 LTS unter KDE Plasma, X11 oder Wayland auf x86-64.

MULTIMODULTOOL2026 ist ein lokal arbeitendes Linux-Desktop-Werkzeug zur sicheren Analyse und Organisation großer Dateisammlungen. Der sicherheitskritische Kern für Einstellungen, Fehler, Single-Instance, Projektpapierkorb, Undo/Redo sowie Abbruch und Wiederanlauf ist automatisiert geprüft. Produktive Nutzerworkflows bleiben bis zur geführten Projekt- und Dateiauswahl gesperrt.

## Schnellstart und Diagnose

```bash
chmod +x start.sh setup.sh
./start.sh
python3 -m src.main --validate-only
python3 -m src.main --show-diagnostics
```

## Projektbezogener Transaktionsbereich

```text
<Projekt>/.multimodultool2026/
├── history/
│   └── actions.jsonl                         # 0600, append-only, SHA-256
├── runs/
│   └── <MMTRUN-ID>/                          # 0700
│       ├── plan.json                         # 0600, unveränderlich
│       ├── checkpoint.json                   # 0600, atomar ersetzt
│       ├── run.lock                          # 0600, flock
│       └── cancel.request                    # 0600, nur bei Anforderung
└── trash/
    └── transactions/<MMTTRASH-ID>/
        ├── manifest.json                     # 0600
        └── payload
```

Absolute Projektpfade werden weder im Laufplan noch im Aktionsjournal gespeichert. Projektgrenzen, Symlinks, Eigentümer, Hardlinks, Dateitypen, Mountgrenzen und Rechte werden vor jeder sicherheitskritischen Aktion geprüft.

## Transaktionaler Laufvertrag

Jeder lange Lauf erhält:

- eine eindeutige `MMTRUN-`-Lauf-ID,
- einen unveränderlichen Plan mit SHA-256-Hash,
- einen atomar ersetzten Checkpoint,
- lückenlose Schrittindizes und Versuchszähler,
- eine exklusive Linux-`flock`-Sperre,
- kontrollierte Abbruchpunkte,
- eine eindeutige Verbindung zu Aktions- und Transaktions-IDs.

Der erste unterstützte lange Lauf ist eine sequenzielle, projektbezogene Papierkorbserie. Jeder Einzelschritt verwendet weiterhin das vorhandene append-only Undo-/Redo-Journal und die atomaren Papierkorbmanifeste.

## Kontrollierter Abbruch

Eine Abbruchanforderung wird separat als private `cancel.request` gespeichert. Der aktive Lauf ist alleiniger Schreiber des Checkpoints und bestätigt den Abbruch nur:

1. bevor ein neuer Intent angehängt wurde, oder
2. nachdem Dateioperation, Verzeichnis-`fsync`, Manifestabschluss und Journalabschluss vollständig bestätigt sind.

Ein bereits begonnener atomarer Einzelschritt wird nicht mitten im kritischen Abschnitt abgebrochen. Sperren und Dateideskriptoren werden beim Verlassen des Prozesses freigegeben; temporäre Dateien werden entfernt.

## Idempotenter Wiederanlauf

Nach normalem Abbruch, Ausnahme oder Prozessende werden gemeinsam geprüft:

- Laufplan und Planhash,
- Checkpointgeneration und aktueller Schritt,
- append-only Aktionsjournal,
- Transaktionsmanifest,
- Originalpfad,
- Payload.

Mögliche Ergebnisse:

- sicher am gespeicherten Schritt fortsetzen,
- nur das nachweislich fehlende Manifest- oder Journalabschlussereignis ergänzen,
- bereits abgeschlossenen Schritt nur im Checkpoint bestätigen,
- widersprüchlichen Zustand unverändert blockieren.

Bereits ausgeführte Dateioperationen werden niemals ein zweites Mal gestartet.

## Echte `SIGKILL`-Prozessabbruchmatrix

Isolierte Linux-Testprozesse werden an zehn Stellen gezielt mit `SIGKILL` beendet:

```text
vor / nach Intent
vor / nach Dateioperation
vor / nach fsync
vor / nach Manifestabschluss
vor / nach Journalabschluss
```

Nach jedem Neustart muss genau eine vollständige Aktion existieren. Geprüft werden außerdem unveränderte Nutzdateninhalte, ein einzelner Payload, gültiges Manifest, vollständige Hashkette, abgeschlossener Checkpoint, erneut freigegebene Laufsperre und fehlende temporäre Reste.

## Undo/Redo und Transaktionsübersicht

Undo arbeitet ausschließlich rückwärts auf der letzten aktiven Aktion; Redo ausschließlich vorwärts auf der nächsten zurückgenommenen Aktion. Die read-only Transaktionsübersicht zeigt `prepared`, `trashed`, `restored` und `damaged`, verändert aber keine Manifeste und besitzt keine Reparatur-, Restore-, Lösch-, Upload- oder Exportfunktion.

## Automatische Prüfungen

```bash
python3 tools/validate_repository.py
python3 -m src.main --validate-only
python3 -m unittest discover -s tests -p "test_*.py" -v
python3 -m unittest tests.test_project_trash -v
python3 -m unittest tests.test_undo_redo -v
python3 -m unittest tests.test_transaction_overview -v
python3 -m unittest tests.test_run_control -v
python3 -m unittest tests.test_run_control_sigkill -v
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
- [`docs/UNDO_REDO_UND_TRANSAKTIONSVERTRAG.md`](docs/UNDO_REDO_UND_TRANSAKTIONSVERTRAG.md)
- [`docs/ABBRUCH_UND_WIEDERANLAUFVERTRAG.md`](docs/ABBRUCH_UND_WIEDERANLAUFVERTRAG.md)

## Installierbarer Linux-Releasekandidat

P0-009 erzeugt ein reproduzierbares Debian-Paket für Kubuntu 22.04 und 24.04 auf x86-64. Der Releasekandidat enthält:

- eindeutige `MMTBUILD-`-Build-ID,
- sortiertes Source- und installiertes SHA-256-Dateimanifest,
- lokal gebündelte PySide6-Wheels für den netzlosen Erststart,
- geprüfte Installation und Aktualisierung,
- lokales Rollback auf den vorherigen verifizierten Paketstand,
- normale Entfernung mit Erhalt der Nutzerdaten,
- ausdrücklich bestätigten Purge von Systemzustand und den XDG-Daten des ausgewählten Nutzers.

Die Release-CI baut denselben Kandidaten zweimal byteidentisch und führt den vollständigen Lebenszyklus in frischen containerisierten Kubuntu-22.04- und Kubuntu-24.04-Userlands aus. Eine kryptografische Release-Signatur folgt separat mit `P3-009`.

```bash
python3 tools/build_deb_release.py   --wheelhouse dist/wheelhouse   --output dist/release
```

- [`docs/LINUX_RELEASEVERTRAG.md`](docs/LINUX_RELEASEVERTRAG.md)
