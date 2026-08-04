# UI_BASISVORLAGE

## Zweck

Diese Datei beschreibt die grafische und räumliche Basis für `MULTIMODULTOOL2026`.

**Referenzdatei:**

`assets/ui-reference/multimodultool2026-ui-layout-reference-2026.webp`

Die Referenz wurde für die Repository-Nutzung platzsparend als WebP-Derivat abgelegt. Aufbau, Proportionen und visuelle Orientierung bleiben erkennbar. Der im Bild enthaltene frühere Werkzeugname ist nicht verbindlich.

## Verbindliche Grundanordnung

Die Oberfläche folgt grundsätzlich dieser Reihenfolge:

1. **Kopfbereich** – Projektname, globaler Sicherheitsstatus und Fensteraktionen.
2. **Linke Hauptnavigation** – dauerhaft erkennbare Hauptbereiche und Systemfunktionen.
3. **Obere Übersichtskarten** – Quellen, Bestand, Prüfstatus und zentrale Kennzahlen.
4. **Primäre Funktionskacheln** – große, schnell erkennbare Einstiege in die Hauptaufgaben.
5. **Prozessanzeige** – nachvollziehbare Schritte, Fortschritt und aktueller Zustand.
6. **Mittlerer Arbeitsbereich** – Auswahl, Vorschau, Regeln, Ergebnisse und sichere Aktionen.
7. **Rechte Kontextleiste** – Hilfe, Hinweise, Diagnose, Detailstatus und Vorschauinformationen.
8. **Untere Aktionsleiste** – Validierung, Rückfall, Hauptaktion und sekundäre Aktion.
9. **Abschlussstatus** – Datenschutz, Sperrstatus, Speicherzustand und Gesamtergebnis.

Die Anordnung bleibt Standard, solange der Nutzer keine ausdrückliche Änderung verlangt.

## Projektbezogene Anpassungen

Ohne zusätzliche Freigabe dürfen angepasst werden:

- Projektname und Modulbezeichnungen
- Icons und verständliche Beschriftungen
- fachliche Inhalte der Kacheln
- Anzahl der Detailfelder innerhalb einer Zone
- Farbthemen und Akzentfarben bei ausreichendem Kontrast
- Statuswerte, Diagramme und Hilfetexte
- responsive Größen und kontrollierte Umbrüche
- interne Komponenten, solange die Zonenlogik erhalten bleibt

## Änderungen mit Freigabepflicht

Eine ausdrückliche Nutzerfreigabe ist erforderlich bei:

- Entfernen einer Hauptzone
- Wechsel von linker Navigation zu ausschließlich oberer Navigation
- Verschieben der Kontextleiste auf eine andere Grundposition
- Auflösen der zentralen Funktionskachel-Reihe
- dauerhafter Verbergung von Sicherheits- oder Statusinformationen
- grundlegender Umkehr der Informationshierarchie
- vollständigem Wechsel zu einem anders aufgebauten Layoutsystem

## Bedien- und Sicherheitsprinzipien

- Der Nutzer muss ohne Fachkenntnis erkennen, was als Nächstes zu tun ist.
- Auswahlfelder, Kacheln, Schalter und Dialoge haben Vorrang vor fehleranfälligen Freitexteingaben.
- Vor riskanten Aktionen erscheinen Wirkung, Ziel, Umfang und Rückfallmöglichkeit.
- Nach jeder Aktion werden Ergebnis, betroffene Elemente und nächster Schritt angezeigt.
- Löschen, Verschieben, Massenumbenennen und Reparieren benötigen Vorschau und kontrollierte Bestätigung.
- Fehlertexte erklären: Was ist passiert? Was blieb unverändert? Wie wird fortgefahren?
- Statusfarben werden nie als einzige Informationsquelle verwendet.

## Prüfliste je UI-Iteration

- [ ] Grundzonen vorhanden und in der vorgesehenen Reihenfolge
- [ ] Projektname lautet `MULTIMODULTOOL2026`
- [ ] Hauptfunktion ohne Fachkenntnis auffindbar
- [ ] keine wichtigen Bedienelemente abgeschnitten oder verdeckt
- [ ] Status und Fortschritt sichtbar
- [ ] Kontraste und Fokuszustände erkennbar
- [ ] riskante Aktion mit Vorschau und Rückfallweg
- [ ] rechte Kontextleiste liefert nutzbare Hilfe oder Diagnose
- [ ] Layout-Manifest weiterhin konsistent
- [ ] geprüfter Stand auf GitHub aktualisiert

## Abweichungsprotokoll

Eine genehmigte größere Abweichung wird in der betreffenden Iteration dokumentiert mit:

- Nutzerwunsch
- betroffener Zone
- Grund der Änderung
- erwarteter Bedienvorteil
- Risiko und Rückfallweg
- aktualisiertem `layout-manifest.json`
- Commit-SHA der Umsetzung
