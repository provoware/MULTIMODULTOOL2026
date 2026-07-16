# Manifest-Loader-Konzept

Stand: 2026-07-16

## Ziel

Der Manifest-Loader soll später Module aus `modules/` vorbereitet prüfen, bevor sie in die lokale Dashboard-App eingebunden werden. Die bestehende Datei `dashboard-studio-ultimate-pro-v3.1.0.html` bleibt der Startpunkt und muss ohne Build-Schritt direkt im Browser laufen.

Dieses Konzept beschreibt nur das gewünschte Verhalten. Es aktiviert noch keinen dynamischen Loader.

## Grundprinzip

Ein Modul wird erst akzeptiert, wenn sein `module.manifest.json` vollständig und verständlich geprüft wurde. Ungültige Module werden nicht geladen. Die App zeigt stattdessen eine einfache Meldung mit Ursache und nächstem Schritt.

## Geplanter Ablauf

1. Modulordner aus einer bekannten Liste lesen.
2. `module.manifest.json` je Modul laden.
3. Pflichtfelder gegen `manifests/MULTIMODULTOOL2026_01_ModuleManifest.schema.json` prüfen.
4. Einstiegspunkte aus `entry` nur akzeptieren, wenn sie auf erlaubte Moduldateien zeigen.
5. Berechtigungen aus `permissions` mit der tatsächlichen Nutzung abgleichen.
6. Speicherregeln aus `storage` vor Import, Export oder lokaler Speicherung beachten.
7. Modul nur registrieren, wenn alle Prüfungen erfolgreich sind.
8. Fehler gesammelt und laientauglich anzeigen.

## Mindestprüfung je Manifest

- `id`: klein geschrieben, eindeutig und passend zum Modulordner.
- `name`: kurz genug für die Oberfläche.
- `version`: SemVer im Format `1.0.0`.
- `type`: einer der erlaubten Typen aus dem Schema.
- `description`: verständliche Aufgabe des Moduls.
- `entry`: nur `module.html`, `module.css`, `module.js` oder `null`.
- `permissions`: nur erlaubte Werte, keine doppelten Einträge.
- `storage`: eigener Modulbereich bevorzugt; Backup-Pflicht beachten.
- `validation`: Eingabegröße und erlaubte Dateiendungen prüfen.

## Fehlerverhalten

Fehlermeldungen sollen immer vier Fragen beantworten:

1. Was ist passiert?
2. Warum ist es passiert?
3. Was kann der Nutzer tun?
4. Wurde etwas geladen, gespeichert oder abgebrochen?

Beispiel:

```text
Modul wurde nicht geladen. Das Manifest von "notizen" enthält eine unbekannte Berechtigung. Bitte die Datei module.manifest.json prüfen. Es wurde nichts gespeichert oder verändert.
```

## Sicherheitsgrenzen

- Kein Modul darf ohne gültiges Manifest starten.
- Kein Modul darf außerhalb seines eigenen Datenbereichs speichern, außer das Manifest erlaubt es ausdrücklich.
- Importierte Daten werden vor dem Speichern geprüft.
- Riskante Aktionen brauchen eine sichtbare Bestätigung.
- Fehlerhafte Module blockieren nicht die gesamte App, sondern werden übersprungen.

## Erste Umsetzungsidee

Die erste technische Umsetzung sollte klein bleiben:

1. Reine Prüffunktion für Manifestdaten erstellen.
2. Prüffunktion mit bestehenden Manifesten testen.
3. Erst danach eine einfache Registrierungsliste für gültige Module vorbereiten.
4. Noch keine automatische Ausführung von fremdem Modul-JavaScript einbauen.

## Bewusste Nicht-Ziele

- Kein Build-System.
- Keine Umbenennung der HTML-Startdatei.
- Keine vollständige Zerlegung der bestehenden App.
- Kein Laden beliebiger externer Dateien aus dem Internet.
- Keine automatische Migration vorhandener Nutzerdaten.
