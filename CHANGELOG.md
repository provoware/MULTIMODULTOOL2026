# CHANGELOG

Alle wesentlichen Änderungen an Code, Struktur, Verhalten, Prüfungen und Dokumentation werden hier chronologisch festgehalten.

## [Unreleased]

### Hinzugefügt – 2026-08-04

- zentrale XDG-Pfadschicht `src/xdg_paths.py` für Konfiguration, Nutzerdaten, Cache, Status, Logs und Sicherungen
- Vor- und Nachvalidierung für absolute Pfade, XDG-Grenzen, Quellbaumtrennung, Symlinks, doppelte Ziele, Verzeichnistypen und Schreibrechte
- private App-Verzeichnisse mit Modus `0700` und rückstandsfreier Schreibprobe
- Diagnosemodus `python3 -m src.main --paths-only`
- sieben Unit-Tests für XDG-Auflösung, Grenzschutz, Symlinkblockade, Rechte und Quellbaumtrennung
- `docs/XDG_PFADVERTRAG.md`
- geführter Linux-Einrichtungsassistent `tools/setup_assistant.py`
- KDE-KDialog mit Terminal-Rückfall für ausdrückliche Bestätigungen
- `setup.sh` als laiengerechter Einstieg für fehlende Python-Systemkomponenten
- Prüfung von Python, `venv`, KDE-Sitzung, X11/Wayland, Schreibrechten, `.venv` und PySide6
- atomarer Aufbau der virtuellen Umgebung über temporären Ordner und Nachprüfung
- Unit-Tests für Plattform-, Sitzungs-, Bestätigungs-, Pfad- und Symlink-Schutz
- `docs/GITHUB_ZUGRIFF.md` mit Berechtigungs- und Geheimnisvertrag

### Geändert – 2026-08-04

- Oberfläche workflow-fokussiert überarbeitet: nummerierte Schritte, sichtbare Sperrzustände, hervorgehobener nächster Schritt und Speicher-/Diagnoseleiste
- normaler Programmstart bereitet XDG-Verzeichnisse sicher vor; `--validate-only` bleibt rein lesend
- Repository-Prüfung um XDG-Vertrag, neue Pflichtdateien und Python-Syntax erweitert
- Fortschritt auf 31 Prozent, 19 erledigte und 43 offene Punkte aktualisiert
- `start.sh` startet bei unvollständiger Umgebung automatisch den Einrichtungsassistenten
- Repository-Prüfung kontrolliert Einrichtungs- und GitHub-Zugriffsvertrag
- GitHub-Rechteprüfung vor Schreibiterationen in `AGENTS.md` verankert

### Sicherheit – 2026-08-04

- Start wird bei relativen XDG-Werten, Zielüberschneidung mit dem Programmverzeichnis, App-Symlinks, doppelten Zielen oder fehlender Schreibbarkeit blockiert
- Programmcode schreibt keine Konfiguration, Logs, Sicherungen oder Nutzerdaten in den Quellbaum
- temporäre Schreibproben werden nach `fsync` vollständig entfernt
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
