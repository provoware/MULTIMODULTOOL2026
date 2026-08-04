# XDG-Pfadvertrag – MULTIMODULTOOL2026

## Zweck

Dieser Vertrag trennt ausführbaren Projektstand strikt von privaten Linux-Benutzerdaten. Konfiguration, Arbeitsdaten, Cache, Status, Logs oder Sicherungen dürfen nicht ungefragt in den Quellbaum geschrieben werden.

## Verbindliche Speicherorte

| Bereich | XDG-Grundlage | Standardpfad |
|---|---|---|
| Konfiguration | `XDG_CONFIG_HOME` | `~/.config/multimodultool2026` |
| Nutzerdaten | `XDG_DATA_HOME` | `~/.local/share/multimodultool2026` |
| Cache | `XDG_CACHE_HOME` | `~/.cache/multimodultool2026` |
| Status | `XDG_STATE_HOME` | `~/.local/state/multimodultool2026` |
| Protokolle | Statuspfad | `~/.local/state/multimodultool2026/logs` |
| Sicherungen | Datenpfad | `~/.local/share/multimodultool2026/backups` |

## Vorvalidierung

Vor jeder Anlage werden geprüft:

1. gesetzte `XDG_*_HOME`-Werte sind absolute Pfade,
2. jedes Ziel bleibt innerhalb seiner XDG-Grenze,
3. kein Ziel liegt im Programmverzeichnis,
4. Top-Level-Ziele sind nicht doppelt belegt,
5. App-Pfade enthalten keine Symlinks,
6. bestehende Ziele sind Verzeichnisse.

Bei Fehlern wird der Start blockiert. Produktive Dateien bleiben unverändert.

## Sichere Anlage

- Verzeichnisse werden nach Pfadtiefe angelegt.
- App-Verzeichnisse erhalten `0700`.
- XDG-Basisverzeichnisse anderer Programme werden nicht umberechtigt.
- keine Shell-Kommandos und kein `sudo`.

## Nachvalidierung

Nach Anlage werden Existenz, Symlinkfreiheit, Schreib-/Betretbarkeit, Grenzen und eine temporäre Schreibprobe mit `fsync` geprüft. Die Prüfdatei wird vollständig entfernt.

## Ereignisjournal

Das zentrale Journal liegt unter:

```text
~/.local/state/multimodultool2026/logs/events.jsonl
```

- reguläre Datei, kein Symlink
- Rechte `0600`
- JSONL-Format
- `fsync` nach jedem Ereignis
- unsicheres Journal blockiert den normalen Start

## Betriebsarten

```bash
python3 -m src.main --validate-only
python3 -m src.main --paths-only
```

Beide sind rein lesend. `--validate-only` darf keine XDG-Verzeichnisse anlegen.

## Datenschutz

Private vollständige Pfade werden in Nutzerberichten auf `~` reduziert. Keine privaten Dateiinhalte oder Geheimnisse in Logs oder portable Projektdateien übernehmen.
