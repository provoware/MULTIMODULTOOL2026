# Provoware GenreTool Pro 2.0

## Zweck

Vollständig eigenständiges Songs-Untermodul für eine lokale Kreativdatenbank mit Genres, Stimmungen, Stilen, Effekten, Themen und Besonderheiten. Das Modul verwaltet die Begriffe dauerhaft und erzeugt daraus kopierbare Zufallskombinationen.

## Vollständiger Funktionsumfang

- Mitgelieferte `genres_db.json` mit 1.800 datenbankweit eindeutigen Startbegriffen.
- Je 300 Werte in Genres, Stimmungen, Stilen, Effekten, Themen und Besonderheiten.
- Automatisches, nicht destruktives Laden der Startdaten bei leerem Modul-Speicher.
- Mehrfacheingabe über Komma, Semikolon oder Zeilenumbruch.
- Datenbankweite Dublettenprüfung ohne Beachtung von Groß-/Kleinschreibung.
- Suche, Kategorienfilter, A–Z/Z–A-Sortierung, Favoriten- und Eigene-zuerst-Sortierung.
- Seitenanzeige für große Datenbestände mit 40 Einträgen pro Seite.
- Ergänzen, Bearbeiten, Löschen, Favorisieren und Kopieren.
- Datenbankprüfung auf ungültige Kategorien und normalisierte Dubletten.
- Frei wählbare Mixer-Kategorien und ein bis zwölf Ergebnisse pro Durchlauf.
- Optionales Meiden der letzten Treffer und Bevorzugen von Favoriten.
- Einzelne Ergebnisbestandteile sperren und nur offene Bestandteile neu würfeln.
- Einzelnes Ergebnis oder alle Ergebnisse kopieren; Fallback für ältere Browser.
- Verlauf der letzten 50 erzeugten Kombinationen.
- JSON-, TXT- und CSV-Import bis 8 MB.
- Export, lokale Sicherung, Backup-Datei, Rücksetzen auf Startdaten sowie Undo/Redo.
- Gekapselter lokaler Speicherbereich: `multimodultool2026.provoware-genretool-pro.v2`.
- Statusmeldungen über Speichern, Abbruch, Fehler und unveränderte Daten.
- Tastaturbedienbare Formulare, Schaltflächen und Dialoge.

## Dateien

- `module.manifest.json`: Modulbeschreibung, Version und Sicherheitsgrenzen.
- `module.html`: gekapselte, barrierearme Oberfläche.
- `module.css`: responsives Modullayout für kleine und große Panels.
- `module.js`: vollständige Fachlogik, Persistenz und Bedienung.
- `genres_db.json`: geprüfte Startdatenbank.
- `preview.html`: direkt nutzbare Modulvorschau über den lokalen Server.

## Start und Vorschau

Projekt starten:

```sh
./scripts/start-local.sh
```

Danach im Browser öffnen:

```text
modules/provoware-genretool-pro/preview.html
```

Ein direkter Start über `file://` kann das Laden von `genres_db.json` blockieren. Eigene, bereits gespeicherte Daten bleiben davon unberührt.

## Einbindung

Das Modul ist im App-Manifest registriert:

```text
../modules/provoware-genretool-pro/module.manifest.json
```

Die dateibasierte Moduloberfläche ist vollständig funktionsfähig. Die Hauptanwendung muss für eine direkte Einbettung weiterhin die im Manifest angegebenen HTML-, CSS- und JS-Einstiegspunkte laden; die separate Vorschau funktioniert bereits vollständig.

## Prüfung

```sh
python3 tests/validate_module_manifests.py
python3 tests/validate_genres_module.py
node --check modules/provoware-genretool-pro/module.js
python3 -m json.tool modules/provoware-genretool-pro/genres_db.json >/dev/null
```

Die GenreTool-Prüfung kontrolliert:

- Manifest-Version und Einstiegspunkte,
- Registrierung im App-Manifest,
- alle Pflichtrollen und Bedienaktionen der Oberfläche,
- das Fehlen von Platzhaltern,
- JavaScript-Syntax und zentrale Laufzeitfunktionen,
- exakt 1.800 normalisierte, datenbankweit eindeutige Startbegriffe.

## Rückbau

Vor riskanten Änderungen `Datenbank exportieren` oder `Backup erstellen` verwenden. Änderungen an Einträgen können zusätzlich über Undo/Redo zurückgenommen werden. Das Zurücksetzen lädt nur nach Bestätigung erneut die geprüfte Startdatenbank.
