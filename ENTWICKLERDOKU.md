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
├── run_control.py
└── trash_contract_panel.py
```

## Laufsteuerungs-API

### Lauf anlegen

```python
snapshot = create_run(project_root, source_paths)
```

Die Funktion validiert alle Quellen rein lesend über den Papierkorbvertrag, verhindert doppelte Pfade, erzeugt eine eindeutige Lauf-ID und schreibt `plan.json` sowie den initialen `checkpoint.json` atomar in einen privaten Laufordner.

### Lauf fortsetzen

```python
result = resume_run(project_root, run_id)
```

Optional:

```python
result = resume_run(
    project_root,
    run_id,
    allow_cancelled=True,
    max_steps=10,
    failpoint=callback,
)
```

`max_steps` begrenzt kontrolliert die in einem Aufruf ausgeführten Schritte. `failpoint` ist ausschließlich eine injizierte Testschnittstelle und aktiviert ohne übergebenen Callback keine Umgebungsschalter.

### Abbruch anfordern

```python
snapshot = request_cancel(project_root, run_id)
```

Die Anforderung schreibt nur `cancel.request`. Sie erwirbt nicht die Ausführungssperre und schreibt niemals den Checkpoint. Der aktive Lauf ist alleiniger Checkpointschreiber und bestätigt den Abbruch an der nächsten sicheren Grenze.

### Lauf prüfen

```python
snapshot = inspect_run(project_root, run_id)
```

Diese Funktion liest Plan und Checkpoint ausschließlich mit `O_RDONLY` und `O_NOFOLLOW`, validiert Eigentümer, Dateityp, Hardlinks, Rechte, Größe, Planhash und Checkpointinvarianten und verändert keine Datei.

## Datenmodelle

### `RunPlan`

- Schemaversion
- Lauf-ID
- Operation `project-trash-batch`
- Erstellungszeit
- lückenlose `RunItem`-Liste
- Planhash

### `RunCheckpoint`

- Zustand und nächste Schrittposition
- lückenlose abgeschlossene Indizes
- Versuchszähler
- optionaler `CurrentStep`
- monotone Generation
- Zeitstempel
- Abbruchkennzeichen und Nutzertext

### `CurrentStep`

- Schrittindex
- Versuch
- Aktions-ID
- Transaktions-ID
- relativer Projektpfad

Die IDs werden vor dem Intent im Checkpoint persistiert. Dadurch kann ein Prozess vor dem ersten Journalereignis sterben, ohne beim Neustart neue Identitäten oder Doppelaktionen zu erzeugen.

## Checkpoint-Schreibweg

1. vollständige Struktur validieren,
2. JSON in private Datei im selben Laufordner schreiben,
3. Datei `0600`, vollständige Schreibschleife,
4. Datei-`fsync`,
5. `os.replace`,
6. Verzeichnis-`fsync`,
7. Datei mit `O_NOFOLLOW` erneut lesen,
8. JSON-Wert byteunabhängig nachvalidieren,
9. temporäre Datei entfernen.

## Schritt-Recovery

### Checkpoint ohne Journal

Quelle vorhanden, Transaktionsordner fehlt: derselbe aktuelle Schritt wird mit gespeicherter Aktions- und Transaktions-ID gestartet.

### `prepare` ohne Transaktion

Intent bleibt bestehen. Die Transaktion wird mit derselben ID aufgebaut; `prepare` wird nicht doppelt angehängt.

### `prepared` ohne Payload

Manifest und Quelle werden erneut geprüft. Der Schritt setzt direkt vor `os.replace` fort.

### Payload ohne Manifestabschluss

Quell- und Transaktionsverzeichnis werden erneut mit `fsync` bestätigt, Manifest wird auf `trashed` gesetzt und danach nur das fehlende `apply` angehängt.

### Journalabschluss ohne Checkpoint

Die Dateioperation wird nicht wiederholt. Nur `completedIndices`, `nextIndex` und Checkpointgeneration werden fortgeschrieben.

## SIGKILL-Testarchitektur

`tests/helpers/run_control_worker.py` startet einen realen Unterprozess. Ein injizierter Failpoint schreibt zunächst eine private Markierungsdatei mit `fsync` und beendet den Prozess dann mit `SIGKILL`.

`tests/test_run_control_sigkill.py` wiederholt den vollständigen Neuaufbau für zehn Stufen. Danach wird der Lauf in einem neuen Prozesskontext fortgesetzt und auf folgende Invarianten geprüft:

- Zustand `completed`,
- exakt eine Journalaktion,
- keine pending Aktion,
- exakt ein Payload,
- gültiges Manifest,
- kein Originalobjekt,
- keine `.tmp`-Datei,
- zweiter Resume-Aufruf ohne Änderung.

## Kritische Kopplung

`run_control.py` verwendet paketinterne, bereits getestete Primitive aus `project_trash.py` und `undo_redo.py`. Die Kopplung ist bewusst eng, damit Manifest- und Journalformate nicht dupliziert werden. Änderungen an privaten Hilfsfunktionen müssen die Lauf- und SIGKILL-Tests zwingend mit ausführen.

## Prüfkommandos

```bash
python3 tools/validate_repository.py
python3 -m src.main --validate-only
python3 -m unittest tests.test_run_control -v
python3 -m unittest tests.test_run_control_sigkill -v
python3 -m unittest tests.test_undo_redo -v
python3 -m unittest tests.test_project_trash -v
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_gui_trash_contract -v
```

## Bekannte Architekturgrenzen

- nur sequenzielle Projektpapierkorbserien sind als lange Operation freigegeben,
- kein Plan-Branching oder Verwerfen einer Redo-/Laufkette,
- keine Schema-Migration für alte Laufcheckpoints,
- `SIGKILL` bildet keinen echten Stromverlust mit Hardwarecache ab,
- produktive GUI-Ausführung bleibt bis P1-001/P1-003 gesperrt.
