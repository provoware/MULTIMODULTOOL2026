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
- Einstellungen werden vorvalidiert, mit `fsync` bestätigt und atomar ersetzt.
- Jeder globale Fehler nennt Ursache, Folge, Datenstand, Lösung, Diagnosekennung und sicheren nächsten Schritt.
- Normale GUI-Starts verwenden genau eine Linux-Primärinstanz mit Peer-UID-Prüfung.
- Diagnose und Transaktionsübersicht bleiben rein lesend.

## Projekttransaktionen

- Dateiaktionen verwenden den projektbezogenen Papierkorb und ausschließlich `os.replace` im selben Dateisystem.
- Jede reversible Aktion besitzt Aktions- und Transaktions-ID.
- `history/actions.jsonl` ist append-only, `0600` und SHA-256-hashverkettet.
- Undo läuft rückwärts, Redo vorwärts; Konflikte und beschädigte Zustände blockieren.
- Dauerhaftes Löschen, Copy-delete-Fallback und stilles Überschreiben sind verboten.

## Abbruch- und Wiederanlaufvertrag

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

## Prozessabbruchmatrix

Die CI muss echte Linux-`SIGKILL`-Abbrüche vor und nach Intent, Dateioperation, `fsync`, Manifestabschluss und Journalabschluss prüfen. Nach jedem Neustart ist genau eine vollständige Aktion zulässig; temporäre Dateien, doppelte Payloads und verlorene Journalabschlüsse sind Fehler.

## UI-Basis

Die visuelle Referenz unter `assets/ui-reference/` bleibt bindende Orientierung. Die neun Zonen bleiben erhalten. Sicherheitszustände sind immer textuell sichtbar. Produktive Projekt- und Dateiauswahl bleibt bis zum geführten Workflow gesperrt.

## Ablauf jeder Iteration

### Vorprüfung

- Ausgangscommit, Zielbranch, Konto und mindestens `push` prüfen.
- Datenverlust-, Datenschutz-, Linux-, Mount-, Symlink-, Journal-, Prozessabbruch-, UI- und Rückfallrisiken bewerten.
- TODO, Schwachstellen und Upgrade-Pool entdoppeln.
- kleinsten vollständigen reversiblen Patch planen.

### Umsetzung

- keine stillen Löschungen oder Überschreibungen
- keine neue Abhängigkeit ohne dokumentierten Grund
- produktive Dateiaktionen nur nach Vorschau, Validierung und Rückfallweg
- kleine testbare Linux-Module
- keine Zugangsdaten, privaten Dateiinhalte oder absoluten Projektpfade in Journalen
- Fehler ausschließlich über die zentrale Ereignisschicht erklären

### Nachvalidierung

```bash
python3 -m src.main --validate-only
python3 tools/validate_repository.py
python3 -m unittest discover -s tests -p "test_*.py" -v
python3 -m unittest tests.test_project_trash -v
python3 -m unittest tests.test_undo_redo -v
python3 -m unittest tests.test_transaction_overview -v
python3 -m unittest tests.test_run_control -v
python3 -m unittest tests.test_run_control_sigkill -v
python3 -m unittest tests.test_single_instance_stress -v
python3 -m unittest tests.test_settings_failpoints -v
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_gui_offscreen -v
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_gui_trash_contract -v
```

Nicht physisch geprüfte KDE-, X11-, Wayland-, DPI-, ACL-, Mount-, Stromausfall- oder Hardwarecachefälle werden offen benannt.

## Fortschritts- und GitHub-Vertrag

- Fortschrittsquelle ist ausschließlich die Checkbox-Zahl in `TODO.md`.
- README, TODO und `src/main.py` müssen exakt übereinstimmen.
- Erledigt gilt erst nach Umsetzung, Abnahme, Dokumentation, grünem CI-Lauf und GitHub-Commit.
- Jede abgeschlossene Iteration wird auf `provoware/MULTIMODULTOOL2026` übertragen.
- Tokens, Passwörter und private Schlüssel dürfen niemals im Repository liegen.
