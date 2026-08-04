# ENTWICKLERDOKU

## Architekturstand

```text
src/main.py
├── manifest_validator.py
├── xdg_paths.py
├── settings_manager.py
├── error_events.py
├── error_dialog.py
├── single_instance.py
├── diagnostics_center.py
├── project_trash.py
├── undo_redo.py
├── transaction_overview.py
└── trash_contract_panel.py
```

## Projektpapierkorb-API

```python
preview = preview_trash_move(project_root, source_path)
result = execute_trash_move(preview)
restored = restore_transaction(project_root, transaction_id)
```

Vorschau und Ausführung prüfen Projektgrenze, Quelltyp, Symlinks, Hardlinks, Mountstatus, Schreibrechte, freien Speicher, Quellfingerabdruck und Konflikte. Move und Restore verwenden ausschließlich `os.replace` auf demselben Dateisystem.

## Undo-/Redo-Journal

```python
journal = UndoRedoJournal(project_root)
result = journal.record_trash(preview)
undo_result = journal.undo_last()
redo_result = journal.redo_next()
snapshot = journal.inspect()
```

Speicherort:

```text
<Projekt>/.multimodultool2026/history/actions.jsonl
```

### Ereignismodell

- `prepare` → `apply` oder `cancel`
- `apply` → `undo-intent` → `undo`
- `undo` → `redo-intent` → `redo`
- `redo` → `undo-intent`

Jedes Ereignis enthält:

- Schemaversion und lückenlose Sequenznummer
- eindeutige Ereignis-, Aktions- und Transaktions-ID
- Operation `project-trash`
- relativen Originalpfad
- Zeitstempel und Folgezustand
- Recovery-Kennzeichen
- `previousHash` und `eventHash`

Der Hash wird über das kanonische JSON ohne `eventHash` berechnet. Jede neue Zeile referenziert den Hash der vorherigen Zeile.

### Schreibvertrag

1. Journalpfad und Eigentümer prüfen.
2. Datei mit `O_APPEND`, `O_NOFOLLOW` und `O_CLOEXEC` öffnen.
3. Exklusives `flock` setzen.
4. bestehendes Journal vollständig lesen und validieren.
5. Folgezustand und Stapelinvariante prüfen.
6. genau eine vollständige JSONL-Zeile anhängen.
7. `fsync` ausführen.
8. Lock freigeben.

Vorhandene Zeilen werden nicht ersetzt, gekürzt oder repariert.

### Stapelmodell

Die Aktionsliste muss jederzeit als angewendetes Präfix und zurückgenommener Suffix darstellbar sein. Daher:

- Undo: letzte angewendete Aktion
- Redo: erste zurückgenommene Aktion
- neue Aktion bei vorhandenem Redo-Suffix: blockiert

Ein Redo behält die Aktions-ID, erhält jedoch eine neue Papierkorb-Transaktions-ID. Das alte Restore-Manifest bleibt unverändert abgeschlossen.

### Recovery

`reconcile()` gleicht ausschließlich unvollständige Intent-Zustände ab:

- `prepare` ohne Transaktion und Quelle vorhanden → `cancel`
- `prepare` mit Payload und freiem Original → fehlendes `apply`
- `undo-intent` mit Manifest `restored` → fehlendes `undo`
- `redo-intent` mit vollständiger neuer Transaktion → fehlendes `redo`

Mehrdeutige Zustände lösen `SafeOperationError(category="undo-redo-journal")` aus.

## Rein lesende Transaktionsübersicht

```python
snapshot = read_transaction_overview(project_root)
entries = snapshot.filtered("damaged")
```

`transaction_overview.py` scannt höchstens 1.000 Transaktionsverzeichnisse. Gültige Manifeste werden als `prepared`, `trashed` oder `restored` dargestellt. Symlinks, falsche Rechte, ungültige IDs und beschädigte Manifeste erscheinen als `damaged`. Keine Datei wird angelegt oder verändert.

## GUI-Vertrag

`trash_contract_panel.py` zeigt Sicherheitsregeln und die read-only Transaktionsübersicht. Vorhanden sind Zustandsfilter, Liste und read-only Detailfeld. Nicht vorhanden sind Restore-, Reparatur-, Lösch-, Upload- oder Exportaktionen.

## Prüfkommandos

```bash
python3 tools/validate_repository.py
python3 -m unittest tests.test_project_trash -v
python3 -m unittest tests.test_undo_redo -v
python3 -m unittest tests.test_transaction_overview -v
python3 -m unittest tests.test_single_instance_stress -v
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_gui_trash_contract -v
```

## Bekannte Architekturgrenzen

- Prozessabbruch wird über Intent-Recovery modelliert; eine echte Kill-/Stromausfallmatrix folgt separat.
- Journal ist auf 8 MiB und 20.000 Ereignisse begrenzt; Archivierung oder Kompaktierung ist nicht implementiert.
- Eine Redo-Kette kann derzeit nur vollständig abgearbeitet werden; bewusstes Verwerfen benötigt später einen eigenen bestätigten Vertrag.
- eingebettete fremde Mounts in verschobenen Verzeichnissen werden noch nicht rekursiv analysiert.
- produktive GUI-Ausführung bleibt bis P1-001/P1-003 gesperrt.
