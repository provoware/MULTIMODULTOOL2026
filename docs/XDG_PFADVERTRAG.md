# XDG-Pfadvertrag – MULTIMODULTOOL2026

## Zweck

Dieser Vertrag trennt den ausführbaren Projektstand strikt von privaten Linux-Benutzerdaten. Das Programm darf Konfiguration, Arbeitsdaten, Cache, Status, Logs oder Sicherungen nicht ungefragt in den Quellbaum schreiben.

## Verbindliche Speicherorte

| Bereich | XDG-Grundlage | Standard ohne Umgebungsvariable |
|---|---|---|
| Konfiguration | `XDG_CONFIG_HOME` | `~/.config/multimodultool2026` |
| Nutzerdaten | `XDG_DATA_HOME` | `~/.local/share/multimodultool2026` |
| Cache | `XDG_CACHE_HOME` | `~/.cache/multimodultool2026` |
| Status | `XDG_STATE_HOME` | `~/.local/state/multimodultool2026` |
| Protokolle | Statuspfad | `~/.local/state/multimodultool2026/logs` |
| Sicherungen | Datenpfad | `~/.local/share/multimodultool2026/backups` |

## Vorvalidierung

Vor jeder Anlage werden geprüft:

1. alle gesetzten `XDG_*_HOME`-Werte sind absolute Pfade,
2. jedes App-Ziel bleibt innerhalb seiner XDG-Grenze,
3. kein Ziel liegt im Programmverzeichnis,
4. Top-Level-Ziele sind nicht doppelt belegt,
5. bestehende App-spezifische Pfade sind keine Symlinks,
6. bestehende Ziele sind Verzeichnisse und keine Dateien.

Bei einem Fehler wird der Start blockiert. Produktive Dateien bleiben unverändert.

## Sichere Anlage

- Verzeichnisse werden nach Pfadtiefe angelegt.
- App-spezifische Verzeichnisse erhalten Modus `0700`.
- XDG-Basisverzeichnisse anderer Programme werden nicht pauschal umberechtigt.
- Die Pfadschicht verwendet nur die Python-Standardbibliothek.
- Es werden keine Shell-Kommandos und kein `sudo` verwendet.

## Nachvalidierung

Nach der Anlage werden erneut geprüft:

1. jedes Pflichtverzeichnis existiert,
2. kein Ziel wurde zwischenzeitlich zu einem Symlink,
3. jedes Ziel ist beschreibbar und betretbar,
4. die XDG- und Quellbaumgrenzen gelten weiterhin,
5. eine temporäre Testdatei kann geschrieben und mit `fsync` bestätigt werden,
6. die Testdatei wird vollständig entfernt.

## Betriebsarten

### Rein lesende Gesamtprüfung

```bash
python3 -m src.main --validate-only
```

Diese Betriebsart berechnet und prüft den Pfadplan, legt aber keine Verzeichnisse an.

### Pfade anzeigen

```bash
python3 -m src.main --paths-only
```

Zeigt den berechneten Pfadplan und verändert nichts.

### Normaler Start

```bash
./start.sh
```

Nach Linux-, Manifest- und Einrichtungsprüfung werden die XDG-Verzeichnisse sicher vorbereitet. Erst bei grünem Ergebnis startet die Oberfläche.

## Datenschutz

- Vollständige Benutzerpfade werden nur dort angezeigt, wo sie zur Diagnose nötig sind.
- Portable Projektdateien speichern keine absoluten Benutzerpfade.
- Logs werden später ausschließlich im XDG-State-Bereich angelegt und benötigen einen Datenschutzfilter.
- Die XDG-Pfadschicht liest oder protokolliert keine Inhalte privater Dateien.

## Fehlerverhalten

Eine Fehlermeldung nennt:

- betroffenen Bereich,
- konkreten Grund,
- Fole für den Start,
- unveränderten Datenstand,
- verständlichen Lösungsweg.

Bei Fehlern findet keine automatische Ausweichsspeicherung in den Programmordner statt.

## Änderungsregel

Änderungen an Speicherorten, Rechten, Symlinkbehandlung, Schreibprüfung oder Pfadgrenzen erfordern im selben Entwicklungsstand:

- Anpassung von `src/xdg_paths.py`,
- passende Tests in `tests/test_xdg_paths.py`,
- Aktualisierung dieser Datei,
- Prüfung von README, Anleitung, Entwicklerdokumentation, Schwachstellen und Changelog,
- erfolgreichen Repository-Vertrag und GitHub-Workflow.


## Einstellungsdateien im Konfigurationsbereich

Innerhalb des validierten Konfigurationsverzeichnisses verwendet die Anwendung:

- `settings.json` – aktive, schema-geprüfte Einstellungen,
- `settings.last-valid.json` – letzte gültige Sicherung,
- `settings.corrupt-<UTC-Zeit>.json` – lokal isolierte beschädigte Datei.

Diese Dateien verwenden Modus `0600`, dürfen keine Symlinks sein und bleiben innerhalb von `XDG_CONFIG_HOME`. Details stehen in `docs/EINSTELLUNGSVERTRAG.md`.

Die rein lesenden Modi `--validate-only` und `--settings-only` dürfen weder XDG-Verzeichnisse noch Einstellungsdateien erzeugen oder verändern.
