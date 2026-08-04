# Single-Instance- und Diagnosevertrag

## Ziel

MULTIMODULTOOL2026 besitzt unter Linux genau eine normale GUI-Instanz pro Nutzer und Sitzung. Weitere Starts dürfen weder parallele Schreibzustände noch unkontrollierte Datenübergaben erzeugen.

## Laufzeitpfade

```text
$XDG_RUNTIME_DIR/multimodultool2026/
├── instance.sock
└── instance.json
```

- Laufzeitwurzel und App-Unterordner: aktueller Nutzer, keine Symlinks, `0700`
- Socket und Metadaten: sicherer Dateityp, ein Link, aktueller Nutzer, `0600`
- keine Ausweichsperre in `/tmp`

## Lokale Authentisierung und Nachrichten

Der Server prüft über Linux `SO_PEERCRED`, dass die Verbindung vom gleichen Nutzer stammt. Erlaubt sind nur:

- `activate`
- `show-diagnostics`
- optional eine validierte Diagnosekennung im Format `MMT-...`

Dateipfade, freie Argumentlisten, Shellbefehle, private Inhalte sowie Lösch-, Upload- und Exportaufträge sind verboten. Maximale Nachrichtengröße: 4096 Bytes.

## Stale-Recovery

Eine nicht antwortende Sperre wird nur entfernt, wenn Socket und Metadaten sicher sind und Prozessstatus oder Boot-ID eindeutig belegen, dass keine aktive Instanz mehr besteht. Beschädigte, fremde oder zweifelhafte Sperren bleiben unverändert.

## Parallelstart-Stresstest

`tests/test_single_instance_stress.py` erzeugt eine Primärinstanz und gibt danach **20 Zweitstarts nahezu gleichzeitig** über eine Thread-Barriere frei. Jede Sekundärinstanz sendet eine eindeutige erlaubte Diagnosekennung.

Pflichtinvarianten:

1. genau eine Primärinstanz bleibt bestehen,
2. alle 20 weiteren Starts erhalten die Sekundärrolle,
3. jede gültige Kennung erreicht die Primärinstanz genau einmal,
4. keine Kennung geht verloren oder wird verdoppelt,
5. nach kontrolliertem Schließen fehlen `instance.sock` und `instance.json`,
6. der private App-Laufzeitordner enthält keine Reste.

Der Test ist ein zusätzliches CI-Gate und ersetzt nicht die normalen Einzelstart-, Stale- und Beschädigungstests.

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

## Bekannte Grenze

Der automatisierte Stresslauf findet auf Ubuntu-CI statt. Physische Tests unter stark ausgelastetem KDE Plasma, X11 und Wayland bleiben zusätzlich erforderlich.
