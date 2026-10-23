# Vorrelease-Pflichtmatrix – MULTIMODULTOOL2026

**Stichtag:** 23.10.2026 · **Basis:** `476b7688fd181221eb956ddeb9cd8546b70bf777` · **Entwicklungszweig:** `fix/20261023-qt-gate-productive-ui`.

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

## 2026-10-23 – GUI-Integration und wahrheitsgetreues Qt-Gate

- **Befund auf `main`:** Der GUI-Aufbau band die vorhandene produktive Oberfläche und den geführten Startassistenten nicht ein. Die Qt-Offscreen-Tests wurden selbst nach erfolgreicher PySide6-Installation als **skipped** gemeldet. Der CI-Job war grün, obwohl die betreffenden GUI-Funktionen nicht geprüft wurden.
- **Arbeitspaket:** Vorhandenen geführten Workflow in `build_window` anbinden, Navigations-Aktivzustand und sichtbaren Zurück-Pfad ergänzen. Bestehende Sicherheitsmodus- und Bestätigungsgrenzen bleiben maßgeblich.
- **Test:** Neuer Offscreen-Test für Aktivzustand, Navigation und Zurück. CI verlangt vor GUI-Tests einen erfolgreichen QtCore-/QtWidgets-Import; erforderliche native Laufzeitbibliotheken werden installiert.
- **Erwartete Wirkung:** Die zuvor nur vorhandenen, aber nicht angebundenen Fachmodule werden erreichbar. Eine fehlende Qt-Laufzeit darf die GUI-Abnahme nicht mehr unbemerkt überspringen.
- **Risikoklasse:** R3 (CI-Gate) mit R1 (GUI-Verdrahtung); kein Datenformatwechsel, keine Migration, kein automatischer Schreibzugriff.
- **Status:** Implementiert auf Entwicklungszweig; **PASS erst nach realem Qt-Test und grünen GitHub-Gates**. Container ersetzt keine physische Kubuntu-/KDE-Sichtprüfung.
- **Offen:** 800×600 und 200-%-Skalierung, Tastaturmatrix, Barrierefreiheit, vollständige Integrations- und reale Desktopabnahme sowie alle noch nicht erledigten TODO-Pflichten.
- **Nächster Schritt:** Erst GitHub-GUI-Gate und fachliche GUI-Tests auswerten; Fehler ursächlich korrigieren, danach nur nach grünen Pflicht-Gates Merge erwägen.
