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

Der Papierkorb-Kern ist entwickelt und automatisiert geprüft. Die spätere Nutzeroberfläche muss immer denselben Ablauf verwenden:

1. Projektordner über einen Auswahldialog bestimmen.
2. Datei oder Ordner auswählen.
3. **Vorschau** erzeugen – dabei wird noch nichts angelegt oder verschoben.
4. Pfadgrenze, Mountstatus, Symlinks, Hardlinks, Konflikte, freien Speicher und Wiederherstellbarkeit prüfen.
5. Transaktions-ID, Originalpfad, Papierkorbziel und Manifest anzeigen.
6. Erst nach Bestätigung atomar in den Projektpapierkorb verschieben.
7. Ergebnis und Wiederherstellungsweg anzeigen.

Interner Speicherort:

```text
<Projekt>/.multimodultool2026/trash/transactions/<MMTTRASH-ID>/
├── manifest.json
└── payload
```

Die Anwendung kopiert nicht und löscht anschließend. Sie verwendet nur eine atomare Umbenennung innerhalb desselben Dateisystems. Ein Mountwechsel wird blockiert.

## Wiederherstellung

Eine Transaktion kann nur wiederhergestellt werden, wenn:

- das Manifest gültig und privat ist,
- der Payload seit dem Verschieben unverändert blieb,
- der ursprüngliche Elternordner sicher erreichbar ist,
- am Originalpfad kein neues Objekt liegt.

Bei einem Namenskonflikt wird nichts überschrieben. Beschädigte Manifeste und unklare Zustände bleiben unverändert und werden mit Diagnosekennung erklärt.

## Noch bewusst gesperrt

- grafische Projekt- und Dateiauswahl
- Massenaktionen
- Papierkorb leeren
- dauerhafte Löschung
- Undo/Redo über mehrere Aktionen

Diese Sperren verhindern, dass die geprüfte Kern-API vor dem geführten Projektworkflow unkontrolliert benutzt wird.

## Zweiter Start und Diagnose

Ein zweiter normaler Start aktiviert die bestehende Instanz. Er darf nur `activate` oder `show-diagnostics` übertragen. Die Diagnosezentrale bleibt rein lesend.

```bash
python3 -m src.main --show-diagnostics
```

## Prüfungen für Entwickler

```bash
python3 tools/validate_repository.py
python3 -m unittest tests.test_project_trash -v
python3 -m unittest tests.test_single_instance_stress -v
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_gui_trash_contract -v
```

## Fehlerfall

Keine Sperrdatei, kein Manifest und kein Payload darf manuell gelöscht oder überschrieben werden. Diagnosekennung sichern, Ursache prüfen und erst nach grüner Vorprüfung fortfahren.
