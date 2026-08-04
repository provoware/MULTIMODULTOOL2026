# XDG-Pfadvertrag – MULTIMODULTOOL2026

## Dauerhafte App-Bereiche

- Konfiguration: `$XDG_CONFIG_HOME/multimodultool2026`
- Daten: `$XDG_DATA_HOME/multimodultool2026`
- Cache: `$XDG_CACHE_HOME/multimodultool2026`
- Status: `$XDG_STATE_HOME/multimodultool2026`
- Logs: `$XDG_STATE_HOME/multimodultool2026/logs`
- Sicherungen: `$XDG_DATA_HOME/multimodultool2026/backups`

App-Verzeichnisse verwenden `0700`. Relative Pfade, Quellbaumziele, Symlinks, falsche Eigentümer, Doppelziele und unbeschreibbare Ziele blockieren.

## Flüchtiger Instanzbereich

```text
$XDG_RUNTIME_DIR/multimodultool2026
```

Fehlt die Variable, ist ausschließlich `/run/user/<uid>` erlaubt. `/tmp` ist verboten. App-Unterordner verwendet `0700`; Socket und Metadaten `0600`.

## Projektbezogene Transaktionsdaten

Papierkorb, Undo-/Redo-Historie und Laufcheckpoints liegen bewusst innerhalb des ausdrücklich gewählten Projekts:

```text
<Projekt>/.multimodultool2026/
├── history/actions.jsonl
├── runs/<MMTRUN-ID>/
└── trash/transactions/<MMTTRASH-ID>/
```

Diese Ausnahme ist erforderlich, damit Dateioperationen und Wiederherstellung auf demselben Dateisystem bleiben. Sie darf nicht als allgemeiner App-Konfigurations-, Cache- oder Logpfad verwendet werden.

Sicherheitsregeln:

- Projektstamm absolut, vorhanden, sicher beschreibbar und dem aktuellen Nutzer zugeordnet,
- interne Verzeichnisse `0700`, private Dateien `0600`,
- keine absoluten Pfade in Plan oder Aktionsjournal,
- keine Symlink-Komponenten oder Mountwechsel,
- kein Fallback in Programmquellbaum, `/tmp` oder fremden Mount,
- read-only Prüfungen erzeugen keine Transaktion.

## Installierte Offline-Runtime

Der Systempaketinhalt liegt unter `/usr/lib/multimodultool2026`. Der erste Start erzeugt pro Build-ID ausschließlich unter `$XDG_DATA_HOME/multimodultool2026/runtime/` einen privaten venv-Slot. Upgrade und Rollback überschreiben keinen bestehenden Slot. Normale Paketentfernung bewahrt XDG-Daten; ein vollständiger Purge ist separat, explizit und auf die bekannten Pfade eines eindeutig bestimmten Nicht-root-Nutzers begrenzt.
