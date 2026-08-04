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
└── diagnostics_center.py
```

## Single-Instance-Lebenszyklus

1. Plattform, Manifest und XDG-Pfade prüfen.
2. Ereignisjournal sicher öffnen.
3. XDG-Laufzeitwurzel aus `XDG_RUNTIME_DIR` oder `/run/user/<uid>` bestimmen.
4. App-Laufzeitverzeichnis mit `0700` prüfen oder anlegen.
5. Vorhandenen Socket kontaktieren.
6. Bei erfolgreicher Übergabe als sekundäre Instanz mit Exitcode 0 enden.
7. Bei nicht erreichbarem Socket Metadaten, Boot-ID und Prozesszustand prüfen.
8. Nur eindeutig veraltete Sperre entfernen; beschädigte Sperre blockieren.
9. Primären Socket binden, auf `0600` setzen und Metadaten atomar schreiben.
10. Serverthread starten; Qt-Hauptthread liest Nachrichten über Queue und QTimer.
11. Beim Beenden nur eigene Socket- und Metadatendateien entfernen.

## Nachrichtenvertrag

```json
{"schemaVersion":1,"action":"activate"}
```

oder:

```json
{"schemaVersion":1,"action":"show-diagnostics","diagnosticId":"MMT-XDG-20260804-ABCD1234"}
```

Unbekannte Felder, Aktionen, Diagnoseformate, Pfade und freie Argumente werden verworfen. Nachrichten sind auf 4096 Bytes begrenzt. Der Server akzeptiert nur die Peer-UID des aktuellen Nutzers.

## Wayland

`showNormal()`, `raise_()`, `activateWindow()` und `QWindow.requestActivate()` werden kombiniert. Wayland-Compositoren können Fokusdiebstahl begrenzen; das Fenster wird dennoch sichtbar gemacht und die interne Diagnose fokussiert. Physische KDE-Wayland-Abnahme bleibt erforderlich.

## Diagnosezentrale

`read_diagnostics()` öffnet mit `O_RDONLY`, `O_CLOEXEC` und `O_NOFOLLOW`, prüft Dateityp, Eigentümer, Hardlinkzahl und `0600`, liest höchstens 2 MiB und 500 gültige Datensätze und verändert das Journal nicht.

`DiagnosticsController` besitzt nur Filter, Liste, read-only Detailfeld und Kopierknopf. Methoden für Löschen, Upload oder Export existieren nicht.

## Fehlerintegration

Instanzprobleme werden als `single-instance` oder `single-instance-runtime` über `ErrorEventCenter` erfasst. Sichere Stale-Recovery erzeugt `single-instance-recovery`. Alle Ereignisse besitzen die sechs Pflichtfelder.

## Tests

- `tests/test_single_instance.py`: Nachrichtengrenzen, Zweitstart, Cleanup, stale und beschädigte Sperren
- `tests/test_diagnostics_center.py`: read-only Zugriff, Rechte, Symlink, ungültige Zeilen, Filter und Grenzen
- `tests/test_gui_offscreen.py`: neun Zonen, Diagnosewidgets, verbotene Aktionen und Fehlerdialog
- bestehende Einstellungs-, XDG-, Fehler- und Failpoint-Tests bleiben verpflichtend
