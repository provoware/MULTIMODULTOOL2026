# CHANGELOG

Alle wesentlichen Änderungen an Code, Struktur, Verhalten, Prüfungen und Dokumentation werden hier chronologisch festgehalten.

## [Unreleased]

### Hinzugefügt – 2026-08-04

- geführter Linux-Einrichtungsassistent `tools/setup_assistant.py`
- KDE-KDialog mit Terminal-Rückfall für ausdrückliche Bestätigungen
- `setup.sh` als laiengerechter Einstieg für fehlende Python-Systemkomponenten
- Prüfung von Python, `venv`, KDE-Sitzung, X11/Wayland, Schreibrechten, `.venv` und PySide6
- atomarer Aufbau der virtuellen Umgebung über temporären Ordner und Nachprüfung
- Unit-Tests für Plattform-, Sitzungs-, Bestätigungs-, Pfad- und Symlink-Schutz
- `docs/GITHUB_ZUGRIFF.md` mit Berechtigungs- und Geheimnisvertrag

### Geändert – 2026-08-04

- `start.sh` startet bei unvollständiger Umgebung automatisch den Einrichtungsassistenten
- Repository-Prüfung kontrolliert Einrichtungs- und GitHub-Zugriffsvertrag
- Fortschritt auf 29 Prozent, 18 erledigte und 44 offene Punkte aktualisiert
- Pflichtdokumente an P0-001 und den nächsten Schritt P0-002 angepasst
- GitHub-Rechteprüfung vor Schreibiterationen in `AGENTS.md` verankert

### Sicherheit – 2026-08-04

- keine GitHub-Tokens oder Zugangsdaten im Repository
- `.venv`-Symlinks werden blockiert
- keine Befehlsausführung über `shell=True`
- bestehende `.venv` wird erst nach vollständigem Aufbau und PySide6-Importprüfung ersetzt
- fehlgeschlagene temporäre Einrichtung wird bereinigt; vorhandene Umgebung bleibt erhalten
- Systempakete werden nur nach sichtbarer Bestätigung und als konkrete `apt-get`-Befehle installiert

### Vorheriger Grundstand – 2026-08-04

- startbares PySide6-Linux-Desktop-Grundgerüst mit neun Layoutzonen
- Linux- und Manifestblocker
- Repository-Vertragsprüfer, Unit-Tests und Ubuntu-GitHub-Actions
- verbindliche Linux-, Dokumentations-, Fortschritts- und UI-Verträge
