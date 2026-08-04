# AGENTS.md – MULTIMODULTOOL2026

## Projektauftrag

Dieses Repository wird als laienoptimiertes, transparentes und datensicheres Linux-Desktop-Werkzeug entwickelt. Änderungen müssen verständlich, prüfbar, rückbaubar und mit GitHub synchronisiert sein.

## Plattformvertrag

- ausschließlich Linux-Desktop
- primär Kubuntu 22.04/24.04, KDE Plasma, X11/Wayland, x86-64
- keine Windows-, macOS-, Android-, iOS-, Browser- oder PWA-Sonderlogik
- Nicht-Linux-Systeme werden vor Datenänderungen blockiert

## Grundlegende Sicherheitsverträge

- XDG-App-Verzeichnisse verwenden `0700`, private Dateien `0600`.
- Einstellungen werden vorvalidiert, temporär geschrieben, mit `fsync` bestätigt und atomar ersetzt.
- Jeder globale Fehler nennt Ursache, Folge, Datenstand, Lösung, Diagnosekennung und sicheren nächsten Schritt.
- Normale GUI-Starts verwenden genau eine Linux-Primärinstanz mit Unix-Socket und Peer-UID-Prüfung.
- Diagnose bleibt rein lesend; Löschen, Upload, Reparatur und Auto-Export sind verboten.

## Projektpapierkorbvertrag

- Destruktive Dateiaktionen dürfen reguläre Dateien und Verzeichnisse nur in den projektbezogenen Papierkorb verschieben.
- Vor jeder Aktion sind Projektgrenze, Mountstatus, Symlinks, Hardlinks, Namenskonflikte, freier Speicher und Wiederherstellbarkeit zu prüfen.
- Ausführung und Restore verwenden ausschließlich `os.replace` innerhalb desselben Dateisystems.
- Kopieren mit anschließendem Löschen und dauerhaftes Leeren sind verboten.
- Transaktionsordner verwenden `0700`; `manifest.json` verwendet `0600` und Schema 1.
- Beschädigte Manifeste, veränderte Payloads und Konflikte bleiben unverändert.

## Undo-/Redo-Vertrag

- Jede Dateioperation erhält eindeutige Aktions-, Transaktions- und Ereignis-IDs.
- Das Projektjournal liegt unter `.multimodultool2026/history/actions.jsonl`.
- Journalordner verwendet `0700`, Journaldatei `0600`.
- Das Journal ist append-only; bestehende Zeilen werden nie geändert oder entfernt.
- Ereignisse sind lückenlos sequenziert und über SHA-256 verkettet.
- Vor einer Dateioperation wird ein Intent, danach ein Abschlussereignis angehängt.
- Undo ist nur für die letzte aktive Aktion zulässig und läuft rückwärts.
- Redo ist nur für die nächste zurückgenommene Aktion zulässig und läuft vorwärts.
- Wiederholtes Undo oder Redo darf keine Doppeloperation erzeugen.
- Neue Aktionen bleiben blockiert, solange eine Redo-Kette vorhanden ist.
- Unterbrochene Intents werden nur bei eindeutigem Manifest- und Dateizustand abgeschlossen.
- Hashfehler, widersprüchliche Zustände und Reihenfolgekonflikte blockieren unverändert.

## Read-only Transaktionsübersicht

- Sichtbare Zustände: `prepared`, `trashed`, `restored`, `damaged`.
- Filterung verändert keine Transaktionsdatei.
- Beschädigte Zustände werden nur markiert.
- Restore, Reparatur, Löschen, Upload und Auto-Export sind nicht zulässig.

## Parallelstartvertrag

- Der Stresstest startet 20 nahezu gleichzeitige Zweitinstanzen.
- Genau eine Primärinstanz bleibt bestehen.
- Jede gültige Aktivierungskennung kommt höchstens einmal an.
- Nach dem Schließen bleiben keine Socket- oder Metadatenreste.

## UI-Basis

Die visuelle Referenz unter `assets/ui-reference/` bleibt bindende Orientierung. Die neun Zonen bleiben erhalten. Produktive Projekt- und Dateiauswahl bleibt bis zum geführten Projektworkflow gesperrt.

## Ablauf jeder Iteration

### Vorprüfung

- Ausgangscommit, Zielbranch, Konto und mindestens `push` prüfen.
- Datenverlust-, Datenschutz-, Linux-, Mount-, Symlink-, Journal-, UI- und Rückfallrisiken bewerten.
- TODO, Schwachstellen und Upgrade-Pool entdoppeln.
- kleinsten vollständigen reversiblen Patch planen.

### Umsetzung

- keine stillen Löschungen oder Überschreibungen
- keine neue Abhängigkeit ohne dokumentierten Grund
- produktive Dateiaktionen nur nach Vorschau, Validierung und Rückfallweg
- kleine testbare Linux-Module
- keine Zugangsdaten, privaten Dateiinhalte oder absoluten Projektpfade im Aktionsjournal
- Fehler ausschließlich über die zentrale Ereignisschicht erklären

### Nachvalidierung

```bash
python3 -m src.main --validate-only
python3 tools/validate_repository.py
python3 -m unittest discover -s tests -p "test_*.py" -v
python3 -m unittest tests.test_project_trash -v
python3 -m unittest tests.test_undo_redo -v
python3 -m unittest tests.test_transaction_overview -v
python3 -m unittest tests.test_single_instance_stress -v
python3 -m unittest tests.test_settings_failpoints -v
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_gui_offscreen -v
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_gui_trash_contract -v
```

Nicht physisch geprüfte KDE-, X11-, Wayland-, DPI-, ACL-, Mount- oder Prozessabbruchfälle werden offen benannt.

## Pflichtpflege

Betroffene Dateien werden im selben Commit aktualisiert: `README.md`, `TODO.md`, `CHANGELOG.md`, `ANLEITUNG_TOOL.md`, `SCHWACHSTELLEN.md`, `UPGRADE_POOL.md`, `ENTWICKLERDOKU.md` sowie die Verträge unter `docs/`.

## Fortschritts- und GitHub-Vertrag

- Fortschrittsquelle ist ausschließlich die Checkbox-Zahl in `TODO.md`.
- README, TODO und `src/main.py` müssen exakt übereinstimmen.
- Erledigt gilt erst nach Umsetzung, Abnahme, Dokumentation, grünem CI-Lauf und GitHub-Commit.
- Jede abgeschlossene Iteration wird auf `provoware/MULTIMODULTOOL2026` übertragen.
- Tokens, Passwörter und private Schlüssel dürfen niemals im Repository liegen.
