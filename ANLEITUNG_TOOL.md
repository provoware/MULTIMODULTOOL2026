# ANLEITUNG_TOOL

## Unterstützte Systeme

Kubuntu 22.04/24.04, KDE Plasma, X11 oder Wayland, x86-64. Andere Systeme werden kontrolliert blockiert.

## Start

```bash
chmod +x start.sh setup.sh
./start.sh
```

Beim Start werden Linux, Python, PySide6, XDG-Pfade, Einstellungen, Ereignisjournal und privater Single-Instance-Laufzeitpfad geprüft.

## Sicherer Projektpapierkorb

Der spätere Nutzerworkflow muss immer diesen Ablauf verwenden:

1. Projektordner über einen Auswahldialog bestimmen.
2. Datei oder Ordner auswählen.
3. Rein lesende Vorschau erzeugen.
4. Projektgrenze, Mountstatus, Symlinks, Hardlinks, Konflikte, freien Speicher und Wiederherstellbarkeit prüfen.
5. Aktions-ID, Transaktions-ID, Originalpfad, Papierkorbziel und Manifest anzeigen.
6. Erst nach Bestätigung atomar in den Projektpapierkorb verschieben.
7. Ergebnis, Journalabschluss und Wiederherstellungsweg anzeigen.

```text
<Projekt>/.multimodultool2026/
├── history/actions.jsonl
└── trash/transactions/<MMTTRASH-ID>/
    ├── manifest.json
    └── payload
```

Die Anwendung kopiert nicht und löscht anschließend. Ein Mountwechsel wird blockiert.

## Undo

Undo darf ausschließlich die zuletzt aktive Aktion zurücknehmen:

1. Journal- und Hashkette prüfen.
2. `undo-intent` absturzsicher anhängen.
3. Papierkorbmanifest, Payload und freien Originalpfad prüfen.
4. Payload atomar zurückverschieben.
5. `undo` als Abschluss anhängen.

Mehrere Undo-Schritte laufen in umgekehrter Ausführungsreihenfolge. Ein erneut angefordertes Undo derselben bereits zurückgenommenen Aktion verändert nichts.

## Redo

Redo darf ausschließlich die nächste zurückgenommene Aktion wiederholen:

1. Originalquelle erneut prüfen.
2. neue Papierkorb-Transaktions-ID erzeugen,
3. `redo-intent` anhängen,
4. Quelle atomar in einen neuen Transaktionsordner verschieben,
5. `redo` anhängen.

Mehrere Redo-Schritte laufen in ursprünglicher Ausführungsreihenfolge. Die Aktions-ID bleibt stabil. Eine neue Aktion wird blockiert, solange eine Redo-Kette vorhanden ist.

## Unterbrochene Aktion

Bleibt durch einen Prozessabbruch ein Intent ohne Abschluss zurück, wird nichts blind wiederholt. Manifest, Payload und Originalpfad werden verglichen. Nur bei eindeutigem Zustand wird das fehlende Abschlussereignis ergänzt. Widersprüchliche Zustände werden blockiert.

## Rein lesende Transaktionsübersicht

Die Übersicht zeigt und filtert:

- `prepared`
- `trashed`
- `restored`
- `damaged`

Sie besitzt keine Schaltfläche zum Wiederherstellen, Reparieren, Löschen, Hochladen oder Exportieren. Beschädigte Zustände werden ausschließlich sichtbar markiert.

## Noch bewusst gesperrt

- grafische Projekt- und Dateiauswahl
- Massenaktionen
- Papierkorb leeren
- dauerhafte Löschung
- automatisches Verwerfen einer Redo-Kette
- lange Operationen ohne den noch folgenden Abbruch-/Wiederanlaufvertrag

## Zweiter Start und Diagnose

Ein zweiter normaler Start aktiviert die bestehende Instanz. Er darf nur `activate` oder `show-diagnostics` übertragen. Die Diagnosezentrale bleibt rein lesend.

```bash
python3 -m src.main --show-diagnostics
```

## Prüfungen für Entwickler

```bash
python3 tools/validate_repository.py
python3 -m unittest tests.test_project_trash -v
python3 -m unittest tests.test_undo_redo -v
python3 -m unittest tests.test_transaction_overview -v
python3 -m unittest tests.test_single_instance_stress -v
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_gui_trash_contract -v
```

## Fehlerfall

Keine Sperrdatei, kein Manifest, kein Payload und keine Journalzeile manuell löschen oder überschreiben. Diagnosekennung sichern, Ursache prüfen und erst nach grüner Vorprüfung fortfahren.
