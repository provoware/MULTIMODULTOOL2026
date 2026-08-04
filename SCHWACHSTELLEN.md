# SCHWACHSTELLEN

## Bewertungslogik

- **Blocker:** Datenverlust, unsicherer Start oder falsche Erfolgsbehauptung
- **Hoch:** sicherheitskritische Funktion unvollständig
- **Mittel:** reale Linux-Abnahme oder Wartbarkeit offen
- **Niedrig:** Komfort- oder Dokumentationsrest

## Aktuelle Schwachstellen

| ID | Risiko | Stufe | Gegenmaßnahme | Status |
|---|---|---:|---|---|
| S-001 | produktive Dateiaktionen besitzen noch keinen Papierkorb/Undo | Blocker | Aktionen gesperrt lassen; P0-006/P0-007 umsetzen | offen |
| S-002 | parallele Starts könnten später konkurrierende Zustände erzeugen | hoch | P0-005 Single-Instance-Schutz | offen |
| S-003 | Ereignisjournal besitzt noch keine Rotation/Größenbegrenzung | mittel | P3-003 mit atomarer Rotation und Datenschutzfilter | offen |
| S-004 | physische KDE-Abnahme unter X11/Wayland fehlt | mittel | P4-009 auf Kubuntu 22.04/24.04 | offen |
| S-005 | Qt-Offscreen-Test ersetzt keine DPI-/Fenstermanager-Abnahme | mittel | reale Tests 1024×680 bis 4K und 80–200 % | offen |
| S-006 | Crash zwischen Kernel-/Datenträgergrenzen kann hardwareabhängig sein | mittel | Failpoint-Matrix plus spätere VM-/Dateisystemtests | teilweise reduziert |
| S-007 | Journalfehler können vor GUI-Start nur in Konsole erscheinen | niedrig | vollständiger Konsolenvertrag; später Startdiagnose-Dialog im Launcher | akzeptiert |
| S-008 | technische Details können unbekannte Geheimnisformate enthalten | mittel | Filter erweitern, private Inhalte nie bewusst übergeben, Tests ausbauen | offen |
| S-009 | keine externe Crashdump-Auswertung | niedrig | erst nach Datenschutz- und Einwilligungsdesign bewerten | zurückgestellt |
| S-010 | Einstellungen besitzen noch keine Schema-Migration >1 | hoch | P3-007 idempotente Migration und Rückfall | offen |

## Bereits reduzierte Risiken

- XDG-Pfade, Symlinks und Rechte werden vor/nach Anlage geprüft.
- Einstellungen werden atomar geschrieben und automatisch wiederhergestellt.
- zehn Failpoints beweisen alte-oder-neue Vollständigkeit.
- unbehandelte Hauptthread-, Worker- und Qt-Ausnahmen werden zentral erfasst.
- jeder Fehler nennt Datenstand und sicheren nächsten Schritt.
- Geheimnismuster und Benutzerpfade werden vor Logging reduziert.

## Freigabegrenze

Kein produktiver Einsatz auf unersetzlichen Daten, bevor P0-005 bis P0-008 abgeschlossen und physisch abgenommen sind.
