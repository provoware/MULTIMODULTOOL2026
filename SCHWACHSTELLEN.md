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
| S-016 | `_save_` kennzeichnet eine grüne technische Matrix, aber noch keine kryptografische Herausgebersignatur. | hoch | Bedeutung in README, Hilfe und Releasevertrag klar begrenzen; P3-009 bleibt Pflicht vor Stable. | kontrolliert |
| S-017 | Ein harter Runnerverlust oder eine sofortige Plattformabschaltung kann selbst einen `if: always()`-Upload verhindern. | mittel | Lebenszyklus nach 74 Minuten kontrolliert beenden und sechs Minuten Uploadreserve vor dem 80-Minuten-Joblimit lassen; bestehende Artefakte niemals als vollständig ausgeben, wenn Evidenz fehlt. | bestmöglich kontrolliert |
| S-018 | Ein manueller Workflowabbruch kann je nach Zeitpunkt nur das bis dahin geschriebene Rohprotokoll enthalten. | niedrig | Phase und inneren Exit-Code fortlaufend in gemountete Dateien schreiben; äußerer Exit-Code und Log werden separat gesichert. | kontrolliert |
| S-019 | Release-Finalisierung erzeugt nur Kopien mit `_save_`; Rohartefakte bleiben im kurzlebigen Buildartefakt erhalten. | niedrig | Fertiges Paket separat mit 30 Tagen Aufbewahrung hochladen; Rohartefakte nur 14 Tage behalten und eindeutig als nicht final dokumentieren. | kontrolliert |
| S-020 | Tooltips ersetzen keine vollständige Tastatur-, Screenreader- und physische KDE-Abnahme. | mittel | Zugängliche Beschreibungen und `What’s This` bereitstellen; P2-001 und P4-009 offen halten. | offen |

## Behobene Schwachstellen dieser Finalisierung

| ID | Vorheriger Fehler | Korrektur | Nachweis |
|---|---|---|---|
| F-001 | `${Status}` wurde in der inneren Shell als nicht gesetzte Variable ausgewertet. | Übergabe als wörtlicher `dpkg-query`-Platzhalter `\${Status}`. | Shellsyntax, Repositoryvertrag und Kubuntu-Lebenszyklus |
| F-002 | Fehlerhafte Kubuntu-Läufe konnten ohne vollständiges Rohprotokoll enden. | Phasendatei, innerer/äußerer Exit-Code, Rohlog und `if: always()`-Upload. | Workflow- und Lebenszyklusvertrag |
| F-003 | Ein Jobtimeout ließ keinen sicheren Zeitraum für den Artefaktupload. | Kontrolliertes 74-Minuten-Limit innerhalb des 80-Minuten-Jobs. | Workflowvertrag |
| F-004 | GUI zeigte widersprüchlich `46 %` und `47 %`. | Eine Fortschrittskonstante für Karte und Fortschrittsbalken; Repositoryvalidator gleicht README, TODO und GUI ab. | GUI- und Repositorytest |
| F-005 | Hilfe-Schaltfläche war ohne Funktion; Sperrtexte waren zu allgemein. | Rein lesender Hilfedialog und konkrete Sperrgründe je Schaltfläche. | Offscreen-GUI-Test |
| F-006 | Pauschales Umbenennen releasefähiger Quelldateien hätte Imports und Manifeste zerstört. | `_save_` nur auf atomar erzeugte, geprüfte Releaseausgaben anwenden. | Finalizer-Regressionen und Release-Statusrichtlinie |
| F-007 | Veraltete generierte Ausgabedateien konnten bei manueller Bereinigung übersehen werden. | Finalizer ersetzt den gesamten Zielordner erst nach vollständiger Vorvalidierung atomar. | Stale-Output-Regression |

## Bewusst ausgeschlossene Lösungen

- kein Copy-delete-Fallback bei Mountwechsel
- keine dauerhafte Löschung oder automatische Papierkorbleerung
- kein Überschreiben bestehender Restore-Ziele
- kein automatisches Reparieren beschädigter Manifeste, Journale, Pläne oder Checkpoints
- keine globale Lauf- oder Instanzsperre in `/tmp`
- kein Checkpointschreiben durch den externen Abbruchanforderer
- kein Abbruch mitten zwischen Dateioperation und Konsistenzabschlüssen
- kein Diagnoseupload oder automatischer Export
- keine pauschale `_save_`-Umbenennung von Python-Modulen, Tests, Manifesten oder Startdateien
- keine Behauptung einer Signatur oder Stable-Freigabe allein aufgrund des `_save_`-Zusatzes

## P0-009 – verbleibende Releasegrenzen

- Die Kubuntu-Abnahme läuft containerisiert; gebootete KDE-/SDDM-, X11- und Wayland-VMs bleiben offen.
- SHA-256-Sidecars erkennen Veränderung, ersetzen aber keine kryptografische Herausgebersignatur; `P3-009` bleibt Releaseblocker für Stable.
- `SIGKILL`- und Dateisystemtests beweisen keinen Schutz vor defektem Hardware-Schreibcache oder physischem Stromverlust.
- Der Releasekandidat ist ausschließlich für x86-64 gebaut; ARM64 ist nicht freigegeben.
- Der vollständige Nutzerdaten-Purge ist absichtlich auf einen ausdrücklich bestimmten Nicht-root-Nutzer und bekannte XDG-Pfade begrenzt.
