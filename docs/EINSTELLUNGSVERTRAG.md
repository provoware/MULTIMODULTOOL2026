# Einstellungsvertrag – MULTIMODULTOOL2026

## Zweck

Dieser Vertrag definiert das versionierte, transaktionale Einstellungsformat. Einstellungen liegen ausschließlich im bereits geprüften XDG-Konfigurationsverzeichnis und niemals im Programmverzeichnis.

## Dateien

| Zweck | Datei | Rechte |
|---|---|---:|
| aktive Einstellungen | `settings.json` | `0600` |
| letzte gültige Sicherung | `settings.last-valid.json` | `0600` |
| formaler Vertrag | `standards/settings-schema-v1.json` | Repository-Datei |

Standardpfad:

```text
~/.config/multimodultool2026/settings.json
```

## Versionierung

- Aktuelle `schemaVersion`: **1**
- Unbekannte oder zukünftige Versionen werden nicht stillschweigend interpretiert.
- Unbekannte Felder, falsche Datentypen und Werte außerhalb definierter Grenzen werden blockiert.
- Sichere Standardwerte sind im Code und im JSON-Schema konsistent festgelegt.
- Migrationen zwischen künftigen Versionen benötigen eine separate, idempotente und getestete Migrationsschicht.

## Vorvalidierung

Vor jedem Speichern werden geprüft:

1. gültiges JSON-Datenmodell,
2. bekannte `schemaVersion`,
3. ausschließlich erlaubte Felder,
4. Datentypen und Wertebereiche,
5. unveränderliche Sicherheitsvorgaben,
6. absoluter XDG-Konfigurationspfad,
7. keine Symlinks,
8. reguläre Dateien statt Verzeichnissen oder Spezialdateien,
9. private Dateirechte `0600`.

Ungültige Daten werden nicht geschrieben. Die aktive Datei bleibt unverändert.

## Atomarer Schreibvorgang

1. Daten vollständig vorvalidieren.
2. Temporäre Datei im selben Konfigurationsverzeichnis anlegen.
3. Rechte sofort auf `0600` setzen.
4. JSON vollständig schreiben.
5. Datei mit `fsync` bestätigen.
6. Temporäre Datei erneut einlesen und validieren.
7. Aktuelle gültige Datei als `settings.last-valid.json` sichern.
8. Temporäre Datei mit `os.replace` atomar aktivieren.
9. Zielverzeichnis mit `fsync` bestätigen.
10. Aktive Datei nachvalidieren.
11. Temporäre Reste in jedem Fehlerfall entfernen.

## Automatisches Rollback

Ist `settings.json` beschädigt, unvollständig oder nicht kompatibel:

1. die defekte Datei wird als `settings.corrupt-<UTC-Zeit>.json` isoliert,
2. die letzte gültige Sicherung wird geprüft,
3. bei gültiger Sicherung erfolgt ein atomarer Rollback,
4. ohne gültige Sicherung werden sichere Standardwerte atomar angelegt,
5. Ursache und verwendete Quelle werden verständlich gemeldet.

Eine defekte Konfiguration darf keine produktiven Dateifunktionen freischalten.

## Rein lesende Prüfung

```bash
python3 -m src.main --validate-only
python3 -m src.main --settings-only
```

Diese Modi dürfen keine Verzeichnisse oder Dateien anlegen, verändern, umbenennen oder löschen. Sie zeigen nur, ob beim normalen Start eine Wiederherstellung möglich wäre.

## Datenschutz

- Einstellungen enthalten keine Passwörter, Tokens oder privaten Schlüssel.
- Private vollständige Benutzerpfade werden nicht in portable Projektdateien übernommen.
- Beschädigte Dateien bleiben lokal im XDG-Konfigurationsbereich.
- Keine Einstellungsdatei wird automatisch auf GitHub übertragen.

## Tests

Pflichtfälle:

- gültige Standardwerte,
- unbekanntes Feld,
- unbekannte Version,
- falscher Datentyp,
- Werte außerhalb der Grenzen,
- erster Start,
- atomarer Austausch,
- letzte gültige Sicherung,
- beschädigte aktive Datei,
- fehlende Sicherung,
- Symlinkblockade,
- zu offene Dateirechte,
- simulierter Austauschfehler,
- rein lesende Prüfung ohne Schreibzugriff.

## Pflegepflicht

Änderungen an Struktur, Version, Sicherheitswerten, Speicherweg, Backup oder Rollback aktualisieren im selben Commit:

- `src/settings_manager.py`
- `standards/settings-schema-v1.json`
- `tests/test_settings_manager.py`
- `docs/EINSTELLUNGSVERTRAG.md`
- `ANLEITUNG_TOOL.md`
- `ENTWICKLERDOKU.md`
- `CHANGELOG.md`
- `TODO.md`
- `README.md`
