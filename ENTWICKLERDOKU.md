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
└── trash_contract_panel.py
```

## Projektpapierkorb-API

### Vorschau

```python
preview = preview_trash_move(project_root, source_path)
```

Die Funktion ist rein lesend. Sie prüft Projektgrenze, Quelltyp, Symlinks, Hardlinks, Mountstatus, Schreibrechte, freien Speicher und Transaktionskonflikte. Der Quellfingerabdruck besteht aus Dateisystemgerät, Inode, Modus, Größe, Nanosekunden-Mtime und Typ.

### Ausführung

```python
result = execute_trash_move(preview)
```

Ablauf:

1. Vorschau gegen den aktuellen Quellfingerabdruck nachvalidieren.
2. private Projektpfade mit `0700` anlegen.
3. Manifest `prepared` atomar mit `0600` schreiben und `fsync` ausführen.
4. Quelle mit `os.replace` nach `payload` verschieben.
5. Quell- und Transaktionsverzeichnis mit `fsync` bestätigen.
6. Manifest atomar auf `trashed` setzen.

Es existiert kein Copy-delete-Zweig.

### Wiederherstellung

```python
result = restore_transaction(project_root, transaction_id)
```

Vor dem atomaren Restore werden Manifest, ID, Pfadgrenzen, Payloadtyp, Fingerabdruck, Dateisystem, Elternordner und Zielkonflikt geprüft. `prepared` mit vorhandenem vollständigem Payload ist ein kontrollierter Recovery-Zustand.

### Fehler

Alle Blockaden erzeugen `SafeOperationError(category="project-trash")`. Dadurch werden Ursache, Folge, Datenstand, Lösung, Diagnosekennung und sicherer nächster Schritt zentral dargestellt und protokolliert.

## Single-Instance-Stresstest

`tests/test_single_instance_stress.py` startet eine Primärinstanz und 20 per Barrier nahezu gleichzeitig freigegebene Zweitinstanzen. Jede sendet eine eindeutige Diagnosekennung. Abnahme:

- alle Zweitstarts erhalten die Sekundärrolle,
- exakt 20 eindeutige Nachrichten kommen an,
- jede Kennung erscheint genau einmal,
- nach `close()` fehlen Socket und Metadaten,
- das private App-Laufzeitverzeichnis ist leer.

## GUI-Vertrag

`src/trash_contract_panel.py` ist ein eigenständiges read-only Qt-Panel ohne PySide6-Import zur Modulzeit. Es besitzt keine Aktion zum Leeren oder dauerhaften Löschen. Die produktive Integration in den geführten Projektworkflow folgt erst nach sicherer Projekt- und Ordnerauswahl.

## Prüfkommandos

```bash
python3 tools/validate_repository.py
python3 -m unittest tests.test_project_trash -v
python3 -m unittest tests.test_single_instance_stress -v
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_gui_trash_contract -v
```

## Bekannte Architekturgrenzen

- eingebettete fremde Mounts innerhalb eines als Ganzes verschobenen Verzeichnisses werden noch nicht rekursiv analysiert,
- gemeinschaftliche Projekte mit fremdem Eigentümer oder komplexen ACLs werden blockiert,
- produktive GUI-Ausführung bleibt bis P1-001/P1-003 gesperrt,
- transaktionsübergreifendes Undo/Redo folgt mit P0-007.
