# CHANGELOG

Alle wesentlichen Änderungen an Code, Struktur, Verhalten, Prüfungen und Dokumentation werden hier chronologisch festgehalten.

## [Unreleased]

### Hinzugefügt – 2026-08-04

- startbares PySide6-Linux-Desktop-Grundgerüst mit allen neun verbindlichen Layoutzonen
- Manifestprüfung vor dem grafischen Start
- expliziter Linux-Plattformblocker für Nicht-Linux-Systeme
- startfreier Diagnosemodus `python3 -m src.main --validate-only`
- laiengerechte Linux-Startroutine `start.sh`
- zentrales QSS-Grundtheme in `src/theme.qss`
- automatischer Repository-Vertragsprüfer
- Unit-Tests für Manifest, Linux-Plattformvertrag, Zonenfolge und Repository-Vertrag
- GitHub-Actions-Workflow auf Ubuntu für jeden Push und Pull Request
- `ANLEITUNG_TOOL.md`
- `TODO.md` mit 62 atomaren, priorisierten und prüfbaren Punkten
- `SCHWACHSTELLEN.md`
- `UPGRADE_POOL.md`
- `ENTWICKLERDOKU.md`

### Geändert – 2026-08-04

- Projektumfang verbindlich auf Linux-Desktop-Systeme begrenzt
- Kubuntu 22.04/24.04, KDE Plasma, X11 und Wayland als primärer Zielrahmen festgelegt
- `README.md` um verbindlichen Fortschrittsblock, Linux-Zielumfang, Schnellstart, Prüfungen und aktuellen Funktionsumfang erweitert
- `AGENTS.md` um Linux-Plattformvertrag, Dokumentationspflege, Fortschrittsvertrag, TODO-Qualitätsregeln und Pflichtprüfungen erweitert
- `layout-manifest.json` um maschinenlesbaren Linux-Plattformvertrag ergänzt

### Sicherheit – 2026-08-04

- GUI-Start wird auf Nicht-Linux-Systemen sowie bei ungültigem oder fehlendem Layout-Manifest blockiert
- Referenzpfad darf das Projektverzeichnis nicht verlassen
- produktive Dateioperationen bleiben bis zur Umsetzung von Linux-Datenpfad-, Backup-, Papierkorb- und Undo-Verträgen deaktiviert
