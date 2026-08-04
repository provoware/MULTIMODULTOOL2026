# ENTWICKLERDOKU

## 1. Technischer Stand

- ausschließlich Linux-Desktop
- Kubuntu 22.04/24.04, KDE Plasma, X11/Wayland, x86-64
- Python 3.10+
- PySide6 / Qt Widgets
- Start: `./start.sh`
- Einrichtung: `./setup.sh`
- Fortschritt: 36 Prozent, 23 erledigt, 41 offen

## 2. Startfluss

```text
start.sh
  ├─ Linux/Python/.venv/PySide6 prüfen
  ├─ bei Bedarf setup.sh
  └─ python -m src.main
       ├─ Plattform und Manifest rein lesend prüfen
       ├─ XDG-Pfade berechnen und sicher anlegen
       ├─ EventJournal im XDG-Logpfad validieren
       ├─ Einstellungen laden oder wiederherstellen
       ├─ Recovery-Ereignis zentral protokollieren
       ├─ SafeApplication + Exception-Hooks installieren
       └─ Qt-Oberfläche mit Z01–Z09 starten
```

## 3. Fehler- und Ereignisarchitektur

### `src/error_events.py`

- `ErrorEvent`: unveränderlicher Nutzer- und Logvertrag
- `create_event()`: erzwingt alle Pflichtfelder
- `event_from_exception()`: übersetzt beliebige Ausnahmen
- `event_from_messages()`: übersetzt Listen aus Validatoren
- `event_from_settings_result()`: übersetzt Recovery/Blockade
- `SafeOperationError`: verbindliche spätere Dateioperationsfehler
- `EventJournal`: private JSONL-Datei mit `0600` und `fsync`
- `ErrorEventCenter`: zentraler In-Memory-/Journal-Verteiler
- `install_exception_hooks()`: Hauptthread und Worker-Threads

### `src/error_dialog.py`

Der Qt-Dialog bleibt vom Kernmodul getrennt. `error_events.py` importiert PySide6 nicht und bleibt in CI/Diagnose ohne GUI-Abhängigkeit testbar.

Objektkennungen:

- `errorCause`
- `errorConsequence`
- `errorDataState`
- `errorSolution`
- `errorDiagnosticId`
- `errorNextStep`

### `src/main.py`

- `cli_entrypoint()` fängt unerwartete Bootstrap-Ausnahmen ab.
- `SafeApplication.notify()` fängt Qt-Ereignisausnahmen ab.
- ein Qt-Signal transportiert Worker-/Hook-Ereignisse sicher in den GUI-Thread.
- Manifest-, XDG- und Settings-Fehler verwenden denselben Vertrag.

## 4. Datenschutz

`sanitize_text()`:

- ersetzt Benutzerverzeichnis durch `~`,
- entfernt typische GitHub-Token, Bearer-, Passwort-, Secret- und API-Key-Muster,
- entfernt Steuerzeichen,
- begrenzt Länge technischer Details.

Das Journal enthält keine privaten Dateiinhalte. Eine vollständige Logrotation folgt erst mit `P3-003`.

## 5. Einstellungs-Failpoints

`write_settings(..., failpoint=...)` akzeptiert optional einen Test-Hook. Ohne Hook bleibt das Produktionsverhalten unverändert.

Deklarierte Punkte:

```text
before_temp_write
after_temp_write
before_fsync
after_fsync
before_backup
after_backup
before_replace
after_replace
before_postvalidate
after_postvalidate
```

`FailpointController` löst genau am gewählten Punkt `InjectedFailpoint` aus. Der Transaktionscode entfernt temporäre Dateien und liefert ein blockiertes, diagnostizierbares Ergebnis.

## 6. Zustandsinvariante

Nach jedem simulierten Ausfall gilt:

```text
aktive Einstellungen ∈ {vollständige alte Version, vollständige neue Version}
```

Zusätzlich:

- jede vorhandene Sicherung ist JSON- und schema-gültig,
- keine temporäre Datei bleibt zurück,
- keine Teilkonfiguration wird akzeptiert.

## 7. Wichtige Dateien

| Datei | Verantwortung |
|---|---|
| `src/error_events.py` | zentrales Ereignismodell, Filter, Hooks, Journal |
| `src/error_dialog.py` | globaler Qt-Fehlerdialog |
| `src/main.py` | Bootstrap-, XDG-, Settings- und Qt-Integration |
| `src/settings_manager.py` | atomare Einstellungen und Failpoints |
| `tests/test_error_events.py` | Ereignis-, Journal-, Filter- und Hooktests |
| `tests/test_settings_failpoints.py` | zehnstufige Ausfallmatrix |
| `tests/test_gui_offscreen.py` | Zonen-, Scroll-, Sperr- und Dialogprüfung |
| `docs/FEHLER_UND_EREIGNISVERTRAG.md` | verbindlicher Nutzer-/Sicherheitsvertrag |

## 8. Lokale Prüfungen

```bash
python3 -m py_compile src/*.py tests/*.py tools/*.py
python3 -m src.main --validate-only
python3 tools/validate_repository.py
python3 -m unittest discover -s tests -v
python3 -m unittest tests.test_settings_failpoints -v
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_gui_offscreen -v
```

## 9. Entwicklungsregeln

- Fehlerlogik bleibt von Widgets getrennt.
- neue Dateioperationen verwenden zentrale Ereignistypen.
- technische Details dürfen Pflichtfelder nicht ersetzen.
- keine Geheimnisse oder private Dateiinhalte in Journal/Dialogs.
- kein Start ohne sicheres Ereignisjournal nach XDG-Anlage.
- Failpoints bleiben explizite Testinjektion; keine Umgebungsvariable aktiviert sie unbemerkt.

## 10. Nächste Architekturgrenze

`P0-005` führt einen Linux-Single-Instance-Schutz ein. Ein zweiter Start muss sicher an die bestehende Instanz übergeben werden und alle Fehler über die neue Ereignisschicht melden.
