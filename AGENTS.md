# AGENTS.md – MULTIMODULTOOL2026

## 1. Zweck, Geltung und Priorität

Diese Datei ist der verbindliche Arbeitsvertrag für alle automatisierten und menschlichen Entwicklungsarbeiten in diesem Repository.

Prioritätsreihenfolge:

1. Datenintegrität und Rückbaubarkeit
2. Reproduzierbarkeit und nachvollziehbare Evidenz
3. funktionale Korrektheit
4. Plattformvertrag
5. Entwicklungs- und Prüfgeschwindigkeit
6. Komfort und kosmetische Verbesserungen

Eine Änderung gilt nicht als Fortschritt, wenn sie nur Aktivität erzeugt, aber keine Hypothese bestätigt, keinen Fehler eingrenzt und keinen überprüfbaren Teilzustand fertigstellt.

## 2. Plattformvertrag

- ausschließlich Linux-Desktop
- primär Kubuntu 22.04/24.04, KDE Plasma, X11/Wayland, x86-64
- keine Windows-, macOS-, Android-, iOS-, Browser- oder PWA-Sonderlogik
- Nicht-Linux-Systeme werden vor Datenänderungen blockiert
- Containerprüfungen belegen Paket- und Abhängigkeitsverhalten, ersetzen aber keine gebootete KDE-Sitzung

## 3. Nicht verhandelbare Sicherheitsverträge

- XDG-App-Verzeichnisse verwenden `0700`, private Dateien `0600`.
- Einstellungen werden vorvalidiert, mit `fsync` bestätigt und atomar ersetzt.
- Jeder globale Fehler nennt Ursache, Folge, Datenstand, Lösung, Diagnosekennung und sicheren nächsten Schritt.
- Normale GUI-Starts verwenden genau eine Linux-Primärinstanz mit Peer-UID-Prüfung.
- Diagnose und Transaktionsübersicht bleiben rein lesend.
- Dauerhaftes Löschen, Copy-delete-Fallback und stilles Überschreiben sind verboten.
- Zugangsdaten, private Schlüssel, persönliche Dateiinhalte und absolute Projektpfade dürfen nicht in Repository, Journal oder Diagnosebericht gelangen.

## 4. Größe einer Entwicklungseinheit

Jede Arbeitseinheit besitzt genau:

- ein primäres Ziel,
- eine überprüfbare Hypothese oder Anforderung,
- einen kleinen reversiblen Patch,
- einen definierten Checkpoint,
- einen klaren Abbruchgrund.

Standardgrenze:

- höchstens drei produktive Dateien pro Minimal-Patch,
- zugehörige Tests und Dokumentation dürfen zusätzlich angepasst werden,
- größere Querschnittsänderungen benötigen vorab eine begründete Dateiliste,
- Diagnose-, Fehlerbehebungs- und Refactoringänderungen werden nicht vermischt,
- reine Formatierungsänderungen sind in funktionalen Patches verboten.

## 5. Verbindlicher Entwicklungsablauf mit Checkpoints

### Schritt 1 – Ausgangsstand sichern

- Repository, Branch, PR, Head-SHA und Zielplattform bestimmen.
- Aktuelle Dateiliste und relevante Workflows laden.
- Bereits laufende Prüfungen erfassen, bevor ein weiterer Commit erzeugt wird.

**Checkpoint C1:** Der Ausgangsstand ist eindeutig reproduzierbar.

### Schritt 2 – Risiko und kleinsten Abschluss bestimmen

- Änderung als R0 bis R3 klassifizieren.
- Betroffene Sicherheits-, Daten-, Prozess-, Release- und UI-Verträge benennen.
- Nur den kleinsten fachlich vollständigen Teil planen.

**Checkpoint C2:** Ziel, Risiko, Patchgrenze und notwendige Prüfstufe stehen fest.

### Schritt 3 – Evidenz vor Korrektur

Bei unbekannter Fehlerursache:

- vollständige relevante Protokolle einmal auswerten,
- gemeinsame und plattformspezifische Ursachen trennen,
- Hypothesen nach Evidenz priorisieren,
- Diagnoseinstrumentierung getrennt von der Korrektur committen,
- Produktivlogik im Diagnosecommit unverändert lassen.

**Checkpoint C3:** Der Fehler ist reproduzierbar und die letzte erfolgreiche Phase sichtbar.

### Schritt 4 – Minimal korrigieren

- nur die bestätigte Ursache ändern,
- keine Nebenoptimierungen,
- keine Versionssprünge oder Abhängigkeitswechsel ohne zwingenden Grund,
- bestehende Rückfall- und Sicherheitsverträge unverändert erhalten.

**Checkpoint C4:** Der Diff enthält nur ursächlich notwendige Änderungen.

### Schritt 5 – Billige Prüfungen zuerst

- Syntax,
- statische Verträge,
- unmittelbar betroffene Tests,
- keine vollständige Release- oder Stressmatrix vor erfolgreichen Schnellprüfungen.

**Checkpoint C5:** Alle schnellen Gates sind grün.

### Schritt 6 – Repräsentativen Integrationspfad prüfen

- zuerst genau einen aussagekräftigen Lebenszyklus oder Integrationspfad ausführen,
- bei Fehlern nur den neuen Befund analysieren,
- nicht automatisch die gesamte Matrix wiederholen.

**Checkpoint C6:** Der Patch funktioniert praktisch oder die Hypothese wurde enger begrenzt.

### Schritt 7 – Plattformmatrix erweitern

- zweite Kubuntu-Version erst nach grünem repräsentativen Pfad,
- X11/Wayland- oder VM-Prüfungen nur ausführen, wenn der betroffene Vertrag sie verlangt,
- identische erfolgreiche Vorstufen nicht unnötig wiederholen.

**Checkpoint C7:** Alle für den Merge verpflichtenden Plattformvarianten sind grün.

### Schritt 8 – Vollständige Abnahme

- vollständigen Repository-Vertrag,
- relevante Stress- und Wiederanlauftests,
- Dokumentations- und Fortschrittskonsistenz,
- PR-Dateiliste und bekannte Grenzen prüfen.

**Checkpoint C8:** Der PR ist mergefähig.

### Schritt 9 – Merge und Hauptzweignachweis

- erst nach erfüllten Merge-Gates squash-mergen,
- danach genau einen vollständigen Nachweis auf `main` ausführen,
- identischen Fehler nicht durch wiederholtes Neu­starten kaschieren.

**Checkpoint C9:** Der Hauptzweig besitzt denselben grünen Nachweis.

## 6. Risikoklassen

### R0 – Dokumentation oder Metadaten

Beispiele:

- Markdown ohne Vertragsänderung,
- Kommentare,
- reine Statusbeschreibung.

Erforderlich:

- Plausibilitätsprüfung,
- Link-, Pfad- und Konsistenzprüfung,
- keine Runtime-, Release- oder VM-Prüfung.

### R1 – Lokal begrenzte Implementierung

Beispiele:

- einzelne Python-Funktion,
- reine GUI-Darstellung ohne Schreibzugriff,
- lokaler Validator.

Erforderlich:

- L0 und L1,
- vollständige Suite erst vor Merge oder bei Querschnittswirkung.

### R2 – Daten-, Prozess- oder Integrationslogik

Beispiele:

- Einstellungen,
- Journal,
- Papierkorb,
- Undo/Redo,
- Wiederanlauf,
- Shell-Starter,
- Paketmanager.

Erforderlich:

- L0, L1 und L2,
- L4 vor Merge,
- betroffene Failpoint- oder Abbruchtests.

### R3 – Release-, Sicherheits- oder Plattformvertrag

Beispiele:

- Debian-Paket,
- Install/Upgrade/Rollback/Uninstall,
- Workflowmatrix,
- Signatur- oder Manifestprüfung,
- SIGKILL-, Mount-, ACL- oder echte Desktop-Sitzung.

Erforderlich:

- L0 bis L4,
- L5 vor Release oder wenn der jeweilige Vertrag geändert wurde.

## 7. Prüfstufen und Ausführungsfrequenz

### L0 – Sofortige Schnellprüfung

Nach jedem funktionalen Patch:

- Python-Syntax beziehungsweise Importprüfung,
- `bash -n` für geänderte Shellskripte,
- Repository-Validator für geänderte Verträge,
- offensichtliche Pfad-, Berechtigungs- und Manifestprüfung.

Ziel: Sekunden bis wenige Minuten.

### L1 – Betroffene Tests

Nach jeder Funktionsänderung:

- nur die direkt betroffenen Testmodule,
- neue Regression zuerst rot beweisen, danach grün,
- keine Wiederholung unveränderter, bereits grüner Module.

Ziel: wenige Minuten.

### L2 – Repräsentativer Integrationslauf

Nach einer Änderung an Integrations-, Release- oder Prozesslogik:

- genau ein vollständiger aussagekräftiger Pfad,
- vollständiges Protokoll,
- letzte Phase und Exit-Code,
- Artefakte auch bei Fehler.

Ziel: Ursache praktisch bestätigen, bevor eine Matrix gestartet wird.

### L3 – Verpflichtende Matrix

Nur:

- vor Merge,
- nach Änderung der Plattform-, Paket- oder Desktoplogik,
- wenn L2 grün ist.

Für P0-009 mindestens:

- Kubuntu 22.04 Container-Lebenszyklus,
- Kubuntu 24.04 Container-Lebenszyklus.

### L4 – Vollständiger Repository-Vertrag

Ausführen:

- vor Merge,
- nach Abhängigkeits-, Build-, Manifest-, Sicherheits- oder Workflowänderungen,
- spätestens nach fünf kleinen funktionalen Commits seit dem letzten vollständigen grünen Lauf,
- nicht nach reinen Dokumentationsänderungen.

### L5 – Teure oder physische Abnahme

Ausführen:

- vor einem Releasekandidaten beziehungsweise Stable-Release,
- nach Änderungen am jeweils betroffenen Vertrag,
- nicht nach jeder kleinen Implementierungsänderung.

Dazu gehören:

- echte `SIGKILL`-Matrix,
- längere Parallel- und Lasttests,
- gebootete Kubuntu-VMs,
- KDE Plasma unter X11 und Wayland,
- DPI-, ACL-, Mount-, Stromausfall- und Hardwarecachefälle.

Nicht physisch geprüfte Fälle werden ausdrücklich benannt.

## 8. Standardprüfungen nach Änderungsart

### Python-Modul

```bash
python3 -m src.main --validate-only
python3 tools/validate_repository.py
python3 -m unittest <direkt_betroffenes_testmodul> -v
```

### Shellskript

```bash
bash -n <geändertes_skript>
python3 tools/validate_repository.py
```

Danach nur den betroffenen Lebenszyklus oder Starterpfad ausführen.

### GUI

```bash
QT_QPA_PLATFORM=offscreen python3 -m unittest <betroffenes_gui_testmodul> -v
```

Physische KDE-Abnahme erst in L5 oder bei Änderung des Desktopvertrags.

### Vollständige Suite

```bash
python3 -m src.main --validate-only
python3 tools/validate_repository.py
python3 -m unittest discover -s tests -p "test_*.py" -v
```

Spezialisierte Stress-, Failpoint- und SIGKILL-Tests werden nur zusätzlich gestartet, wenn ihre Komponenten betroffen sind oder L5 fällig ist.

## 9. Endlosschleifen-, Retry- und Timeoutvertrag

### Schleifen

- Jede Schleife besitzt einen Versuchszähler und eine monotone Deadline.
- `while true` ist nur zulässig, wenn Abbruchsignal, Deadline und Heartbeat vorhanden sind.
- Pollingintervalle liegen normalerweise zwischen 15 und 30 Sekunden.
- Ein Pollingprozess darf das Zeitbudget des übergeordneten Schritts nicht überschreiten.
- Lange Operationen melden mindestens alle 60 Sekunden Phase, Laufzeit und letzten Fortschritt.

### Wiederholungen

- Kein identischer Wiederholungslauf ohne neue Evidenz, Konfigurationsänderung oder Codeänderung.
- Maximal zwei identische Wiederholungsversuche.
- Externe Downloads: höchstens ein Erstversuch plus zwei Retries mit begrenztem Backoff.
- Nach drei erfolglosen Patchzyklen ist eine Strategieprüfung verpflichtend.
- Ein erfolgreicher Vorjob wird nicht erneut gestartet, wenn GitHub den fehlgeschlagenen Job separat wiederholen kann und sich der Commit nicht geändert hat.

### Timeouts

Jeder CI-Job und jeder potenziell blockierende Unterprozess erhält ein festes Zeitbudget.

Richtwerte:

- Syntax und Validatoren: 2 bis 5 Minuten,
- Unit-Tests: 10 bis 15 Minuten,
- Integrationspfad: 30 bis 45 Minuten,
- Kubuntu-Lebenszyklus: höchstens 80 Minuten,
- VM- und physische Desktop-Abnahme: eigenes begründetes Budget.

Ein Prozess gilt als verdächtig blockiert, wenn er länger als fünf Minuten weder Ausgabe noch messbaren Zustandsfortschritt liefert. Dann werden Diagnose, Prozessbaum, letzte Phase und Ressourcenstatus gesichert, bevor kontrolliert abgebrochen wird.

### Konstruktiver Abbruch

Nach Timeout oder Abbruch müssen verfügbar sein:

- Lauf- oder Job-ID,
- letzte Phase,
- ursprünglicher Exit-Code oder Signal,
- relevante Protokollauszüge,
- vollständiges Rohprotokoll als Artefakt,
- aktueller Hypothesenstand,
- genau ein nächstes gezieltes Experiment.

## 10. CI-, Parallelitäts- und Artefaktvertrag

- Diagnose- und Fehlerläufe laden Protokolle und Statusartefakte mit `if: always()` hoch.
- Uploadfehler dürfen den ursprünglichen Exit-Code nicht verdecken.
- Branchbezogene Concurrency darf veraltete Läufe abbrechen, aber keinen bewusst gestarteten Evidenzlauf vernichten.
- Vor einem Commit wird geprüft, ob bereits ein gleichwertiger Lauf aktiv ist.
- Dokumentationsänderungen werden nicht zwischen Diagnosecommit und Diagnoseauswertung geschoben, sofern dadurch unnötige Release-Läufe entstehen.
- Reine Dokumentationscommits dürfen mit dokumentiertem CI-Skip erfolgen, wenn der nächste funktionale Commit sämtliche erforderlichen Gates wieder ausführt.
- Releaseartefakte werden pro Head-SHA einmal gebaut und von nachgelagerten Jobs wiederverwendet.
- Jobname, Matrixwert, tatsächlich verwendetes Image und tatsächliche Betriebssystemversion müssen im Protokoll eindeutig sichtbar sein.

## 11. Projekttransaktionen

- Dateiaktionen verwenden den projektbezogenen Papierkorb und ausschließlich `os.replace` im selben Dateisystem.
- Jede reversible Aktion besitzt Aktions- und Transaktions-ID.
- `history/actions.jsonl` ist append-only, `0600` und SHA-256-hashverkettet.
- Undo läuft rückwärts, Redo vorwärts; Konflikte und beschädigte Zustände blockieren.
- Dauerhaftes Löschen, Copy-delete-Fallback und stilles Überschreiben sind verboten.

## 12. Abbruch- und Wiederanlaufvertrag

- Jeder lange Lauf besitzt eine eindeutige `MMTRUN-`-ID.
- Der Plan ist unveränderlich und SHA-256-geprüft.
- Checkpoints werden atomar ersetzt und nachvalidiert.
- Laufordner verwenden `0700`; Plan, Checkpoint, Sperre und Abbruchanforderung `0600`.
- Ein `flock` erlaubt genau einen schreibenden Laufprozess.
- Externe Abbruchanforderungen verändern ausschließlich `cancel.request`; nur der aktive Prozess schreibt Checkpoints.
- Abbruch wird nur vor einem neuen Intent oder nach einem vollständig bestätigten Schritt akzeptiert.
- Wiederanlauf gleicht Checkpoint, Journal, Manifest, Originalpfad und Payload gemeinsam ab.
- Bereits ausgeführte Dateioperationen dürfen nicht wiederholt werden.
- Widersprüchliche Zustände bleiben unverändert und werden über `SafeOperationError` erklärt.
- Verbindliche Details: `docs/ABBRUCH_UND_WIEDERANLAUFVERTRAG.md`.

## 13. Prozessabbruchmatrix

Die CI muss echte Linux-`SIGKILL`-Abbrüche vor und nach Intent, Dateioperation, `fsync`, Manifestabschluss und Journalabschluss prüfen. Nach jedem Neustart ist genau eine vollständige Aktion zulässig; temporäre Dateien, doppelte Payloads und verlorene Journalabschlüsse sind Fehler.

Diese teure Matrix wird nur ausgeführt:

- nach Änderungen an Wiederanlauf, Journal, Manifest oder Transaktionslogik,
- vor Release,
- bei einem neu aufgetretenen Abbruch- oder Konsistenzfehler.

## 14. UI-Basis

Die visuelle Referenz unter `assets/ui-reference/` bleibt bindende Orientierung. Die neun Zonen bleiben erhalten. Sicherheitszustände sind immer textuell sichtbar. Produktive Projekt- und Dateiauswahl bleibt bis zum geführten Workflow gesperrt.

## 15. Linux-Releasevertrag P0-009

- Releaseziel ist ein reproduzierbares `amd64`-Debian-Paket für Kubuntu 22.04/24.04.
- Runtime-Dateien stammen ausschließlich aus `release/package-files.txt`.
- Build-ID, Source-Manifest, installiertes SHA-256-Manifest und Wheelhouse-Manifest sind verpflichtend.
- Der Erststart installiert PySide6 ausschließlich aus dem gebündelten lokalen Wheelhouse.
- Installation, Upgrade, Rollback und Entfernung laufen nur nach Vorprüfung und ausdrücklichem `--yes`.
- Normale Entfernung bewahrt Nutzerdaten; der Nutzerdaten-Purge benötigt eine eindeutig bestimmte Nicht-root-Identität.
- Signaturen und Vertrauenskette bleiben bis `P3-009` ausdrücklich offen.

Zusätzlicher Ausführungsvertrag für Releasefehler:

1. beide fehlgeschlagenen Jobprotokolle vollständig auswerten,
2. gemeinsame Ursache von Matrix- oder Versionsfehlern trennen,
3. separaten Diagnosecommit ohne Produktivkorrektur erstellen,
4. Diagnoseergebnis vollständig sichern,
5. gemeinsame Ursache minimal korrigieren,
6. L0 und L1 ausführen,
7. einen repräsentativen Lebenszyklus ausführen,
8. erst danach beide Kubuntu-Lebenszyklen vollständig ausführen,
9. erst bei zwei grünen Lebenszyklen und grünem L4 squash-mergen.

## 16. Fortschritts- und GitHub-Vertrag

- Fortschrittsquelle ist ausschließlich die Checkbox-Zahl in `TODO.md`.
- README, TODO und `src/main.py` müssen exakt übereinstimmen.
- Erledigt gilt erst nach Umsetzung, Abnahme, Dokumentation, grünem erforderlichem CI-Lauf und GitHub-Commit.
- Jede abgeschlossene Iteration wird auf `provoware/MULTIMODULTOOL2026` übertragen.
- Tokens, Passwörter und private Schlüssel dürfen niemals im Repository liegen.
- Branch und PR werden vor jeder Schreiboperation erneut geprüft.
- Ein Merge erfolgt nur mit exakt benanntem geprüften Head-SHA.

## 17. Pflichtbericht jeder Iteration

Jeder Abschluss nennt kompakt:

- Ziel und Risikoklasse,
- geänderte Dateien,
- tatsächlich ausgeführte Prüfungen und deren Begründung,
- bewusst nicht ausgeführte Prüfungen und deren Begründung,
- Checkpointstatus,
- CI-Run und geprüften SHA,
- bekannte Grenzen,
- Fortschritt in Prozent sowie erledigte und offene Punkte,
- direkt folgenden technischen Entwicklungsschritt,
- alternative Verbesserung mit hohem Nutzen und geringem Risiko.