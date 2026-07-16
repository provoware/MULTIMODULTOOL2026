# Schnell-Text-Speicher

Dieses Modul sammelt kurze, wiederverwendbare Textbausteine. Die Bausteine sind bewusst knapp formuliert, damit sie schnell kopiert, angepasst und in eigenen Arbeitsabläufen genutzt werden können.

## Ausgelagerte Textstruktur

Die eigentlichen Textbausteine liegen jetzt in `data/schnell-text-speicher-bausteine.json`. Dadurch bleibt diese README kurz, während die Inhalte als klare Datenstruktur geprüft und später leichter in das Modul geladen werden können.

Die Datei nutzt diese einfache Struktur:

- `moduleId`: Zuordnung zum Modulordner.
- `version`: Version der Bausteinsammlung.
- `description`: kurzer Zweck der Sammlung.
- `categories`: Liste der Kategorien mit `id`, `name` und `snippets`.

## Pflege-Regeln

- Jeder Baustein steht in genau einer Kategorie.
- Exakte Dubletten sind nicht erlaubt.
- Bausteine bleiben kurz, konkret und ohne private Daten.
- Neue Kategorien bekommen eine kleine ID mit Bindestrichen.
- Nach Änderungen an der JSON-Datei wird `python3 tests/validate_quicktext_snippets.py` ausgeführt.

## Aktuelle Kategorien

- Coding
- Prompting
- Vibecoding
- KI-Bildgenerierung
- KI-Musikgenerierung
- KI-Contentcreation
