# CHANGELOG

Alle wesentlichen Änderungen an Code, Struktur, Verhalten, Prüfungen und Dokumentation werden chronologisch festgehalten.

## [Unreleased]

### Hinzugefügt – 2026-08-04

- `src/settings_manager.py` als Standardbibliotheksmodul für versionierte Einstellungen
- `standards/settings-schema-v1.json` mit strikt verbotenen unbekannten Feldern
- aktive Datei `settings.json` und letzte gültige Sicherung `settings.last-valid.json`
- Vorvalidierung von Version, Feldern, Typen, Wertebereichen, Sicherheitswerten, Pfaden, Symlinks und Dateirechten
- atomarer Schreibweg über temporäre Datei, `fsync`, Nachvalidierung und `os.replace`
- Quarantäne beschädigter Dateien als `settings.corrupt-<UTC-Zeit>.json`
- automatischer Rollback aus Sicherung oder sichere Standardwerte
- rein lesender Diagnosemodus `python3 -m src.main --settings-only`
- 15 Unit-Tests für Schema, Transaktion, Sicherung, Recovery, Symlinks, Rechte und Fehlerfälle
- `docs/EINSTELLUNGSVERTRAG.md`
- automatisierter Qt-Offscreen-GUI-Smoke-Test mit fünf Pflichtprüfungen

### Geändert – 2026-08-04

- `src/main.py` bindet XDG- und Einstellungsprüfung in den Startablauf ein
- Oberfläche zeigt Einstellungsstatus, Rollback-Bereitschaft und den nächsten P0-Schritt
- alle neun Layoutzonen besitzen maschinenprüfbare Objekt- und Zonenkennungen
- Arbeits- und Kontextbereich sind unabhängig scrollbar
- noch nicht freigegebene Aktionen bleiben sichtbar, erklärt und deaktiviert
- GitHub Actions installiert PySide6 und führt den Offscreen-Smoke-Test aus
- Repository-Vertrag prüft Einstellungs-, Schema-, GUI- und Fortschrittsvertrag
- Fortschritt auf 33 Prozent, 21 erledigte und 42 offene Punkte aktualisiert
- Pflichtdokumentation an P0-003 und D-018 angepasst

### Sicherheit – 2026-08-04

- Einstellungsdateien verwenden Modus `0600`
- Konfigurationsverzeichnis bleibt XDG-konform und mit `0700` geschützt
- unbekannte Versionen, Felder und unsichere Werte werden vor Schreibzugriff blockiert
- temporäre Dateien werden in jedem Fehlerfall entfernt
- defekte Einstellungen schalten keine produktiven Funktionen frei
- rein lesende Diagnose verändert keine XDG- oder Einstellungsdatei
- GUI-Smoke-Test verwendet keine privaten Nutzerdaten

### Bereits umgesetzt – 2026-08-04

- geführter Linux-Einrichtungsassistent mit atomarer `.venv`
- sichere XDG-Pfadverwaltung für Konfiguration, Daten, Cache, Status, Logs und Sicherungen
- Linux-, Manifest-, Dokumentations- und GitHub-Zugriffsvertrag
- startbares PySide6-Grundgerüst mit neun verbindlichen Layoutzonen
