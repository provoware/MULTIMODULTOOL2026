# Provoware GenreTool Pro

## Zweck

Songs-Untermodul für eine lokale Kreativdatenbank mit Genres, Stimmungen, Stilen, Effekten, Themen und Besonderheiten. Das Modul erzeugt daraus kopierbare Zufallskombinationen.

## Funktionsumfang

- Mitgelieferte `genres_db.json` mit 1.800 datenbankweit eindeutigen Einträgen.
- Je 300 Werte in Genres, Stimmungen, Stilen, Effekten, Themen und Besonderheiten.
- Suche, Kategorienfilter, Ergänzen, Bearbeiten, Löschen und Favorisieren.
- Ein bis zwölf Zufallsergebnisse mit sechs Kategorien.
- Einzelne Ergebnisbestandteile sperren und offene Bestandteile neu würfeln.
- Kopieren, Verlauf, Import, Export, Backup, Rücksetzen sowie Undo/Redo.
- JSON-, TXT- und CSV-Import bis 8 MB mit Dublettenprüfung.
- Eigener lokaler Speicherbereich: `multimodultool2026.provoware-genretool-pro.v1`.

## Einbindung

Das Modul ist im App-Manifest registriert:

```text
../modules/provoware-genretool-pro/module.manifest.json
```

Dateien:

- `module.manifest.json`: Modulbeschreibung und Sicherheitsgrenzen.
- `module.html`: gekapselte Oberfläche.
- `module.css`: gekapselte Gestaltung.
- `module.js`: Fachlogik und lokaler Zustand.
- `genres_db.json`: Startdatenbank.
- `preview.html`: direkte Modulvorschau über den lokalen Startserver.

## Vorschau

Projekt über `./scripts/start-local.sh` starten und danach öffnen:

```text
modules/provoware-genretool-pro/preview.html
```

Ein direkter Start über `file://` kann das Laden von `genres_db.json` blockieren.

## Prüfung

```sh
python3 tests/validate_module_manifests.py
python3 tests/validate_genres_module.py
node --check modules/provoware-genretool-pro/module.js
```

Die GenreTool-Prüfung kontrolliert Manifest, App-Registrierung, Einstiegspunkte, Pflichtoberfläche sowie exakt 1.800 normalisierte Unikate.

## Architekturgrenze

Die stabile Hauptanwendung ist weiterhin eine Single-File-HTML-App. Das Genres-Modul ist vollständig dateibasiert vorbereitet; die automatische Anzeige innerhalb der Hauptoberfläche erfolgt, sobald der geplante Manifest-Modul-Loader aktiv ist.
