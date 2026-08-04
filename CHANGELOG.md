# CHANGELOG

Alle wesentlichen Änderungen an Code, Verhalten, Sicherheit, Tests und Dokumentation werden hier chronologisch erfasst.

## Unveröffentlicht – Entwicklungsstand 2026-08-04

### Hinzugefügt – P0-004

- `src/error_events.py` mit zentralem `ErrorEvent`, Diagnosekennungen und vollständigem Nutzervertrag
- `src/error_dialog.py` mit globalem Qt-Dialog und sechs Pflichtfeldern
- XDG-Ereignisjournal `events.jsonl` mit `0600`, `fsync`, Symlink- und Dateitypprüfung
- Geheimnis- und Benutzerpfadfilter für Dialog und Journal
- zentrale Erfassung über `sys.excepthook`, `threading.excepthook` und sichere Qt-`notify`-Schicht
- `SafeOperationError` als Fehlervertrag für spätere Dateioperationen
- `docs/FEHLER_UND_EREIGNISVERTRAG.md`
- `tests/test_error_events.py`
- `tests/test_settings_failpoints.py`

### Verbessert – P0-004

- Bootstrap-, Manifest-, XDG- und Einstellungsfehler werden in denselben verständlichen Vertrag übersetzt
- Einstellungs-Recovery erzeugt ein sichtbares Warnereignis mit unverändertem Datenstand
- Oberfläche zeigt Status und letzte Diagnose des Fehlerzentrums
- Offscreen-GUI-Test prüft nun zusätzlich den vollständigen globalen Fehlerdialog
- Layout-Manifest um maschinenlesbare `errorEventPolicy` erweitert
- Repository-Vertrag um Fehlerarchitektur, Failpoint-Matrix und neue Pflichtdateien erweitert
- Fortschritt auf 36 Prozent, 23 erledigte und 41 offene Punkte aktualisiert

### Failpoint-Sicherheit

- zehn benannte Unterbrechungspunkte vor/nach temporärem Schreiben, `fsync`, Backup, `os.replace` und Nachvalidierung
- jeder Test beweist vollständigen alten oder neuen Aktivzustand
- vorhandene Sicherungen bleiben schema-gültig
- temporäre Dateien werden bei jedem simulierten Fehler entfernt

### Bekannte Grenzen

- Ereignisrotation und Größenbegrenzung folgen mit `P3-003`
- reale KDE-/X11-/Wayland-Abnahme bleibt offen
- produktive Dateioperationen bleiben gesperrt

## 2026-08-04 – P0-003

- versionierte Einstellungen mit Schema 1, `0600`, atomarem Schreiben, Sicherung, Quarantäne und Recovery
- Qt-Offscreen-Smoke-Test für neun Layoutzonen und gesperrte Aktionen

## 2026-08-04 – P0-002

- sichere XDG-Pfadschicht mit `0700`, Vor-/Nachvalidierung und Schreibproben
- workflow-fokussiertes Linux-Layout

## 2026-08-04 – P0-001

- geführter Linux-Einrichtungsassistent mit atomarer `.venv`
