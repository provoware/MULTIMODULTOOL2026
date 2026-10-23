# Vorrelease-Pflichtmatrix – MULTIMODULTOOL2026

**Stichtag:** 23.10.2026 · **Basis:** `6299d000b4f613383acc17e510bb0386813a6cd5` · **Entwicklungszweig:** `sync/20261023-close-scandir`.

| Pflichtbereich | Bisherige Evidenz | Status / weiterer Schritt |
|---|---|---|
| Fachfunktionen | README meldet P1-001, P1-003–P1-009, P3-009 erledigt | P1-002 Kachelnavigation offen |
| Datensicherheit / Restore | Papierkorb, Journal, Undo/Redo dokumentiert | Nach aktuellem Branch Regression prüfen |
| Fehlerfälle / Sicherheit | Startvalidierung prüft Pfade, Rechte, Mounts | Verzeichnis-Scan wird in diesem Patch explizit geschlossen |
| Design / 800×600 / hohe Skalierung | README nennt Mindestgröße; weitere Screensize-Tests nötig | BLOCKED – Qt-Offscreen-Matrix fehlt |
| Tastatur / Barrierefreiheit | P2-Punkte offen | BLOCKED – Fokus und Kontrast automatisiert prüfen |
| Performance / Wartbarkeit | Python-Module und Prüfstufen vorhanden | R1-Einzelpatch, minimaler Scope |
| Installation / Paketierung | Bestehende CI auf Basis-HEAD grün | Geänderten HEAD erneut prüfen |
| Unit / Regression / Integration | Neuer Regressionsfall bei Erfolgs- und Lesefehlerpfad | Ausführung im vollständigen Checkout offen |
| GUI / Qt | Linux-Desktop-Vertrag | Offscreen- und später Plattformmatrix |
| CI / Dokumentation | Vorherige CI zu altem HEAD grün | Neue CI noch nicht nachgewiesen |
| Release-Kandidat | Noch offene Pflichten | Nicht freigegeben |

## 2026-10-23 – Scandir-Ressourcenfreigabe
- **Befund:** `next(os.scandir(target), None)` beendete den Iterator nicht ausdrücklich.
- **Änderung:** `with os.scandir(target) as entries` und unveränderte Leerzustandsprüfung innerhalb des Kontextmanagers.
- **Wirkung:** Freigabe auch bei Ausnahme; keine Nutzerdatenänderung.
- **Testcode:** `tests/test_start_assistant_scandir.py` erfasst explizites Schließen bei leerem und befülltem Ordner sowie bei simuliertem Lesefehler.
- **Ausgangsnachweis:** Frühere isolierte Testkopie vom 21.10.2026 bestätigt den Ressourcenbefund; Tests auf diesem neuen GitHub-HEAD müssen nachgeholt werden.
- **Restrisiko:** Gering; übrige Startvalidierung unverändert. Pflicht-Gates vor Merge: Syntax, Regressionsmodul, Projektvalidator, Gesamt-Regression gemäß AGENTS.md.
- **PR/Commit:** in GitHub am Branch verifizierbar. Kein Merge und kein Release.
