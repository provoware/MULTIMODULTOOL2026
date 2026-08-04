# Undo-/Redo- und Transaktionsvertrag – MULTIMODULTOOL2026

## Ziel

Jede freigegebene Papierkorb- und spätere Dateioperation erhält eine eindeutige Aktions-ID und mindestens eine eindeutige Transaktions-ID. Undo und Redo sind wiederholbar, konfliktgeprüft, absturzsicher und in eindeutiger Reihenfolge ausführbar. Lange Abläufe verwenden zusätzlich eine Lauf-ID und atomare Checkpoints.

## Speicherorte

```text
<Projekt>/.multimodultool2026/
├── history/actions.jsonl
├── runs/<MMTRUN-ID>/
│   ├── plan.json
│   └── checkpoint.json
└── trash/transactions/<MMTTRASH-ID>/
    ├── manifest.json
    └── payload
```

- Projektkontrollverzeichnisse: `0700`
- private Dateien: `0600`
- Journal-Schema: Version 1
- maximale Journalgröße: 8 MiB
- maximale Ereigniszahl: 20.000
- absolute Pfade im Journal und Laufplan: verboten

## Kennungen

- Aktions-ID: `MMTACTION-YYYYMMDDTHHMMSS-<12 HEX>`
- Transaktions-ID: `MMTTRASH-YYYYMMDDTHHMMSS-<12 HEX>`
- Ereignis-ID: `MMTEVENT-<24 HEX>`
- Lauf-ID: `MMTRUN-YYYYMMDDTHHMMSS-<12 HEX>`

Eine Aktions-ID bleibt bei Undo und Redo stabil. Ein Redo erhält eine neue Transaktions-ID. Ein langer Lauf speichert die aktuelle Aktions- und Transaktions-ID vor dem Intent im Checkpoint.

## Append-only Journal

Erlaubte Ereignisse:

1. `prepare`
2. `apply`
3. `cancel`
4. `undo-intent`
5. `undo`
6. `redo-intent`
7. `redo`

Jedes Ereignis enthält Sequenznummer, Ereignis-ID, Aktions-ID, Transaktions-ID, relativen Projektpfad, Folgezustand, Recovery-Kennzeichen, vorherigen Hash und eigenen SHA-256-Hash.

Das Anhängen verwendet `O_APPEND`, `O_NOFOLLOW`, exklusives `flock`, vollständiges Schreiben und `fsync`. Vorhandene Zeilen werden niemals geändert oder entfernt.

## Reihenfolge und Idempotenz

- Undo ist ausschließlich für die zuletzt aktive Aktion zulässig.
- Mehrere Undo-Schritte laufen rückwärts.
- Redo ist ausschließlich für die nächste zurückgenommene Aktion zulässig.
- Mehrere Redo-Schritte laufen vorwärts.
- Eine neue Aktion wird blockiert, solange eine Redo-Kette vorhanden ist.
- Bereits vollständig erfasste Aktionen werden nicht erneut ausgeführt.
- Bereits zurückgenommene oder erneut angewendete Aktionen liefern einen kontrollierten No-op.

## Verbindung zum Laufcheckpoint

Der Laufcheckpoint ersetzt das Aktionsjournal nicht. Er dokumentiert ausschließlich, welcher geplante Schritt als Nächstes erwartet wird. Autoritative Nachweise bleiben:

1. hashverkettetes Journal,
2. Transaktionsmanifest,
3. Originalpfad,
4. Payload.

Fehlt nach Prozessende nur der Laufcheckpoint, wird ausschließlich dessen Fortschritt ergänzt. Fehlt nach einer bereits ausgeführten Dateioperation der Manifest- oder Journalabschluss, wird nur der nachweislich fehlende Abschluss ergänzt.

## Absturz- und Recovery-Vertrag

- Checkpoint ohne Intent: gleicher Schritt und gleiche IDs werden fortgesetzt.
- `prepare` ohne Transaktionsordner: gleiche Transaktions-ID wird aufgebaut.
- `prepared` ohne Payload: Dateioperation setzt nach erneuter Fingerabdruckprüfung fort.
- Payload vorhanden, Original frei: `fsync`, Manifest und fehlendes `apply` werden ergänzt.
- `apply` vorhanden: nur Laufcheckpoint wird fortgeschrieben.
- widersprüchliche Zustände: unveränderte Blockade.

## Rein lesende Transaktionsübersicht

Sichtbare Zustände: `prepared`, `trashed`, `restored`, `damaged`. Beschädigte Manifeste, Symlinks und falsche Rechte werden markiert, aber niemals verändert. Restore, Reparatur, Löschen, Upload und automatischer Export fehlen.

## Abnahme

- zehn Aktionen vollständig anwenden,
- zehn Undo-Schritte rückwärts,
- zehn Redo-Schritte vorwärts,
- stabile Aktions-IDs,
- neue Redo-Transaktions-IDs,
- keine Doppeloperation,
- Hashmanipulation und Symlinkjournal blockieren,
- Prozessabbruchmatrix ergänzt ausschließlich fehlende Abschlüsse,
- Transaktionsübersicht verändert keine Manifestbytes.
