# Single-Instance- und Diagnosevertrag

## Ziel

MULTIMODULTOOL2026 besitzt unter Linux genau eine normale GUI-Instanz pro Nutzer und Sitzung. Weitere Starts dürfen weder parallele Schreibzustände noch unkontrollierte Datenübergaben erzeugen.

## Laufzeitpfade

```text
$XDG_RUNTIME_DIR/multimodultool2026/
├── instance.sock
└── instance.json
```

- Laufzeitwurzel und App-Unterordner: Eigentümer aktueller Nutzer, keine Symlinks, Modus `0700`
- Socket und Metadaten: Eigentümer aktueller Nutzer, sichere Dateitypen, Modus `0600`
- keine Ausweichsperre in `/tmp`

## Lokale Authentisierung

Der Server prüft über Linux `SO_PEERCRED`, dass die Verbindung vom gleichen Nutzer stammt. Nachrichten anderer Nutzer werden abgelehnt.

## Erlaubte Nachrichten

- `activate`
- `show-diagnostics`
- optional eine Diagnosekennung im Format `MMT-...`

Verboten:

- Dateipfade
- freie Argumentlisten
- Shellbefehle
- private Dateiinhalte
- Lösch-, Upload- oder Exportaufträge
- unbekannte Felder und Schemaversionen

Maximale Nachrichtengröße: 4096 Bytes.

## Stale-Recovery

Eine nicht antwortende Sperre wird nur entfernt, wenn:

1. Socket und Metadaten sicher und dem aktuellen Nutzer zugeordnet sind,
2. Metadaten vollständig und schema-gültig sind,
3. Prozess nicht mehr lebt oder Boot-ID nicht mehr zur aktuellen Sitzung gehört.

Lebender, aber nicht antwortender Prozess, fehlende Metadaten, beschädigtes JSON, Symlink, falscher Eigentümer oder falscher Dateityp blockieren den Start. Der Zustand bleibt unverändert.

## Qt-Übergabe

Der Socketserver arbeitet in einem Hintergrundthread. Gültige Nachrichten gelangen über eine threadsichere Queue und einen Qt-Timer in den Hauptthread. Dort wird das vorhandene Fenster sichtbar gemacht und die Diagnosezentrale optional gefiltert.

## Diagnosezentrale

- ausschließlich lesender Zugriff auf `events.jsonl`
- Filter nach Schweregrad und Diagnosekennung
- vollständige sechs Nutzerfelder sichtbar
- einzelner bereinigter Bericht kopierbar
- kein Löschen, Upload, Auto-Export oder Reparieren
- maximal 2 MiB und 500 gültige Einträge pro Ansicht
- beschädigte Zeilen werden gemeldet und übersprungen

## Abnahme

- zweiter Start aktiviert vorhandene Instanz
- nur erlaubte Nachricht erreicht Primärinstanz
- stale Socket mit totem Prozess wird sicher ersetzt
- beschädigte Sperre bleibt erhalten und blockiert
- Peer-UID wird geprüft
- Diagnosezugriff verändert keine Journalbytes
- Offscreen-GUI enthält Filter, read-only Detail und Kopierfunktion, aber keine verbotenen Aktionen
