# SCHWACHSTELLEN

## Aktuelle bekannte Grenzen

| ID | Schwachstelle | Risiko | Gegenmaßnahme | Status |
|---|---|---:|---|---|
| S-001 | Wayland kann programmgesteuerte Fokusaktivierung begrenzen. | mittel | Fenster sichtbar machen, `requestActivate()` verwenden, physisch unter KDE Wayland prüfen. | offen |
| S-002 | Ereignisjournal besitzt noch keine Rotation oder Archivierung. | mittel | `P3-003` mit Größenlimit und Datenschutztests. | offen |
| S-003 | XDG-Laufzeitpfad kann in ungewöhnlichen Sitzungen fehlen. | mittel | `XDG_RUNTIME_DIR` und `/run/user/<uid>` prüfen; keine `/tmp`-Ausweichlösung. | kontrolliert |
| S-004 | Physische Abnahme auf Kubuntu, X11/Wayland und mehreren DPI-Stufen fehlt. | mittel | `P4-009` mit dokumentierter Testmatrix. | offen |
| S-005 | Produktive Projekt-/Dateiauswahl ist noch nicht angebunden. | hoch | P1-001 und P1-003 vor Freischaltung umsetzen. | absichtlich gesperrt |
| S-006 | Eingebettete fremde Mounts in verschobenen Verzeichnissen werden nicht rekursiv erkannt. | hoch | Linux-Mountinfo vor produktiver Ordnerfreigabe prüfen. | offen |
| S-007 | Gemeinschaftliche ACL-Projekte können durch Eigentümerprüfung blockiert werden. | mittel | ACL-/Gruppenmodell getrennt entwickeln und testen. | bewusst restriktiv |
| S-008 | Dauerhafte Papierkorbleerung ist nicht implementiert. | niedrig | Erst nach Aufbewahrungsvorschau und starker Bestätigung entwickeln. | bewusst ausgeschlossen |
| S-009 | Laufpläne sind auf 1.000 Schritte begrenzt. | niedrig | Begrenzung sichtbar halten; Segmentierung später prüfen. | kontrolliert |
| S-010 | Plan- und Checkpointmigrationen fehlen. | mittel | P3-007 vor Formatänderungen umsetzen. | offen |
| S-011 | Eine vorhandene Lauf- oder Redo-Kette kann nicht verzweigt oder still verworfen werden. | mittel | Nur ausdrücklichen, vollständig protokollierten Abschlussvertrag entwickeln. | bewusst blockiert |
| S-012 | `SIGKILL` prüft Prozessende, nicht Stromverlust oder defekte Hardware-Schreibcaches. | hoch | Spätere VM-/Dateisystemmatrix mit erzwungenem Neustart und dokumentierten Speicherbarrieren. | offen |
| S-013 | Persistente `run.lock`-Datei bleibt nach Laufende bestehen. | niedrig | Kernel-`flock` ist maßgeblich; Reacquire-Test beweist Ressourcenfreigabe. | kontrolliert |
| S-014 | Nur die Papierkorbserie ist als langer Lauf implementiert. | mittel | Weitere Operationen erst über gemeinsame Laufadapter und eigene Invarianten freigeben. | bewusst begrenzt |
| S-015 | Paketinterne Projektpapierkorb-/Journalhilfen sind eng an `run_control.py` gekoppelt. | mittel | Änderungen nur mit kompletter Lauf-, Journal-, Papierkorb- und SIGKILL-Suite. | kontrolliert |

## Bewusst ausgeschlossene Lösungen

- kein Copy-delete-Fallback bei Mountwechsel
- keine dauerhafte Löschung oder automatische Papierkorbleerung
- kein Überschreiben bestehender Restore-Ziele
- kein automatisches Reparieren beschädigter Manifeste, Journale, Pläne oder Checkpoints
- keine globale Lauf- oder Instanzsperre in `/tmp`
- kein Checkpointschreiben durch den externen Abbruchanforderer
- kein Abbruch mitten zwischen Dateioperation und Konsistenzabschlüssen
- kein Diagnoseupload oder automatischer Export

## P0-009 – bekannte Releasegrenzen

- Die Kubuntu-Abnahme läuft containerisiert; gebootete KDE-/SDDM-, X11- und Wayland-VMs bleiben offen.
- SHA-256-Sidecars erkennen Veränderung, ersetzen aber keine kryptografische Herausgebersignatur; `P3-009` bleibt Releaseblocker für Stable.
- `SIGKILL`- und Dateisystemtests beweisen keinen Schutz vor defektem Hardware-Schreibcache oder physischem Stromverlust.
- Der Releasekandidat ist ausschließlich für x86-64 gebaut; ARM64 ist nicht freigegeben.
- Der vollständige Nutzerdaten-Purge ist absichtlich auf einen ausdrücklich bestimmten Nicht-root-Nutzer und bekannte XDG-Pfade begrenzt.
