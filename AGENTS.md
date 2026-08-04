# AGENTS.md – MULTIMODULTOOL2026

## Projektauftrag

Dieses Repository wird als modulares, laienoptimiertes, transparentes und datensicheres Werkzeug entwickelt. Änderungen müssen verständlich, prüfbar, rückbaubar und mit dem aktuellen GitHub-Stand synchronisiert sein.

## Verbindliche UI-Basis

Die Datei `assets/ui-reference/multimodultool2026-ui-layout-reference-2026.webp` ist die primäre visuelle Orientierung.

Verbindliche Regeln:

1. Grundaufbau und räumliche Anordnung bleiben erhalten.
2. Projektbezogene Inhalte, Bezeichnungen, Icons, Farben und Funktionen dürfen angepasst werden.
3. Größere Abweichungen an Navigation, Zonenfolge oder Hauptanordnung erfolgen nur nach ausdrücklichem Nutzerwunsch.
4. Jede UI-Iteration wird gegen `standards/UI_LAYOUT_STANDARD_2026.md` und `layout-manifest.json` geprüft.
5. Der im Referenzbild sichtbare alte Werkzeugname ist nicht zu übernehmen; verwendet wird `MULTIMODULTOOL2026`.

## Arbeitsweise je Iteration

Vor der Änderung:

- Ziel, Nutzen und Nutzerwirkung festlegen
- betroffene Dateien und Bereiche bestimmen
- Datenverlust-, Bedien- und Rückfallrisiken prüfen
- kleinsten sinnvollen, vollständigen Patch planen

Nach der Änderung:

- Syntax und direkt betroffene Formate prüfen
- Layouttreue und Bedienbarkeit prüfen
- riskante Aktionen, Fehlertexte und Rückfallwege prüfen
- offene Punkte dokumentieren
- geprüften Stand auf GitHub aktualisieren

## GitHub-Pflicht

Jede vollständig abgeschlossene Iteration muss auf `provoware/MULTIMODULTOOL2026` übertragen werden.

Eine Iteration ist erst abgeschlossen, wenn:

- der vorgesehene Patch enthalten ist,
- die relevante Validierung durchgeführt wurde,
- der Zielbranch erfolgreich aktualisiert wurde,
- der neue Commit-SHA bestätigt wurde,
- Prüfergebnis und offene Punkte transparent ausgegeben wurden.

Keine Abschlussbehauptung bei fehlgeschlagenem Push, unklarem Branchzustand oder ungeprüften Änderungen.

## Daten- und Bedienungssicherheit

- keine stillen Löschungen oder Überschreibungen
- riskante Aktionen mit Bestätigung, Vorschau und nachvollziehbarer Wirkung
- Undo, Papierkorb oder Backup vor destruktiven Eingriffen vorsehen
- Fehler in einfacher Sprache mit Ursache, Folge und Lösung erklären
- manuelle Eingaben vermeiden, wenn sichere Auswahlfelder, Schalter oder Dialoge möglich sind
- Status, Fortschritt und Ergebnis sichtbar halten

## Iterationsabschluss

Jeder Entwicklungsabschluss nennt mindestens:

- Commit-SHA und Zielbranch
- ausgeführte Prüfungen
- Entwicklungsfortschritt in Prozent
- Anzahl erledigter und offener Punkte
- direkt folgenden technischen Entwicklungsschritt
- alternative Verbesserung mit hohem Nutzen und geringem Risiko
