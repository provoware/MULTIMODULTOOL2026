# Einstellungsvertrag – MULTIMODULTOOL2026

## Zweck

Dieser Vertrag definiert das versionierte, transaktionale Einstellungsformat. Einstellungen liegen ausschließlich im geprüften XDG-Konfigurationsverzeichnis und niemals im Programmverzeichnis.

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
- unbekannte oder zukünftige Versionen werden blockiert
- unbekannte Felder, falsche Typen und Werte außerhalb definierter Grenzen werden blockiert
- Sicherheitswerte `defaultDryRun` und `confirmDestructiveActions` bleiben `true`
- künftige Migrationen benötigen eine separate idempotente Migrationsschicht

## Vorvalidierung

Vor jedem Speichern werden geprüft:

1. JSON-Datenmodell,
2. `schemaVersion`,
3. erlaubte Felder,
4. Datentypen und Wertebereiche,
5. unveränderliche Sicherheitsvorgaben,
6. absoluter XDG-Konfigurationspfad,
7. Symlinkfreiheit,
8. reguläre Dateien,
9. Dateirechte `0600`.

Ungültige Daten werden nicht geschrieben. Die aktive Datei bleibt unverändert.

## Atomarer Schreibvorgang

1. Daten vollständig vorvalidieren.
2. Temporäre Datei im selben Konfigurationsverzeichnis anlegen.
3. Rechte sofort auf `0600` setzen.
4. JSON vollständig schreiben.
5. Datei mit `fsync` bestätigen.
6. Temporäre Datei erneut einlesen und validieren.
7. aktuelle gültige Datei als `settings.last-valid.json` sichern.
8. temporäre Datei mit `os.replace` atomar aktivieren.
9. Zielverzeichnis mit `fsync` bestätigen.
10. aktive Datei nachvalidieren.
11. temporäre Reste in jedem Fehlerfall entfernen.

## Automatisches Rollback

Ist `settings.json` beschädigt oder inkompatibel:

1. defekte Datei als `settings.corrupt-<UTC-Zeit>.json` isolieren,
2. letzte gültige Sicherung prüfen,
3. gültige Sicherung atomar aktivieren,
4. ohne Sicherung sichere Standardwerte aktivieren,
5. Recovery über die zentrale Fehler- und Ereignisschicht melden.

Produktive Dateiaktionen bleiben gesperrt, bis die Einstellungsschicht gültig ist.

## Failpoint-Schnittstelle

`write_settings()` akzeptiert optional einen expliziten Test-Hook. Im normalen Produktionsstart wird kein Hook übergeben.

Deklarierte Punkte:

- `before_temp_write`
- `after_temp_write`
- `before_fsync`
- `after_fsync`
- `before_backup`
- `after_backup`
- `before_replace`
- `after_replace`
- `before_postvalidate`
- `after_postvalidate`

Die Testmatrix beweist für jeden Punkt:

- aktive Datei ist vollständige alte oder vollständige neue Konfiguration,
- vorhandene Sicherung ist vollständig und schema-gültig,
- keine temporäre Datei bleibt zurück,
- der ausgelöste Failpoint wird im Ergebnis benannt.

## Rein lesende Prüfung

```bash
python3 -m src.main --validate-only
python3 -m src.main --settings-only
```

Diese Modi legen keine Verzeichnisse oder Dateien an, verändern nichts und zeigen nur den möglichen Recovery-Weg.

## Fehler- und Ereignisintegration

- blockierte Einstellungen erzeugen ein Fehlerereignis,
- Recovery erzeugt ein Warnereignis,
- jeder Bericht nennt Ursache, Folge, Datenstand, Lösung, Diagnosekennung und sicheren nächsten Schritt,
- isolierte Dateien bleiben lokal im XDG-Konfigurationsbereich.

## Datenschutz

- keine Passwörter, Tokens oder privaten Schlüssel in Einstellungen,
- keine automatische GitHub- oder Cloud-Übertragung,
- private vollständige Benutzerpfade nicht in portable Projektdateien übernehmen.
