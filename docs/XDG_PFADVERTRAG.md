# XDG-Pfadvertrag – MULTIMODULTOOL2026

## Dauerhafte App-Bereiche

- Konfiguration: `$XDG_CONFIG_HOME/multimodultool2026`
- Daten: `$XDG_DATA_HOME/multimodultool2026`
- Cache: `$XDG_CACHE_HOME/multimodultool2026`
- Status: `$XDG_STATE_HOME/multimodultool2026`
- Logs: `$XDG_STATE_HOME/multimodultool2026/logs`
- Sicherungen: `$XDG_DATA_HOME/multimodultool2026/backups`

App-Verzeichnisse verwenden `0700`. Relative Pfade, Quellbaumziele, Symlinks, falsche Eigentümer, Doppelziele und unbeschreibbare Ziele blockieren den Start.

## Flüchtiger Instanzbereich

```text
$XDG_RUNTIME_DIR/multimodultool2026
```

Fehlt die Variable, darf nur `/run/user/<uid>` verwendet werden. Eine Ausweichlösung in `/tmp` ist verboten. App-Unterordner erhält `0700`; Socket und Metadaten `0600`.

## Projektbezogene Transaktionsdaten

Papierkorb-Payloads, Transaktionsmanifeste und das Undo-/Redo-Journal sind bewusst **keine allgemeinen XDG-App-Daten**. Sie liegen innerhalb des ausdrücklich gewählten Projekts, damit atomare Umbenennung, Wiederherstellung und eine portable Projekt-Historie möglich bleiben:

```text
<Projekt>/.multimodultool2026/
├── history/
│   └── actions.jsonl
└── trash/
    └── transactions/
```

Diese Ausnahme gilt ausschließlich für:

- reversible Dateiaktionshistorie,
- Papierkorb-Payloads,
- Transaktionsmanifeste.

Sie darf nicht als Konfigurations-, Cache-, Diagnose-, App-Log- oder allgemeiner Sicherungspfad verwendet werden.

## Sicherheitsregeln

- Projektstamm muss absolut, vorhanden, sicher beschreibbar und dem aktuellen Nutzer zugeordnet sein.
- interne Projektverzeichnisse verwenden `0700`.
- Transaktionsmanifeste und `actions.jsonl` verwenden `0600`.
- Journal enthält ausschließlich relative Projektpfade.
- Pfade dürfen das Projekt nicht verlassen.
- Symlink-Komponenten, Mountwechsel und unklare Eigentumsverhältnisse blockieren.
- es gibt keinen Fallback in den Programmquellbaum, nach `/tmp` oder in einen fremden Mount.
- rein lesende Vorschau, Journalinspektion und Transaktionsübersicht erzeugen keine Datei.

Das XDG-App-Ereignisjournal und das projektbezogene Aktionsjournal erfüllen unterschiedliche Aufgaben und dürfen nicht miteinander vermischt werden.
