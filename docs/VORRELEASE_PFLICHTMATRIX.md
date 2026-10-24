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

## 24.10.2026 – P3-004: isolierte, reproduzierbare Testdaten

**Ausgangs-HEAD (`main`):** `476b7688fd181221eb956ddeb9cd8546b70bf777`.
**Arbeitszweig:** `automation/p3-004-reproducible-fixtures-20261024`.
**Scope:** `tools/generate_test_data.py`, `tests/test_generate_test_data.py`,
`docs/TESTDATENVERTRAG.md`, README und diese Matrix.
**Risiko:** R1 (neue Testwerkzeuge; keine Änderung an Produktivoperationen).
**Checkpoint:** synthetische, deterministische Testfälle; P3-004 bleibt bis
zum vollständig geprüften und integrierten PR ausdrücklich offen.

| Release-Pflicht | Nachweis / Ist | Status und nächster Nachweis |
|---|---|---|
| Fachfunktionen / Grenzfälle | 10 feste Dateien: leere Datei, Unicode, Dubletten, Kollision, tiefe Pfade, gemischte Endungen | P3-004 implementiert; produktive P1-002-Navigation weiterhin offen |
| Datensicherheit / Wiederherstellung | Bestehende Ziele und defekte Symlinks werden verweigert; kein Löschen oder Überschreiben | Regressionen in `tests/test_generate_test_data.py`; echte Recovery separat |
| Fehlerbehandlung / Sicherheit | Absoluter neuer Zielpfad, Symlink-Eltern und Quellbaum blockiert; private Rechte | GitHub-Tests und gezielte Negativtests erforderlich |
| Design / Lesbarkeit / 800×600 / hohe Skalierung | CLI ohne GUI; kein Einfluss auf UI | P2-002/P2-007 und 800×600-Offscreen-Matrix offen |
| Tastatur / Barrierefreiheit | Kein neues GUI-Element | P2-001/P2-003/P2-005/P2-006 offen |
| Performance / Wartbarkeit | Feste, kleine Bytes, keine Zufallsquelle und keine externen Abhängigkeiten | P3-005/P3-006 und Langzeitlast offen |
| Paketierung / Installation | Keine Runtime-Paketänderung | Bestehende Release-Gates vor Merge prüfen |
| Automatisierte Funktion / Regression | 8 neue `unittest`-Fälle, Manifest-Hashes, identische Bytes, Verweigerung bestehender Ziele | GitHub Repository Contract auf letztem HEAD prüfen |
| Integration / GUI / Browser | Reiner Linux-Desktop; Browser ist kein Projektziel | Qt-Offscreen-Gate separat, reale KDE-Abnahme erst vor Release |
| CI | Nach Implementierungsfix: `40079653584` auf `767ed496` erfolgreich | Neuer endgültiger Branch-HEAD muss ebenfalls grün sein |
| Dokumentation | README, Generatorvertrag und Matrix | P3-004 nach grüner PR-Integration in TODO/GUI-Zähler synchronisieren |
| Release-Vorbereitung | Keine Veröffentlichung, keine Migration, kein Merge | Gesamtes Projekt bleibt BLOCKED; persönliche Endabnahme erst am Schluss |

**Negativtest-Befund:** Zwischencommit `48509cf0` scheiterte in der
Unit-Suite; die Ursache war die unzureichende Privatberechtigung rekursiv
angelegter Zwischenordner. Commit `767ed496` legt jede Ebene mit
`0700` an. Der vollständige Repository-Vertrag wurde danach auf
`767ed496` mit Run `40079653584` grün geprüft. Frühere grüne Läufe
werden **nicht** als Nachweis für spätere Commits ausgegeben.

**Nächste Pflicht:** finalen GitHub-HEAD einschließlich Dokumentation
prüfen, Entwurfs-PR ohne Merge eröffnen; danach P1-002-Integration
und P2-Tastatur-/Skalierungsmatrix getrennt bearbeiten.
