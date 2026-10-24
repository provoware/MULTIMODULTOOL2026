# P3-004 – Reproduzierbarer synthetischer Dateibestand

## Zweck und Aufruf

Der Generator `tools/generate_test_data.py` stellt **ausschließlich künstliche**
Dateien für reproduzierbare Prüfungen von Dateibestandsanalyse, Duplikaten,
Namenskollisionen, Dateiendungen, leeren Dateien und Unicode bereit.

```bash
mkdir -p /tmp/mmt-fixtures
python3 tools/generate_test_data.py --output /tmp/mmt-fixtures/lauf-01
python3 -m unittest tests.test_generate_test_data -v
```

Der Zielordner muss **absolut und noch nicht vorhanden** sein. Der direkte
Elternordner muss bereits existieren und darf über keine symbolische
Verknüpfung erreichbar sein. Ziele im Quellbaum sind gesperrt.

## Sicherheits- und Reproduzierbarkeitsvertrag

- Keine Zufallswerte, persönlichen Daten, Systempfade oder Zeitstempel.
- Gleicher Generatorstand erzeugt byteidentische Dateien und `manifest.json`.
- Das Manifest enthält relative Pfade, Größen, SHA-256-Prüfsummen und
  explizite Erwartungen für Dubletten und gleiche Dateinamen.
- Neue Verzeichnisse haben `0700`, Dateien `0600`.
- Bestehende Ziele einschließlich defekter Symlinks werden nicht ersetzt.
- Kein Löschen, Überschreiben, Verschieben oder Ändern bestehender Nutzerdaten.
- Bei Schreibfehlern bleibt ein möglicherweise unvollständiger **neuer**
  Testordner stehen; `manifest.json` wird erst zuletzt angelegt.
- Die Dateien sind Testmaterial und **kein** Release- oder Nutzerdatenbestand.

## Grenzen

Die `.JPG`-Datei enthält absichtlich keine echte Bildkodierung; sie prüft
Dateiendungslogik, nicht Bilddekoder. Der Generator prüft weder riesige
Datenmengen noch gleichzeitige Änderungen durch andere Prozesse. Der
vollständige GUI-/Kubuntu-Test bleibt eine gesonderte Release-Pflicht.

**Prüfevidenz:** `tests/test_generate_test_data.py`; maßgeblich sind
ausschließlich die GitHub-Prüfläufe zum jeweiligen Entwicklungszweig.
