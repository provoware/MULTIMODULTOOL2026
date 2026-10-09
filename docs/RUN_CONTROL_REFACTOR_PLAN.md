# Refactoring-Vorbereitung: Abbruch- und Wiederanlaufsteuerung

**Stand:** 09.10.2026 · **Status:** testgestützte Vorbereitung, **keine** Produktionsaufteilung

## Bestandsaufnahme

`src/run_control.py` umfasst rund **1.067 Zeilen**. Mehrere Verantwortungen liegen zusammen:

| Bereich (Ausgangsstand, ungefähr) | Aufgabe | Risikoklasse |
|---|---|---|
| Zeilen 64–236 | Datenklassen, Laufkennung, Pfadprüfung | R1/R2 |
| Zeilen 237–354 | private Dateien, JSON, Hash, atomarer Ersatz | R2 |
| Zeilen 355–503 | Plan- und Checkpointvalidierung | R2 |
| Zeilen 509–654 | Sperre, Checkpoint und Plananlage | R2 |
| Zeilen 655–748 | Abbruchanforderung und Schrittfortschritt | R2 |
| Zeilen 749–968 | Transaktion, Papierkorb, Journal, Recovery | R2/R3 |
| Zeilen 969–1067 | Wiederaufnahme und Ausführungsschleife | R2 |

**Maßgebend** bleiben `docs/ABBRUCH_UND_WIEDERANLAUFVERTRAG.md`, `AGENTS.md` und die bestehenden SIGKILL-Tests. Die Zeilennummern dienen nur zur Orientierung.

## Neue Ausgangstests

`tests/test_run_control_refactor_contract.py` prüft an **temporären** Projekten:

1. Ein zusätzlicher Hardlink zur Plandatei führt zur kontrollierten Ablehnung.
2. Ein Checkpoint über dem Größenlimit wird vor der Dateioperation zurückgewiesen.
3. Eine beschädigte Abbruchanforderung blockiert, ohne die Nutzdatei zu verschieben.
4. Eine ungültige Laufkennung kann den Projektbereich nicht verlassen.

Die bereits vorhandenen `tests.test_run_control` und `tests.test_run_control_sigkill` sichern unter anderem Idempotenz, Sperre, Abbruch und zehn harte Prozessabbrüche. Der Repository-Workflow führt den neuen Test über `unittest discover` mit aus.

## Empfohlene Reihenfolge der späteren Aufteilung

1. **Nur Datenklassen und reine Validierung auslagern:** etwa nach `src/run_control_state.py`. Dabei öffentlich erreichbare Namen und JSON-Feldnamen beibehalten. Vorher/nachher identische Serialisierung nachweisen.
2. **Dateischutz und persistente Checkpoints abgrenzen:** eigene kleine Datei für private Zugriffe und atomare Schreibvorgänge; weiterhin Rechte 0600/0700, Verzeichnis-`fsync`, Dateigrößenlimits und Schutz vor Symlinks/Hardlinks.
3. **Recovery und Ausführung erst zuletzt entkoppeln:** `_reconcile_current_step`, `_perform_current_step` und `resume_run` sind besonders riskant und bleiben unangetastet, bis die vorherigen Stufen die gesamte Regression bestehen.

`src/run_control.py` soll als **kompatibler Einstieg** bestehen bleiben; die extern verwendeten Namen müssen zunächst weiter importierbar sein. Keine parallele Umbenennung von Datentypen, kein Schemawechsel, kein Formatwechsel, kein Wechsel des Journals.

## Verbindliche Abnahmebedingungen vor einem echten Umbau

- Syntax, die betroffenen Tests und der gesamte bisherige `unittest discover`-Vertrag erfolgreich.
- **SIGKILL-Matrix an allen zehn Stellen** erfolgreich, ohne zweite Dateioperation, ohne verlorenen Journalabschluss und ohne offene temporäre Dateien.
- Ein einziger kontrollierter Executor, unveränderter Planhash, konsistente Checkpoints und private Rechte nachgewiesen.
- Eine Simulation des Wiederanlaufs nach Teilfortschritt und beschädigter Abbruchdatei erfolgreich.
- Für die eigentliche R2/R3-Änderung zusätzlich die nach `AGENTS.md` vorgesehenen Integrations-/Kubuntu-/Release-Gates erfüllen.
- Solange eines dieser Kriterien nicht belegt ist: **nicht zusammenführen; bestehende Produktionsdatei beibehalten.**

## Abgrenzung

Diese Iteration ergänzt ausschließlich Tests und diesen Aufteilungsplan. Keine Änderungen an `src/run_control.py`, Journaldaten, Benutzerdaten, Sicherheitsregeln oder Installationspaketen. Die Verwendung echter Kubuntu-Desktop-Sitzungen ist durch Repository-CI allein **nicht** belegt.
