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

- Destruktive Dateiaktionen dürfen reguläre Dateien und Verzeichnisse standardmäßig nur in den projektbezogenen Papierkorb verschieben.
- Vor jeder Aktion sind Projektgrenze, Mountstatus, Symlink-Komponenten, Hardlinks, Namenskonflikte, freier Speicher und Wiederherstellbarkeit zu prüfen.
- Die Vorschau ist rein lesend und enthält eindeutige Transaktions-ID, Zielpfade, Methode und Quellfingerabdruck.
- Ausführung und Wiederherstellung verwenden ausschließlich `os.replace` innerhalb desselben Dateisystems.
- Kopieren mit anschließendem Löschen ist verboten.
- Transaktionsordner verwenden `0700`; `manifest.json` verwendet `0600` und Schema 1.
- Beschädigte Manifeste, veränderte Payloads und Konflikte bleiben unverändert und werden über `SafeOperationError` erklärt.
- Eine Funktion zum dauerhaften Löschen oder Leeren des Papierkorbs ist nicht freigegeben.
- Verbindliche Details: `docs/PAPIERKORBVERTRAG.md`.

## Parallelstartvertrag

- Der Stresstest startet 20 nahezu gleichzeitige Zweitinstanzen.
- Genau eine Primärinstanz muss bestehen bleiben.
- Jede gültige Aktivierungskennung darf höchstens einmal ankommen.
- Nach dem Schließen dürfen keine Socket- oder Metadatenreste verbleiben.

## UI-Basis

Die visuelle Referenz unter `assets/ui-reference/` bleibt bindende Orientierung. Die neun Zonen bleiben erhalten. Der Papierkorbvertrag darf als separates read-only Panel vorbereitet werden; produktive Dateiauswahl bleibt bis zum geführten Projektworkflow gesperrt.

## Ablauf jeder Iteration

### Vorprüfung

- Ausgangscommit, Zielbranch, Konto und mindestens `push` prüfen.
- Datenverlust-, Datenschutz-, Linux-, Mount-, Symlink-, UI- und Rückfallrisiken bewerten.
- TODO, Schwachstellen und Upgrade-Pool entdoppeln.
- kleinsten vollständigen reversiblen Patch planen.

### Umsetzung

- keine stillen Löschungen oder Überschreibungen
- keine neue Abhängigkeit ohne dokumentierten Grund
- produktive Dateiaktionen nur nach Vorschau, Validierung und Rückfallweg
- kleine testbare Linux-Module
- keine Zugangsdaten oder privaten Dateiinhalte protokollieren
- Fehler ausschließlich über die zentrale Ereignisschicht erklären

### Nachvalidierung

```bash
python3 -m src.main --validate-only
python3 tools/validate_repository.py
python3 -m unittest discover -s tests -p "test_*.py" -v
python3 -m unittest tests.test_project_trash -v
python3 -m unittest tests.test_single_instance_stress -v
python3 -m unittest tests.test_settings_failpoints -v
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_gui_offscreen -v
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_gui_trash_contract -v
```

Nicht physisch geprüfte KDE-, X11-, Wayland-, DPI-, ACL- oder Mountfälle werden offen benannt.

## Pflichtpflege

Betroffene Dateien werden im selben Commit aktualisiert: `README.md`, `TODO.md`, `CHANGELOG.md`, `ANLEITUNG_TOOL.md`, `SCHWACHSTELLEN.md`, `UPGRADE_POOL.md`, `ENTWICKLERDOKU.md` sowie die Verträge unter `docs/`.

## Fortschritts- und GitHub-Vertrag

- Fortschrittsquelle ist ausschließlich die Checkbox-Zahl in `TODO.md`.
- README und TODO müssen exakt übereinstimmen.
- Erledigt gilt erst nach Umsetzung, Abnahme, Dokumentation, grünem CI-Lauf und GitHub-Commit.
- Jede abgeschlossene Iteration wird auf `provoware/MULTIMODULTOOL2026` übertragen.
- Tokens, Passwörter und private Schlüssel dürfen niemals im Repository liegen.
