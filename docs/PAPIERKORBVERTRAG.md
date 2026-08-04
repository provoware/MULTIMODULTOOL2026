# Projektpapierkorbvertrag – MULTIMODULTOOL2026

## Ziel

Destruktive Dateiaktionen dürfen reguläre Dateien und Verzeichnisse standardmäßig nicht dauerhaft löschen. Sie werden ausschließlich nach vollständiger Vorschau atomar in einen projektbezogenen, wiederherstellbaren Papierkorb verschoben.

## Verzeichnisstruktur

```text
<Projekt>/.multimodultool2026/trash/transactions/<TRANSAKTIONS-ID>/
├── manifest.json
└── payload
```

- interne Verzeichnisse: `0700`
- Manifest: `0600`
- Transaktions-ID: `MMTTRASH-YYYYMMDDTHHMMSS-<12 HEX>`
- Manifest-Schema: Version 1

## Vorprüfung

Vor jeder Transaktion werden geprüft:

1. absolute Projekt- und Quellpfade,
2. Quelle liegt innerhalb des Projekts und außerhalb des internen Papierkorbs,
3. Projekt und Quelle sind keine Symlinks und enthalten keine Symlink-Komponente,
4. Quelle ist reguläre Datei oder Verzeichnis,
5. reguläre Datei besitzt keinen zusätzlichen Hardlink,
6. Quelle ist kein Mountpunkt und liegt auf demselben Dateisystem wie das Projekt,
7. Quellordner ist atomar umbenennbar,
8. Transaktions-ID und Zielpfade sind unbelegt,
9. freier Speicher reicht mindestens für sichere Metadaten,
10. Quellfingerabdruck aus Gerät, Inode, Modus, Größe, Änderungszeit und Typ ist stabil.

Die Vorschau ist rein lesend und erzeugt weder Papierkorbordner noch Manifest.

## Ausführung

1. private Papierkorb- und Transaktionsordner anlegen,
2. Manifest im Zustand `prepared` atomar schreiben und mit `fsync` bestätigen,
3. Quelle mit `os.replace` nach `payload` verschieben,
4. Quell- und Transaktionsverzeichnis mit `fsync` bestätigen,
5. Manifest atomar auf `trashed` setzen.

Kopieren mit anschließendem Löschen ist ausdrücklich nicht Bestandteil dieses Vertrags. Ein Mountwechsel blockiert die Aktion.

## Wiederherstellung

Wiederherstellung erfolgt nur, wenn:

- Manifest vollständig, privat und schema-gültig ist,
- Transaktions-ID und Transaktionsordner übereinstimmen,
- Payload vorhanden, unverändert und auf demselben Dateisystem ist,
- ursprünglicher Elternordner sicher und beschreibbar ist,
- am Originalpfad kein Objekt existiert.

Die Wiederherstellung verwendet ebenfalls `os.replace`. Ein `prepared`-Manifest mit vollständig vorhandenem Payload kann nach einer Unterbrechung kontrolliert wiederhergestellt werden.

## Fehlervertrag

Alle Blockaden verwenden `SafeOperationError` und damit den zentralen Sechs-Felder-Vertrag:

- Ursache
- Folge
- unveränderter Datenstand
- Lösung
- Diagnosekennung
- sicherer nächster Schritt

Bei einem Fehler wird weder still überschrieben noch dauerhaft gelöscht. Beschädigte Manifeste und veränderte Payloads bleiben zur Diagnose unverändert.

## Grenzen

- Die grafische Projekt- und Dateiauswahl bleibt bis zum geführten Projektworkflow gesperrt.
- Verzeichnisse werden als einzelnes Objekt atomar verschoben; eingebettete fremde Mounts werden derzeit nicht rekursiv analysiert.
- Projekte mit fremdem Eigentümer oder speziellen gemeinschaftlichen ACL-Modellen werden aktuell blockiert.
- Dauerhafte Papierkorbleerung ist nicht implementiert.
- Undo/Redo über mehrere Transaktionen folgt mit `P0-007`.

## Abnahme

- 17 Papierkorb-Regressionsfälle
- Vorschau verändert keine Datei
- Move und Restore sind atomar und wiederherstellbar
- Mount-, Symlink-, Hardlink-, Konflikt- und Speichermangelzustände blockieren
- beschädigtes Manifest oder veränderter Payload verändert keine Nutzdaten
- kein permanentes Löschen in API oder GUI-Vertrag
