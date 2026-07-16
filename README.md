# MULTIMODULTOOL2026

Lokales Dashboard-Werkzeug als Single-File-HTML-App. Die Anwendung soll ohne Installation, ohne Build-Schritt und direkt im Browser nutzbar bleiben.

## Aktueller Status

- Startdatei: `dashboard-studio-ultimate-pro-v3.1.0.html`
- Arbeitsmodell: Browser direkt öffnen oder Startskript verwenden
- Entwicklungsfortschritt: 63 % (Details siehe `todo.txt`)
- Modulziel: spätere manifestbasierte Module unter `modules/`
- Wichtige Regel: mittelgroße, sichere Änderungen vor großen Umbauten

## Start

Die Anwendung kann per Startskript geöffnet werden:

```sh
./scripts/start-local.sh
```

Alternativ kann die Datei direkt im Browser geöffnet werden:

```text
dashboard-studio-ultimate-pro-v3.1.0.html
```

Es ist kein Build-Schritt und keine Installation nötig.

## Daten und Backups

Die App arbeitet lokal im Browser. Je nach Funktion können Daten im Browser-Speicher liegen. Dieser Speicher ist praktisch, aber begrenzt und browserabhängig.

Wichtige Hinweise:

- Vor riskanten Importen oder Wiederherstellungen sollte ein Backup vorhanden sein.
- Große JSON-Importe sollen vor dem Speichern auf Größe und Inhalt geprüft werden.
- Keine privaten Echtdaten in Beispiel-, Import-, Export- oder Logdateien committen.
- Exportdateien sollten nachvollziehbare Namen mit Datum oder Zeitstempel bekommen.

## Modulstrategie

Ja, Module können künftig separate Dateien sein. Die laufende Version bleibt zuerst als stabile Single-File-HTML-App bestehen. Über **Module → Manifest-Module laden** oder den Button in der Seitenleiste kann die App das App-Manifest lesen und gültige Modulmanifeste ergänzend in die lokale Modulübersicht übernehmen. Beim direkten Öffnen per `file://` kann der Browser diesen Zugriff blockieren; dann bitte das Startskript oder einen lokalen Webserver verwenden.

Neue oder ausgelagerte Module sollen nach dem Modulstandard beschrieben werden:

- Standard: `standards/MULTIMODULTOOL2026_01_Modulstandard.md`
- Manifest-Schema: `manifests/MULTIMODULTOOL2026_01_ModuleManifest.schema.json`
- App-Manifest: `manifests/MULTIMODULTOOL2026_02_AppManifest.json`
- Beispielmanifest: `manifests/MULTIMODULTOOL2026_03_ExampleModule.manifest.json`
- Systemmodule-Bündel: `modules/systemmodule-buendel/module.manifest.json`

## Warum zuerst Standards?

Ein direkter Umbau der großen HTML-Datei in viele Dateien kann funktionierende Bereiche beschädigen. Die Standards legen deshalb zuerst fest, wie Module sicher benannt, beschrieben, geprüft und später geladen werden.

## Bedienbarkeit und Kontraste

Die Oberfläche nutzt ein dunkles Standarddesign mit optionalen Darstellungsmodi. Text-, Linien- und Eingabekontraste sollen gut lesbar bleiben. Änderungen am Design sollen gezielt erfolgen und die bestehende Bedienung nicht unnötig verändern.

Bei GUI-Änderungen bitte prüfen:

- Sind kleine Texte und Statusmeldungen gut lesbar?
- Sind Eingabefelder, Schaltflächen und aktive Elemente klar erkennbar?
- Bleibt die Oberfläche ohne lange Suche bedienbar?
- Sind Fehlermeldungen einfach formuliert und handlungsorientiert?

## Entwicklung

Wichtige Projektdateien:

- `todo.txt`: offene Punkte, erledigte Punkte, Fortschritt und bekannte Grenzen
- `docs/DEVELOPER_GUIDE.md`: technische Hinweise zu Struktur, Start, Barrierefreiheit und Entwicklungsabläufen
- `docs/RELEASE_CHECKLIST.md`: kurze Freigabe-Checkliste für lokale Test- und Weitergabestände
- `AGENTS.md`: verbindliche Arbeitsregeln für Änderungen in diesem Repository

Relevante Prüfungen nach Änderungen:

- HTML-Syntax prüfen, wenn die Startdatei geändert wurde.
- Markdown-Dateien kurz auf Struktur und Lesbarkeit prüfen, wenn Dokumentation geändert wurde.
- Release-Checkliste nutzen, wenn ein lokaler Stand weitergegeben oder als Freigabekandidat markiert werden soll.
- Manifestprüfung ausführen, wenn Dateien unter `manifests/` oder `modules/` betroffen sind.
- Fortschrittsangaben mit `python3 tests/validate_progress_consistency.py` abgleichen, wenn README oder `todo.txt` geändert wurden.

## Nächster sinnvoller Schritt

Als nächste Iteration sollte zuerst eine echte Browser-Sichtprüfung erfolgen: Standardstart, kaputte localStorage-Daten, Backup-Wiederherstellung, JSON-Import sowie Kontrastprüfung in Chromium und Firefox. Das Ergebnis gehört danach mit Datum in `todo.txt`, weil diese Punkte in der nicht-interaktiven Codeprüfung nicht vollständig belegbar sind.
