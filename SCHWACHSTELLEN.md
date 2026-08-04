# SCHWACHSTELLEN

## Aktuelle bekannte Grenzen

| ID | Schwachstelle | Risiko | Gegenmaßnahme | Status |
|---|---|---:|---|---|
| S-001 | Wayland kann programmgesteuerte Fokusaktivierung begrenzen. | mittel | Fenster sichtbar machen, `requestActivate()` verwenden, physisch unter KDE Wayland prüfen. | offen |
| S-002 | Ereignisjournal besitzt noch keine Rotation oder Archivierung. | mittel | `P3-003` mit Größenlimit und Datenschutztests. | offen |
| S-003 | XDG-Laufzeitpfad kann in ungewöhnlichen Sitzungen fehlen. | mittel | `XDG_RUNTIME_DIR` und `/run/user/<uid>` prüfen; keine `/tmp`-Ausweichlösung. | kontrolliert |
| S-004 | Diagnoseansicht lädt höchstens 2 MiB und 500 Einträge. | niedrig | Begrenzung sichtbar melden; Rotation folgt `P3-003`. | kontrolliert |
| S-005 | Physische Abnahme auf Kubuntu, X11/Wayland und mehreren DPI-Stufen fehlt. | mittel | `P4-009` mit dokumentierter Testmatrix. | offen |
| S-006 | Produktive Papierkorbbedienung ist noch nicht an sichere Projekt-/Dateiauswahl angebunden. | hoch | P1-001 und P1-003 vor Freischaltung umsetzen. | absichtlich gesperrt |
| S-007 | Verzeichnisse werden atomar als Ganzes verschoben; eingebettete fremde Mounts werden nicht rekursiv erkannt. | hoch | Vor späterer Ordnerfreigabe Mountbaum per Linux-Mountinfo prüfen. | offen |
| S-008 | Projektstamm muss dem aktuellen Nutzer gehören; gemeinsame ACL-Projekte können blockiert werden. | mittel | ACL-/Gruppenmodell separat entwickeln und testen, keine voreilige Lockerung. | bewusst restriktiv |
| S-009 | Dauerhafte Papierkorbleerung ist nicht implementiert. | niedrig | Erst nach Undo, Aufbewahrungsvorschau und starker Bestätigung entwickeln. | bewusst ausgeschlossen |
| S-010 | Restore setzt voraus, dass der ursprüngliche Elternordner noch existiert. | mittel | Später geführte Wiederherstellungsalternative ohne stilles Neuanlegen ergänzen. | offen |
| S-011 | Transaktionsmanifest kann nach einem erfolgreichen Move im Zustand `prepared` verbleiben, falls die zweite Manifestaktualisierung ausfällt. | mittel | Recovery erkennt den vollständigen Payload und erlaubt kontrollierten Restore; Journal-/Reconcile-Ansicht später ergänzen. | kontrolliert |
| S-012 | Single-Instance-Stresstest läuft in CI, aber noch nicht physisch unter stark ausgelastetem KDE. | niedrig | Lasttest auf realem Kubuntu ergänzen. | offen |

## Bewusst ausgeschlossene Lösungen

- kein Copy-delete-Fallback bei Mountwechsel
- keine dauerhafte Löschung oder automatische Papierkorbleerung
- kein Überschreiben bestehender Restore-Ziele
- kein automatisches Reparieren beschädigter Manifeste
- keine globale Lock-Datei in `/tmp`
- kein Entfernen beschädigter Instanzsperren ohne eindeutige Prüfung
- kein Diagnoseupload oder automatischer Export
