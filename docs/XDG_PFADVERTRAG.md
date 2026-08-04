# XDG-Pfadvertrag – MULTIMODULTOOL2026

## Dauerhafte Bereiche

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

Fehlt die Variable, darf nur `/run/user/<uid>` verwendet werden. Eine Ausweichlösung in `/tmp` ist verboten.

Prüfungen:

- absoluter vorhandener Verzeichnispfad
- aktueller Linux-Nutzer als Eigentümer
- keine Symlinks
- Modus `0700`
- beschreibbar und durchsuchbar

Der App-Unterordner erhält `0700`; Socket und Metadaten `0600`. Laufzeitdaten werden beim kontrollierten Ende entfernt. Rein lesende Modi `--validate-only`, `--paths-only` und `--settings-only` erzeugen keine Laufzeit-, Socket- oder Metadatendateien.
