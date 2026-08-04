# UI_LAYOUT_STANDARD_2026

## 1. Geltungsbereich

Dieser Standard gilt für alle Hauptansichten, Module und produktiven UI-Iterationen von `MULTIMODULTOOL2026`.

Referenzen:

- `assets/ui-reference/multimodultool2026-ui-layout-reference-2026.webp`
- `docs/UI_BASISVORLAGE.md`
- `layout-manifest.json`

Bei Widersprüchen gilt folgende Reihenfolge:

1. ausdrücklicher aktueller Nutzerwunsch
2. dieser Standard
3. Layout-Manifest
4. grafische Referenz

## 2. Unveränderliche Layoutprinzipien

Ohne ausdrücklichen Nutzerwunsch bleiben erhalten:

- vertikale Hauptnavigation links
- globale Identität und Sicherheitsstatus im Kopfbereich
- Kennzahlen- und Informationskarten oberhalb der Hauptfunktionen
- große Hauptfunktionskacheln als schneller Einstieg
- sichtbare Prozess- oder Fortschrittsdarstellung
- zentraler Arbeitsbereich als größte Zone
- Kontext-, Hilfe- und Diagnosebereich rechts
- Aktions- und Statusbereich am unteren Rand
- klare visuelle Trennung zwischen Navigation, Arbeit, Kontext und Status

## 3. Zonenvertrag

### Z01 – App-Kopfbereich

Enthält Projektname, globalen Zustand und übergeordnete Aktionen. Kritische Warnungen dürfen hier nicht durch Dekoration überdeckt werden.

### Z02 – Linke Hauptnavigation

Enthält die Hauptbereiche in stabiler Reihenfolge. Aktiver Bereich, Fokus und deaktivierte Einträge müssen eindeutig erkennbar sein.

### Z03 – Übersichtskarten

Zeigt Quellen, Bestand, Kapazität, Prüfung oder andere zentrale Kennzahlen. Karten enthalten klare Bezeichnung, Wert und Zustand.

### Z04 – Hauptfunktionskacheln

Bietet direkten Zugriff auf die wichtigsten Arbeitsabläufe. Kacheln verwenden Icon, kurze Bezeichnung und verständlichen Status.

### Z05 – Prozessanzeige

Zeigt Schrittfolge, aktuellen Schritt, abgeschlossene Schritte und Blockaden. Fortschritt darf nicht ausschließlich über Farbe vermittelt werden.

### Z06 – Hauptarbeitsbereich

Ist die größte Nutzfläche. Auswahl, Einstellungen, Vorschau und Ergebnis werden logisch gruppiert. Destruktive Aktionen stehen nicht direkt neben harmlosen Aktionen ohne deutliche Abgrenzung.

### Z07 – Rechte Kontextleiste

Zeigt Hilfe, Details, Diagnose, Hinweise oder Vorschauinformationen passend zum aktuellen Arbeitsschritt.

### Z08 – Untere Aktionsleiste

Enthält Validierungszustand, Rückfallfunktion, primäre Aktion und sekundäre Aktion. Die primäre Aktion wird erst aktiv, wenn erforderliche Vorprüfungen bestanden sind.

### Z09 – Abschlussstatus

Zeigt Datenschutz-, Speicher-, Sperr- und Gesamtergebnis. Der Nutzer erkennt, ob Daten verändert wurden und ob ein Rückfall möglich ist.

## 4. Responsive Verhalten

Die Zonenlogik bleibt auf kleineren Bildschirmen erhalten.

- Desktop: linke Navigation, Zentrum und rechte Kontextleiste gleichzeitig sichtbar, soweit die Mindestbreite dies zulässt.
- Tablet: rechte Kontextleiste darf als einblendbares Panel erscheinen; ihr Inhalt bleibt erreichbar.
- Mobil: Zonen werden in der festgelegten Informationsreihenfolge gestapelt. Navigation kann als kontrolliertes Menü erscheinen.
- Kein wichtiges Element darf unter einem Rand verschwinden.
- Vergrößerung der Schrift oder Browserzoom darf keine unzugänglichen Hauptaktionen erzeugen.
- Horizontales Scrollen für Kernfunktionen ist zu vermeiden.

## 5. Interaktionsstandard

- Hauptabläufe werden über Kacheln, Schalter, Auswahlfelder und geführte Dialoge angeboten.
- Freitext wird nur eingesetzt, wenn keine sichere Auswahl möglich ist.
- Jede riskante Aktion besitzt Vorprüfung, Vorschau, Bestätigung und Nachprüfung.
- Abbruch, Undo, Papierkorb oder Backup werden abhängig vom Risiko vorgesehen.
- Lange Vorgänge zeigen Fortschritt, aktuellen Teilschritt und Abbruchwirkung.
- Deaktivierte Aktionen erklären den Grund und den nächsten möglichen Schritt.

## 6. Visueller Standard

- dunkle Grundfläche mit klar abgegrenzten Karten und Panels ist die Ausgangsrichtung
- Neon-Akzente dürfen Funktionsgruppen markieren, aber keine Information ersetzen
- Textkontrast muss lesbar bleiben; helle Schrift auf hellem Feld ist unzulässig
- Fokusrahmen und aktive Zustände müssen deutlich erkennbar sein
- Warnung, Fehler, Erfolg und Information verwenden zusätzlich Icon und Text
- Dekoration darf weder Inhalt noch Klickflächen überlagern

## 7. Validierungs-Gates

Eine UI-Iteration gilt nur dann als bestanden, wenn:

1. alle erforderlichen Zonen vorhanden oder genehmigt abweichend dokumentiert sind,
2. Reihenfolge und Hauptproportionen der Basis entsprechen,
3. keine Kernaktion abgeschnitten, verdeckt oder unerreichbar ist,
4. Tastaturfokus und aktive Zustände erkennbar sind,
5. Statusmeldungen Ursache, Wirkung und nächsten Schritt nennen,
6. riskante Aktionen vor und nach der Ausführung geprüft werden,
7. `layout-manifest.json` syntaktisch gültig und fachlich konsistent ist,
8. der geprüfte Stand auf GitHub übertragen und per Commit-SHA bestätigt wurde.

## 8. Änderungsverfahren

Kleine projektbezogene Anpassungen werden direkt umgesetzt und validiert. Größere strukturelle Änderungen benötigen vorher:

- eindeutigen Nutzerwunsch
- dokumentierte betroffene Zonen
- Vorher-Nachher-Begründung
- Bedien- und Sicherheitsbewertung
- Rückfallplan
- Aktualisierung von Standard, Manifest und Referenzhinweis, soweit betroffen
