# Fehler- und Ereignisvertrag – MULTIMODULTOOL2026

## Pflichtfelder

Jeder globale Fehlerbericht enthält Ursache, Folge, Datenstand, Lösung, Diagnosekennung und sicheren nächsten Schritt.

## Erfasste Bereiche

- Hauptthread-, Worker- und Qt-Ausnahmen
- Manifest-, XDG- und Einstellungsfehler
- Einstellungs-Recovery
- Single-Instance-Laufzeit und Sperren
- Projektpapierkorb, Undo/Redo und Transaktionsübersicht
- Laufplan, Checkpoint, Laufsperre, Abbruchanforderung und Wiederanlauf
- spätere Dateioperationen über `SafeOperationError`

## Laufsteuerungsfehler

`src/run_control.py` verwendet `SafeOperationError(category="run-control")`. Typische Ursachen:

- veränderter Planhash,
- beschädigter oder widersprüchlicher Checkpoint,
- fremde Lauf-, Aktions- oder Transaktions-ID,
- unsichere Rechte, Symlink oder zusätzlicher Hardlink,
- konkurrierender Laufprozess,
- widersprüchlicher Original-/Payloadzustand,
- fehlender oder beschädigter Manifest-/Journalnachweis,
- unzulässiger automatischer Wiederanlauf.

Der Datenstand muss genau nennen, ob die Quelle am Originalpfad, im Payload oder bereits vollständig journalisiert liegt. Ein fehlender Abschluss darf nicht als fehlende Dateioperation fehlinterpretiert werden.

## Prozessabbruch

`SIGKILL` kann keinen Dialog mehr auslösen. Der nächste Prozess erzeugt bei einem Widerspruch den vollständigen Fehlervertrag. Eindeutige Zustände werden ohne Fehlermeldung idempotent fortgesetzt oder abgeschlossen; Recovery wird in Journal und Laufresultat markiert.

## Ereignisjournal

```text
~/.local/state/multimodultool2026/logs/events.jsonl
```

Reguläre Datei, ein Hardlink, aktueller Eigentümer, keine Symlinks, Modus `0600`, JSONL und `fsync` je Eintrag. Private Pfade und typische Geheimnismuster werden reduziert.

## Grenzen

Journalrotation folgt `P3-003`. Physische KDE-, Stromausfall-, Sonder-Mount- und ACL-Abnahmen bleiben offen.
