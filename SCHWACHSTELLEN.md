# SCHWACHSTELLEN

## Aktuelle bekannte Grenzen

| ID | Schwachstelle | Risiko | Gegenmaßnahme | Status |
|---|---|---:|---|---|
| S-001 | Wayland kann programmgesteuerte Fokusaktivierung begrenzen. | mittel | Fenster sichtbar machen, `requestActivate()` verwenden, physisch unter KDE Wayland prüfen. | offen |
| S-002 | Ereignisjournal besitzt noch keine Rotation oder Archivierung. | mittel | `P3-003` mit Größenlimit, Rotation und Datenschutztests. | offen |
| S-003 | XDG-Laufzeitpfad kann in ungewöhnlichen Sitzungen fehlen. | mittel | `XDG_RUNTIME_DIR` und `/run/user/<uid>` sicher prüfen; keine `/tmp`-Ausweichlösung. | kontrolliert |
| S-004 | Laufender, aber blockierter Altprozess kann eine neue Instanz verhindern. | niedrig | Sperre nicht erzwingen; vollständige Diagnose ausgeben. | bewusst sicher |
| S-005 | Diagnoseansicht lädt höchstens 2 MiB und 500 Einträge. | niedrig | Begrenzung sichtbar melden; Rotation folgt `P3-003`. | kontrolliert |
| S-006 | Physische Abnahme auf Kubuntu, X11/Wayland und mehreren DPI-Stufen fehlt. | mittel | `P4-009` mit dokumentierter Testmatrix. | offen |
| S-007 | Produktive Dateioperationen sind noch nicht freigegeben. | hoch | Papierkorb, Undo und Wiederanlauf zuerst umsetzen. | absichtlich gesperrt |

## Bewusst ausgeschlossene Lösungen

- keine globale Lock-Datei in `/tmp`
- kein automatisches Beenden einer angeblich alten Instanz
- kein Entfernen beschädigter Sperren ohne eindeutige Prüfung
- keine Weitergabe beliebiger Kommandozeilenargumente
- kein Diagnoseupload oder automatischer Export
