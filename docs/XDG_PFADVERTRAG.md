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

## Projektbezogener Papierkorb

Der Papierkorb ist bewusst **kein XDG-App-Datenbereich**. Er liegt innerhalb des ausdrücklich gewählten Projekts, damit atomare Umbenennung und Wiederherstellung auf demselben Dateisystem möglich bleiben:

```text
<Projekt>/.multimodultool2026/trash/transactions/
```

Diese Ausnahme gilt ausschließlich für transaktionsbezogene Payloads und Manifeste des gewählten Projekts. Sie darf nicht als allgemeiner Konfigurations-, Cache-, Log- oder App-Datenpfad verwendet werden.

Sicherheitsregeln:

- Projektstamm muss absolut, vorhanden, sicher beschreibbar und dem aktuellen Nutzer zugeordnet sein.
- interne Projektpapierkorb-Verzeichnisse verwenden `0700`.
- Transaktionsmanifeste verwenden `0600`.
- Pfade dürfen das Projekt nicht verlassen.
- Symlink-Komponenten, Mountwechsel und unklare Eigentumsverhältnisse blockieren.
- es gibt keinen Fallback in den Quellbaum des Programms, nach `/tmp` oder in einen fremden Mount.

Rein lesende Vorschau und App-Prüfmodi erzeugen keine Papierkorbtransaktion.
