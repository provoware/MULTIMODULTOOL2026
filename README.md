# MULTIMODULTOOL2026

Lokales Dashboard-Werkzeug als Single-File-HTML-App. Die Anwendung soll ohne Installation, ohne Build-Schritt und direkt im Browser nutzbar bleiben.

## Aktueller Status

- Startdatei: `dashboard-studio-ultimate-pro-v3.1.0.html`
- Arbeitsmodell: empfohlenes Startskript mit lokalem Server; direkter Datei-Start nur als eingeschränkter Rückfall
- Entwicklungsfortschritt: 91 % (Details siehe `todo.txt`)
- Modulziel: spätere manifestbasierte Module unter `modules/`
- Wichtige Regel: mittelgroße, sichere Änderungen vor großen Umbauten

## Start

Die Anwendung sollte per Startskript geöffnet werden. Das Skript prüft die wichtigsten Projektdateien, sucht einen freien lokalen Port, startet einen kleinen lokalen Python-Server und öffnet die App im Browser:

```sh
./scripts/start-local.sh
```

Alternativ kann die Datei direkt im Browser geöffnet werden. Das ist nur ein eingeschränkter Rückfall, weil Browser beim Datei-Start ausgelagerte Manifest-, Modul- und Startdaten-Dateien blockieren können:

```text
dashboard-studio-ultimate-pro-v3.1.0.html
```

Es ist kein Build-Schritt nötig. Für das empfohlene Startskript wird nur ein vorhandenes `python3` oder `python` verwendet.

## Daten und Backups

Die App arbeitet lokal im Browser. Je nach Funktion können Daten im Browser-Speicher liegen. Dieser Speicher ist praktisch, aber begrenzt und browserabhängig.

Wichtige Hinweise:

- Vor riskanten Importen oder Wiederherstellungen sollte ein Backup vorhanden sein.
- In den Einstellungen kann **Speicher prüfen** einen kurzen Browser-Speicher-Test, eine Speicher-Schätzung und einen Backup-Lesetest ausführen, ohne Nutzdaten zu verändern.
- Große JSON-Importe sollen vor dem Speichern auf Größe und Inhalt geprüft werden.
- Keine privaten Echtdaten in Beispiel-, Import-, Export- oder Logdateien committen.
- Exportdateien sollten nachvollziehbare Namen mit Datum oder Zeitstempel bekommen.

## Modulstrategie

Ja, Module können künftig separate Dateien sein. Die laufende Version bleibt zuerst als stabile Single-File-HTML-App bestehen. Über **Module → Manifest-Module laden** oder den Button in der Seitenleiste kann die App das App-Manifest lesen und gültige Modulmanifeste ergänzend in die lokale Modulübersicht übernehmen. Beim direkten Öffnen per `file://` kann der Browser diesen Zugriff blockieren; deshalb startet `./scripts/start-local.sh` automatisch einen lokalen Server und öffnet die App über `http://127.0.0.1`.

Neue oder ausgelagerte Module sollen nach dem Modulstandard beschrieben werden:

- Standard: `standards/MULTIMODULTOOL2026_01_Modulstandard.md`
- Manifest-Schema: `manifests/MULTIMODULTOOL2026_01_ModuleManifest.schema.json`
- App-Manifest: `manifests/MULTIMODULTOOL2026_02_AppManifest.json`
- Beispielmanifest: `manifests/MULTIMODULTOOL2026_03_ExampleModule.manifest.json`
- Systemmodule-Bündel: `modules/systemmodule-buendel/module.manifest.json`
- HTML-Auslagerungsplan: `docs/HTML_AUSLAGERUNGSPLAN.md`

## Warum zuerst Standards?

Ein direkter Umbau der großen HTML-Datei in viele Dateien kann funktionierende Bereiche beschädigen. Die Standards legen deshalb zuerst fest, wie Module sicher benannt, beschrieben, geprüft und später geladen werden.

## Bedienbarkeit und Kontraste

Die Oberfläche nutzt ein dunkles Standarddesign mit optionalen Darstellungsmodi. Text-, Linien-, Statuschip- und Eingabekontraste sollen gut lesbar bleiben. Die Kontrast- und Fokuszustände wurden am 2026-07-16 gezielt nachgeschärft; die echte Chromium-/Firefox-Sichtprüfung muss auf einer Browserinstallation nachgeholt werden, weil Snap- und Playwright-Browserdownloads im Container blockiert waren. Änderungen am Design sollen weiter gezielt erfolgen und die bestehende Bedienung nicht unnötig verändern.

Bei GUI-Änderungen bitte prüfen:

- Sind kleine Texte und Statusmeldungen gut lesbar?
- Sind Eingabefelder, Schaltflächen und aktive Elemente klar erkennbar?
- Bleibt die Oberfläche ohne lange Suche bedienbar?
- Sind Fehlermeldungen einfach formuliert und handlungsorientiert?
- Passt sich das 3×3-Raster ohne unnötiges horizontales Scrollen an kleine und große Browserfenster an?
- Lassen sich aktive Module per Tastatur einblenden und platzierte Module mit Pfeiltasten im Raster verschieben?

## Entwicklung

Wichtige Projektdateien:

- `todo.txt`: offene Punkte, erledigte Punkte, Fortschritt und bekannte Grenzen
- `docs/DEVELOPER_GUIDE.md`: technische Hinweise zu Struktur, Start, Barrierefreiheit und Entwicklungsabläufen
- `docs/RELEASE_CHECKLIST.md`: kurze Freigabe-Checkliste für lokale Test- und Weitergabestände
- `docs/RELEASE_STATUS_2026-07-16.md`: aktuelles Release-Kandidaten-Protokoll mit lokalen Vorprüfungen und offenen Browserpunkten
- `AGENTS.md`: verbindliche Arbeitsregeln für Änderungen in diesem Repository

Relevante Prüfungen nach Änderungen:

- HTML-Syntax prüfen, wenn die Startdatei geändert wurde.
- Markdown-Dateien kurz auf Struktur und Lesbarkeit prüfen, wenn Dokumentation geändert wurde.
- Release-Checkliste nutzen, wenn ein lokaler Stand weitergegeben oder als Freigabekandidat markiert werden soll.
- Manifestprüfung ausführen, wenn Dateien unter `manifests/` oder `modules/` betroffen sind.
- Fortschrittsangaben mit `python3 tests/validate_progress_consistency.py` abgleichen, wenn README oder `todo.txt` geändert wurden.

## Nächster sinnvoller Schritt

Als nächste Iteration sollte das Release-Kandidaten-Protokoll in `docs/RELEASE_STATUS_2026-07-16.md` in einer echten Browserumgebung abgearbeitet werden: Chromium-Start, Firefox-Start, Speicherprüfung, Backup-Wiederherstellung, kleiner JSON-Import und Exportdownload. Die lokale Code-Vorprüfung ist getrennt dokumentiert, damit Freigabeprüfungen nicht mit Layoutänderungen vermischt werden.
