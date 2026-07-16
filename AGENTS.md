# AGENTS.md – MULTIMODULTOOL2026

## 1. Projektrolle

Arbeite in diesem Repository als präziser Code-Architekt, Tool-Entwickler, GUI-Optimierer, Qualitätsprüfer und technischer Dokumentierer.

Ziel ist ein stabiles, schnelles, verständliches und lokal nutzbares Dashboard-Werkzeug. Kleine, sichere und gut begründete Änderungen sind wichtiger als große Umbauten.

## 2. Projektkontext

- Projektname: `MULTIMODULTOOL2026`
- Anwendungstyp: lokale Single-File-HTML-App mit geplanter Modulstruktur
- Aktueller Startpunkt: `dashboard-studio-ultimate-pro-v3.1.0.html`
- Aktueller Runtime-Ansatz: Browser direkt öffnen, kein Build-Schritt
- Langfristiges Ziel: manifestbasierte Module unter `modules/`
- Modulstandard: `standards/MULTIMODULTOOL2026_01_Modulstandard.md`
- App- und Modulmanifeste: `manifests/`
- Offene Aufgaben: `todo.txt`

## 3. Verbindliche Projektstruktur

```text
/
├── AGENTS.md
├── README.md
├── todo.txt
├── dashboard-studio-ultimate-pro-v3.1.0.html
├── assets/
├── backups/
├── data/
├── docs/
├── exports/
├── imports/
├── logs/
├── manifests/
├── modules/
├── standards/
├── tests/
└── trash/
```

### Ordnerzwecke

- `assets/`: Bilder, Icons, statische Gestaltungshilfen.
- `backups/`: Sicherheitskopien vor riskanten Änderungen oder Datenmigrationen.
- `data/`: lokale Beispieldaten, Seed-Daten oder geprüfte Testdaten ohne private Nutzerdaten.
- `docs/`: zusätzliche technische Dokumentation, Protokolle und spätere Bedienhinweise.
- `exports/`: erzeugte Exportbeispiele oder dokumentierte Exportformate.
- `imports/`: geprüfte Importbeispiele und kleine Testdateien.
- `logs/`: lokale Prüf- oder Laufprotokolle, sofern sie bewusst versioniert werden sollen.
- `manifests/`: App-Manifest, Modulmanifest-Schema und Beispielmanifeste.
- `modules/`: zukünftige ausgelagerte Dashboard-Module; jedes Modul bekommt einen eigenen Unterordner.
- `standards/`: verbindliche Standards für Module, Datenfluss und Erweiterungen.
- `tests/`: kleine, gezielte Tests für extrahierte Logik und Manifestprüfung.
- `trash/`: sicherer Ablageort für bewusst entfernte lokale Projektartefakte, wenn Löschung vermieden werden soll.

Leere Strukturordner dürfen mit `.gitkeep` versioniert werden. Keine privaten Daten, großen Binärdateien oder automatisch erzeugten Browserdaten committen.

## 4. Arbeitsablauf vor jeder Änderung

Vor jedem Patch zwingend prüfen und kurz festhalten:

1. Ziel der Änderung.
2. Betroffene Dateien.
3. Betroffene Zeilen oder Blöcke, soweit vorher sinnvoll ermittelbar.
4. Patchgrund.
5. Risiken.
6. Bewusste Nicht-Änderungen.
7. Konkrete Schrittliste.

Erst danach patchen. Nicht raten: vorhandene Dateien prüfen und bei Unsicherheit die kleinste sichere Änderung wählen.

### Effizienz- und Iterationsrahmen

- Entwicklungsarbeit erfolgt strikt planungsbasiert, patchbasiert, codesparsam und traffic-sparsam.
- Jede Iteration darf bis zum doppelten bisherigen fachlichen Umfang bearbeiten, wenn alle betroffenen Dateien und Risiken vorher klar eingegrenzt sind.
- Die Verdopplung des Iterationsumfangs bedeutet mehr zusammenhängende, begründete Teilaufgaben pro Iteration, nicht größere riskante Einzelpatches.
- Größere Iterationen bleiben in kleine, prüfbare Patches mit klarer Reihenfolge aufgeteilt.
- Datei- und Internetzugriffe auf das notwendige Minimum beschränken; bereits geprüfte unveränderte Bereiche nicht ohne neuen Anlass erneut analysieren.
- Bei Konflikt zwischen Geschwindigkeit und Sicherheit hat die kleinste sichere Änderung Vorrang.

## 5. Änderungsregeln

- Funktionierenden Code nicht unnötig verändern.
- Keine globalen Umformatierungen ohne direkten Nutzen.
- Keine Architekturwechsel ohne bestätigten Mehrwert.
- Keine neuen Abhängigkeiten ohne klare Begründung.
- Keine Platzhalter wie `TODO später`, `hier ergänzen` oder abgeschnittene Codebereiche.
- Keine destruktiven Dateiaktionen ohne Backup, Papierkorb oder klare Begründung.
- Dokumentation nur bei echter Struktur-, Verhaltens- oder Bedienänderung anpassen.
- Offene Folgeprobleme nicht ungeplant mitbearbeiten, sondern in `todo.txt` dokumentieren.
- Stabil laufende Bereiche weder kosmetisch anpassen noch erneut prüfen, wenn sie von der Änderung nicht betroffen sind.
- Fachbegriffe in Ausgaben möglichst vermeiden oder kurz in einfacher Sprache erklären.

## 6. Modulregeln

Für neue oder ausgelagerte Module gilt:

- Modulordner: `modules/<kleine-id-mit-bindestrichen>/`
- Pflichtdatei: `module.manifest.json`
- Optionale Dateien: `module.html`, `module.css`, `module.js`, `README.md`
- Manifest muss zum Schema in `manifests/MULTIMODULTOOL2026_01_ModuleManifest.schema.json` passen.
- Modulregeln aus `standards/MULTIMODULTOOL2026_01_Modulstandard.md` haben Vorrang für Moduldateien.
- Ein Modul erfüllt genau eine fachliche Aufgabe.
- Module speichern Daten nur in ihrem eigenen Datenbereich.
- Riskante Aktionen brauchen sichtbare Bestätigung und, wenn sinnvoll, ein Backup.

## 7. GUI- und UX-Regeln

Die Oberfläche muss laientauglich bleiben:

- klare visuelle Hierarchie
- gute Kontraste
- sichtbare Statusmeldungen
- verständliche Fehlermeldungen mit Lösungsvorschlag
- wichtige Funktionen ohne langes Suchen erreichbar
- keine überladene Oberfläche
- Tastaturbedienung berücksichtigen, wo sinnvoll
- lange Aufgaben nicht ohne Rückmeldung laufen lassen

Fehlertexte sollen immer beantworten:

1. Was ist passiert?
2. Warum ist es passiert?
3. Was kann der Nutzer tun?
4. Wurde gespeichert, abgebrochen oder nichts verändert?

## 8. Daten-, Backup- und Logging-Regeln

- Nutzereingaben validieren: leere Werte, Dateitypen, Dateigröße, Sonderzeichen, Pfade und doppelte Namen.
- Keine stillen Überschreibungen.
- Vor riskanten Importen, Migrationen oder Speicheränderungen Backup planen.
- Exporte mit nachvollziehbarem Namen und Zeitstempel bevorzugen.
- Browser-Speichergrenzen beachten und verständlich melden.
- Kritische Aktionen müssen nachvollziehbar sein.

Logformat, wenn Projektlogging betroffen ist:

```text
[YYYY-MM-DD HH:MM:SS] LEVEL: Bereich – Meldung | Ursache | Lösung
```

## 9. Größen- und Wartbarkeitsrichtwerte

- Hilfsdateien: möglichst bis 150 Zeilen.
- Normale Module: möglichst bis 300 Zeilen.
- Kernmodule: möglichst bis 500 Zeilen.
- Funktionen: möglichst bis 40 Zeilen; ab 60 Zeilen Teilung prüfen.
- Kleine, klar getrennte Dateien bevorzugen.
- Wiederholte Logik vermeiden.
- Performance nicht durch unnötige Dauerschleifen, Mehrfachberechnungen oder blockierende GUI-Aktionen verschlechtern.

## 10. Validierung

Nach allen Patches einer Iteration nur relevante Prüfungen ausführen:

- Strukturprüfung für neu angelegte oder verschobene Dateien.
- Syntaxprüfung für geänderte HTML-, JSON-, JS- oder Python-Dateien.
- Manifestprüfung, wenn Dateien unter `manifests/` oder `modules/` betroffen sind.
- Direkt betroffene Tests, falls vorhanden.
- Keine Volltests oder Wiederholungsprüfungen ohne Anlass.
- Validierung grundsätzlich erst am Ende aller Patches einer Iteration durchführen, außer ein Zwischentest verhindert klar erkennbaren Folgeschaden.

## 11. Qualitäts-Gates

Ein Arbeitsschritt ist erst abgeschlossen, wenn diese Punkte erfüllt sind:

1. Struktur verstanden und betroffene Dateien identifiziert.
2. Patch ist klein, begründet und nachvollziehbar.
3. Syntax und direkt betroffene Formate sind geprüft.
4. Datenverlust- und Überschreibungsrisiken sind berücksichtigt.
5. GUI bleibt bedienbar, falls GUI betroffen ist.
6. Test- oder Prüfstatus ist dokumentiert.
7. Offene Punkte sind benannt oder in `todo.txt` festgehalten.

## 12. Bewusste Nicht-Ziele ohne separaten Auftrag

- Keine komplette Zerlegung der bestehenden HTML-Datei.
- Keine Umbenennung des aktuellen Startpunkts.
- Kein Build-System einführen.
- Keine externen Frameworks hinzufügen.
- Keine optischen Massenänderungen.
- Keine erfundenen Dateien, Pfade oder Funktionen dokumentieren.

## 13. Abschlussbericht

Jede Iteration endet kompakt mit:

- Kurzfassung der Änderung.
- Geänderte und neue Dateien.
- Validierungsergebnis mit konkreten Befehlen.
- Bekannte Grenzen.
- Zwei konstruktive Empfehlungen für nächste Schritte.
- Bei erweitertem Iterationsumfang zusätzlich kurz nennen, welche Teilaufgaben bewusst gebündelt wurden und welche Grenzen eingehalten wurden.
