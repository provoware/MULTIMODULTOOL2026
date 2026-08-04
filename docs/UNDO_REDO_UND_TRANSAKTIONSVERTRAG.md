# Undo-/Redo- und Transaktionsvertrag – MULTIMODULTOOL2026

## Ziel

Jede freigegebene Papierkorb- und spätere Dateioperation erhält eine eindeutige Aktions-ID und mindestens eine eindeutige Transaktions-ID. Undo und Redo müssen wiederholbar, konfliktgeprüft, absturzsicher und in eindeutiger Reihenfolge ausführbar sein.

## Speicherort

```text
<Projekt>/.multimodultool2026/
├── history/
│   └── actions.jsonl
└── trash/
    └── transactions/<MMTTRASH-ID>/
        ├── manifest.json
        └── payload
```

- `history/`: `0700`
- `actions.jsonl`: `0600`
- Journal-Schema: Version 1
- maximale Journalgröße: 8 MiB
- maximale Ereigniszahl: 20.000
- absolute Pfade im Journal: verboten

## Kennungen

- Aktions-ID: `MMTACTION-YYYYMMDDTHHMMSS-<12 HEX>`
- Transaktions-ID: `MMTTRASH-YYYYMMDDTHHMMSS-<12 HEX>`
- Ereignis-ID: `MMTEVENT-<24 HEX>`

Eine Aktions-ID bleibt bei Undo und Redo stabil. Ein Redo erhält eine neue Papierkorb-Transaktions-ID, damit ein bereits abgeschlossenes Restore-Manifest nicht rückwirkend umgeschrieben wird.

## Append-only Journal

Jede Zeile ist ein vollständiges JSON-Objekt. Vorhandene Zeilen werden niemals geändert oder entfernt. Erlaubte Ereignisse:

1. `prepare`
2. `apply`
3. `cancel`
4. `undo-intent`
5. `undo`
6. `redo-intent`
7. `redo`

Jedes Ereignis enthält Sequenznummer, Ereignis-ID, Aktions-ID, Transaktions-ID, relative Projektquelle, Folgezustand, Recovery-Kennzeichen, Hash des vorherigen Ereignisses und eigenen SHA-256-Hash.

Das Anhängen verwendet `O_APPEND`, `O_NOFOLLOW`, exklusives `flock`, vollständiges Schreiben und `fsync`. Lücken, doppelte Ereignis-IDs, falsche Zustandsfolgen oder eine unterbrochene Hashkette blockieren weitere Aktionen.

## Reihenfolge

- Undo ist ausschließlich für die zuletzt aktive Aktion zulässig.
- Mehrere Undo-Schritte laufen in umgekehrter Aktionsreihenfolge.
- Redo ist ausschließlich für die nächste zurückgenommene Aktion zulässig.
- Mehrere Redo-Schritte laufen in ursprünglicher Aktionsreihenfolge.
- Eine neue Aktion wird blockiert, solange eine Redo-Kette vorhanden ist.

Diese Regel verhindert unklare Verzweigungen und stilles Verwerfen bereits dokumentierter Rücknahmen.

## Idempotenz

- bereits vollständig erfasste Aktion: keine zweite Ausführung
- bereits zurückgenommene Aktion: Undo meldet unveränderten Zustand
- bereits erneut angewendete Aktion: Redo meldet unveränderten Zustand
- wiederholter Abschluss nach Absturz: Manifest und Dateizustand entscheiden, ob nur das fehlende Abschlussereignis ergänzt wird

## Absturz- und Recovery-Vertrag

Vor einer Dateioperation wird ein Intent-Ereignis angehängt. Nach der atomaren Papierkorb- oder Restore-Transaktion folgt das Abschlussereignis.

Bei einem Neustart werden unvollständige Intents ausschließlich anhand sicherer Papierkorbmanifeste und eindeutiger Dateiorte abgeglichen:

- Quelle vorhanden, keine Transaktion: vorbereitete Aktion wird als `cancel` abgeschlossen
- Payload vorhanden, Original frei, Manifest `prepared` oder `trashed`: fehlendes `apply` wird ergänzt
- Manifest `restored`: fehlendes `undo` wird ergänzt
- widersprüchliche, beschädigte oder mehrdeutige Zustände: Blockade ohne automatische Reparatur

## Rein lesende Transaktionsübersicht

Die Übersicht zeigt ausschließlich:

- `prepared`
- `trashed`
- `restored`
- `damaged`

Filterung erfolgt nur nach Zustand. Beschädigte Manifeste, Symlinks, falsche Rechte und ungültige Transaktionsverzeichnisse werden markiert, aber niemals verändert.

Nicht vorhanden:

- Wiederherstellen
- Reparieren
- Löschen oder Leeren
- Upload
- automatischer Export

## Abnahme

- zehn Aktionen werden vollständig angewendet
- zehn Undo-Schritte erfolgen in exakter Rückwärtsreihenfolge
- zehn Redo-Schritte erfolgen in exakter Vorwärtsreihenfolge
- jede Aktions-ID bleibt stabil
- jede Redo-Transaktion erhält eine neue Transaktions-ID
- wiederholtes Undo/Redo erzeugt keine Doppeloperation
- Konflikte blockieren ohne Nutzdatenänderung
- Hashmanipulation und Symlinkjournal werden erkannt
- Intent-Recovery ergänzt nur fehlende Abschlussereignisse
- Transaktionsübersicht verändert keine Manifestbytes
