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
6. Sicherheitsstufe festlegen: Module mit `module.js` gelten vorerst als vertrauensintern und dürfen nicht als Drittmodule freigegeben werden.
7. Speicherregeln aus `storage` vor Import, Export oder lokaler Speicherung beachten.
8. Modul nur registrieren, wenn alle Prüfungen erfolgreich sind.
9. Fehler gesammelt und laientauglich anzeigen.

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

### Vertrauensregel für JavaScript-Module

`module.js` läuft im selben Browser-Kontext wie die Haupt-App. Das bedeutet: Ein solches Modul kann auf App-Zustand, Browser-Speicher und sichtbare Bedienflächen zugreifen. Bis eine isolierte Laufzeit oder eine Hash-Prüfung umgesetzt ist, gilt deshalb diese Grenze:

1. Module mit `module.html` und `module.css` dürfen als lesende Vorschau geprüft werden.
2. Module mit `module.js` dürfen nur als interne, im Repository geprüfte Module geladen werden.
3. Drittmodule mit `module.js` werden nicht freigegeben und müssen eine eigene Vertrauensprüfung erhalten.
4. Fehlermeldungen sollen klar sagen, dass nichts geladen und nichts gespeichert wurde, wenn die Vertrauensstufe nicht reicht.

Diese Regel schließt die Audit-Lücke zur unklaren JavaScript-Ausführung, ohne jetzt einen riskanten iframe- oder Hash-Umbau einzuführen.

## Erste Umsetzungsidee

Die erste technische Umsetzung sollte klein bleiben:

1. Reine Prüffunktion für Manifestdaten erstellen.
2. Prüffunktion mit bestehenden Manifesten testen.
3. Erst danach eine einfache Registrierungsliste für gültige Module vorbereiten.
4. Noch keine automatische Ausführung von fremdem Modul-JavaScript einbauen.
5. Für vorhandene `module.js`-Einträge nur interne Repository-Module akzeptieren und Drittmodule ablehnen.

## Phasenplan für kleine sichere Schritte

Die weitere Arbeit bleibt in drei getrennte Pfade aufgeteilt. Eine Phase gilt erst als erledigt, wenn sie einzeln prüfbar ist und ohne Datenverlust zurückgenommen werden kann.

### Phase 1: Loader-Prototyp ohne Ausführung

1. Bestehende Manifestprüfung als einzige technische Grundlage nutzen.
2. Eine kleine Registrierungsliste aus gültigen Manifesten vorbereiten.
3. Fehler gesammelt und verständlich ausgeben.
4. Noch kein Modul-JavaScript laden und keine bestehende HTML-Struktur verschieben.

### Phase 2: Ein Modul gezielt auslagern

1. Ein fachlich kleines Modul auswählen.
2. `module.html` und, falls nötig, `module.css` über das Manifest prüfen.
3. Die Anzeige zuerst nur lesend einbinden.
4. JavaScript nur aktivieren, wenn das Modul intern geprüft ist und keine Drittmodul-Freigabe behauptet wird.
5. Speichern, Import und riskante Aktionen erst nach separater Prüfung ergänzen.

### Phase 3: Rückbaupfad absichern

1. Vor jeder Auslagerung festhalten, welcher Single-File-Bereich ersetzt wird.
2. Einen Weg dokumentieren, wie das Modul wieder deaktiviert oder in die HTML-Datei zurückgeführt werden kann.
3. Alte Daten erst entfernen, wenn Modulansicht, Speicherbereich und Export geprüft sind.
4. Bei Fehlern bleibt die Single-File-App startbar; fehlerhafte Module werden übersprungen.


## Bewusste Nicht-Ziele

- Kein Build-System.
- Keine Umbenennung der HTML-Startdatei.
- Keine vollständige Zerlegung der bestehenden App.
- Kein Laden beliebiger externer Dateien aus dem Internet.
- Keine automatische Migration vorhandener Nutzerdaten.
