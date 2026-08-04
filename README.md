# MULTIMODULTOOL2026

> **Entwicklungsfortschritt: 43 %**  
> **Erledigte Punkte: 29**  
> **Offene Punkte: 38**  
> **Gesamtpunkte: 67**  
> **Aktuelle Phase:** append-only Undo/Redo und rein lesende Transaktionsübersicht  
> **Letzte Fortschrittsprüfung:** 2026-08-04

> **Plattformvertrag:** Ausschließlich Linux-Desktop. Primäre Zielsysteme sind Kubuntu 22.04 LTS und Kubuntu 24.04 LTS unter KDE Plasma, X11 oder Wayland auf x86-64.

MULTIMODULTOOL2026 ist ein lokal arbeitendes Linux-Desktop-Werkzeug zur sicheren Analyse und Organisation großer Dateisammlungen. Produktive Dateiworkflows bleiben gesperrt, bis Abbruch und Wiederanlauf vollständig geprüft sind.

## Schnellstart und Diagnose

```bash
chmod +x start.sh setup.sh
./start.sh
python3 -m src.main --validate-only
python3 -m src.main --show-diagnostics
```

## Projektpapierkorb und Undo/Redo

Papierkorbtransaktionen bleiben projektbezogen und verwenden ausschließlich atomare Umbenennungen innerhalb desselben Dateisystems:

```text
<Projekt>/.multimodultool2026/
├── history/
│   └── actions.jsonl                         # 0600
└── trash/
    └── transactions/<MMTTRASH-ID>/
        ├── manifest.json                     # 0600
        └── payload
```

Das neue Undo-/Redo-Journal ist append-only und SHA-256-hashverkettet. Es speichert ausschließlich relative Projektpfade sowie eindeutige Aktions-, Transaktions- und Ereignis-IDs. Jede Dateioperation besitzt ein Intent- und ein Abschlussereignis.

Sicherheitsregeln:

- Undo arbeitet nur auf der letzten aktiven Aktion.
- Mehrfaches Undo läuft in exakter Rückwärtsreihenfolge.
- Redo arbeitet nur auf der nächsten zurückgenommenen Aktion.
- Mehrfaches Redo läuft in ursprünglicher Vorwärtsreihenfolge.
- Wiederholtes Undo oder Redo erzeugt keine Doppeloperation.
- Konflikte, beschädigte Hashketten und widersprüchliche Manifestzustände blockieren.
- Eine neue Aktion wird nicht begonnen, solange eine Redo-Kette vorhanden ist.
- Vorhandene Journalzeilen werden niemals verändert oder entfernt.

Ein getesteter Lauf wendet zehn Papierkorbaktionen an, nimmt sie vollständig rückwärts zurück und führt sie danach vollständig vorwärts erneut aus.

## Absturzabgleich

Bleibt nach einer Unterbrechung nur ein Intent-Ereignis zurück, prüft der nächste Aufruf Papierkorbmanifest, Payload und Originalpfad. Nur ein eindeutig belegter Zustand wird durch das fehlende Abschlussereignis ergänzt. Mehrdeutige Zustände bleiben unverändert und werden über den zentralen Fehlervertrag blockiert.

## Rein lesende Transaktionsübersicht

Die Oberfläche kann Transaktionen nach folgenden Zuständen filtern:

- `prepared`
- `trashed`
- `restored`
- `damaged`

Beschädigte oder unsichere Transaktionsverzeichnisse werden nur markiert. Die Übersicht besitzt keine Wiederherstellungs-, Reparatur-, Lösch-, Upload- oder Exportfunktion und verändert keine Manifestbytes.

## Single-Instance und Parallelstart

Normale GUI-Starts verwenden einen privaten Unix-Domain-Socket unter `$XDG_RUNTIME_DIR`. Weitere Starts dürfen nur `activate` oder `show-diagnostics` übergeben und werden über Linux `SO_PEERCRED` dem aktuellen Nutzer zugeordnet. Der Stresstest simuliert 20 nahezu gleichzeitige Zweitstarts und verlangt genau eine Primärinstanz, höchstens einmalige Aktivierungen und vollständige Laufzeitbereinigung.

## Automatische Prüfungen

```bash
python3 tools/validate_repository.py
python3 -m src.main --validate-only
python3 -m unittest discover -s tests -p "test_*.py" -v
python3 -m unittest tests.test_project_trash -v
python3 -m unittest tests.test_undo_redo -v
python3 -m unittest tests.test_transaction_overview -v
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
