# Provoware GenreTool Pro

## Status

Das Modul ist als separates MULTIMODULTOOL2026-Dateimodul umgesetzt. Es besteht aus Manifest, Oberfläche, Styles und lokaler Browser-Logik.

## Ziel

Das Modul verwaltet eine lokale, eindeutig bereinigte Datenbank für musikalische Begriffe. Es kombiniert Genres, Stimmungen, Stile, Effekte, Themen und Besonderheiten zufällig zu kopierbaren Song-Prompt-Ergebnissen.

## Funktionsumfang

- Datenbank mit bis zu 1.800 eindeutigen Einträgen.
- Einträge suchen, ergänzen, bearbeiten, löschen und favorisieren.
- Einträge nach Kategorien verwalten: Genre, Stimmung, Stil, Effekt, Thema und Besonderheit.
- Kategorien mischen und mehrere Zufallsergebnisse auf einmal erzeugen.
- Ergebnisse kommasepariert in die Zwischenablage kopieren.
- Zufallsergebnisse ohne Duplikate innerhalb eines Ergebnisses bilden.
- Einzelne Ergebnisbestandteile sperren, offen neu würfeln und einzeln kopieren.
- Ergebnisverlauf lokal protokollieren.
- Import, Export, Sicherung, Rücksetzen sowie Undo/Redo anbieten.
- Beim Import kommaseparierter Werte jeden Wert einzeln prüfen und einzeln ins Archiv aufnehmen.

## Dateien

- `module.manifest.json`: Modulbeschreibung und Sicherheitsgrenzen.
- `module.html`: lokale Moduloberfläche.
- `module.css`: gekapselte Modulgestaltung.
- `module.js`: lokale Logik mit eigenem Speicherbereich.

## Speicher und Sicherheit

Das Modul nutzt ausschließlich den eigenen lokalen Speicherbereich `multimodultool2026.provoware-genretool-pro.v1`. Doppelte Begriffe werden je Kategorie verhindert. Importdateien über 8 MB werden abgelehnt. Lösch- und Reset-Aktionen verlangen eine sichtbare Bestätigung und erstellen vorher einen Undo-Punkt.

## Bekannte Grenze

Das Modul ist dateibasiert vorbereitet. Die Hauptanwendung besitzt noch keinen dynamischen Modul-Loader, der `module.html`, `module.css` und `module.js` automatisch lädt.
