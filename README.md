# MULTIMODULTOOL2026

**Projektstatus:** initiale, verbindliche Projekt- und UI-Grundlage

MULTIMODULTOOL2026 wird als laienoptimiertes, modulares Werkzeug mit klarer Navigation, transparenter Validierung, sicherer Datenverarbeitung und sichtbaren Statusmeldungen entwickelt.

## Visuelle Leitvorlage

![Visuelle Layout- und Orientierungsvorlage](assets/ui-reference/multimodultool2026-ui-layout-reference-2026.webp)

Die Abbildung ist die primäre grafische Orientierung für Aufbau und Anordnung der Oberfläche. Der im Bild sichtbare frühere Werkzeugname ist nur Bestandteil der ursprünglichen Vorlage; für dieses Repository gilt ausschließlich der Projektname `MULTIMODULTOOL2026`.

Verbindlich erhalten bleiben, solange der Nutzer keine ausdrückliche Abweichung verlangt:

- kompakter Kopfbereich mit Projektidentität und globalem Sicherheitsstatus
- linke Hauptnavigation
- obere Informations- und Statuskarten
- zentrale Reihe großer Funktionskacheln
- sichtbarer Prozess- oder Fortschrittsbereich
- großer mittlerer Arbeitsbereich
- rechte Kontext-, Hilfe- und Diagnoseleiste
- untere Aktions- und Statusleiste
- abschließender Sicherheits- und Systemstatus

Projektbezogen angepasst werden dürfen insbesondere Texte, Icons, Farben, Kachelinhalte, Modulanzahl, fachliche Funktionen und Statuswerte. Die grundlegende räumliche Logik bleibt erhalten.

Details:

- [`docs/UI_BASISVORLAGE.md`](docs/UI_BASISVORLAGE.md)
- [`standards/UI_LAYOUT_STANDARD_2026.md`](standards/UI_LAYOUT_STANDARD_2026.md)
- [`layout-manifest.json`](layout-manifest.json)

## Projektstruktur

```text
/
├── AGENTS.md
├── README.md
├── layout-manifest.json
├── assets/
│   └── ui-reference/
│       └── multimodultool2026-ui-layout-reference-2026.webp
├── backups/
├── data/
├── docs/
│   └── UI_BASISVORLAGE.md
├── exports/
├── logs/
├── modules/
├── src/
├── standards/
│   └── UI_LAYOUT_STANDARD_2026.md
├── tests/
├── tools/
└── trash/
```

Leere Arbeitsordner werden vorerst mit `.gitkeep` erhalten. Ihre fachliche Unterstruktur entsteht erst in geprüften Entwicklungsiterationen.

## Verbindlicher Iterationsablauf

Jede abgeschlossene Entwicklungsiteration wird auf `provoware/MULTIMODULTOOL2026` aktualisiert.

1. Ausgangsstand und Ziel prüfen.
2. Betroffene Dateien und Risiken festlegen.
3. Änderungen klein, nachvollziehbar und rückbaubar umsetzen.
4. Direkt betroffene Formate, Funktionen und Sicherheitsregeln validieren.
5. Den geprüften Stand auf GitHub committen.
6. Commit-SHA, Prüfergebnis, offene Punkte und nächsten technischen Schritt ausgeben.

Ein nur lokal vorliegender, angeblich abgeschlossener Arbeitsstand gilt nicht als abgeschlossene Iteration.

## Aktueller Umfang

Enthalten sind ausschließlich die Projektstruktur, die visuelle Referenz, die verbindliche Layoutregel und das maschinenlesbare Layout-Manifest. Anwendungslogik und produktive Module folgen in separaten, validierten Iterationen.
