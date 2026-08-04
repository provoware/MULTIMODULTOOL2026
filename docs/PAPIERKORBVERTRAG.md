# Projektpapierkorbvertrag – MULTIMODULTOOL2026

## Ziel

Destruktive Dateiaktionen dürfen reguläre Dateien und Verzeichnisse standardmäßig nicht dauerhaft löschen. Sie werden ausschließlich nach vollständiger Vorschau atomar in einen projektbezogenen, wiederherstellbaren Papierkorb verschoben und im append-only Aktionsjournal dokumentiert.

## Verzeichnisstruktur

```text
<Projekt>/.multimodultool2026/
├── history/actions.jsonl
└── trash/transactions/<TRANSAKTIONS-ID>/
    ├── manifest.json
    └── payload
```

- interne Verzeichnisse: `0700`
- Manifest und Aktionsjournal: `0600`
- Transaktions-ID: `MMTTRASH-YYYYMMDDTHHMMSS-<12 HEX>`
- Aktions-ID: `MMTACTION-YYYYMMDDTHHMMSS-<12 HEX>`
- Manifest- und Journal-Schema: Version 1

## Vorprüfung

Vor jeder Transaktion werden geprüft:

1. absolute Projekt- und Quellpfade,
2. Quelle liegt innerhalb des Projekts und außerhalb des internen Papierkorbs,
3. Projekt und Quelle sind keine Symlinks und enthalten keine Symlink-Komponente,
4. Quelle ist reguläre Datei oder Verzeichnis,
5. reguläre Datei besitzt keinen zusätzlichen Hardlink,
6. Quelle ist kein Mountpunkt und liegt auf demselben Dateisystem wie das Projekt,
7. Quellordner ist atomar umbenennbar,
8. Aktions-ID, Transaktions-ID und Zielpfade sind unbelegt,
9. freier Speicher reicht mindestens für sichere Metadaten,
10. Quellfingerabdruck aus Gerät, Inode, Modus, Größe, Änderungszeit und Typ ist stabil.

Die Vorschau ist rein lesend und erzeugt weder Papierkorbordner, Manifest noch Journalzeile.

## Ausführung mit Journal

1. `prepare` mit Aktions- und Transaktions-ID absturzsicher anhängen,
2. private Papierkorb- und Transaktionsordner anlegen,
3. Manifest im Zustand `prepared` atomar schreiben und mit `fsync` bestätigen,
4. Quelle mit `os.replace` nach `payload` verschieben,
5. Quell- und Transaktionsverzeichnis mit `fsync` bestätigen,
6. Manifest atomar auf `trashed` setzen,
7. `apply` als Abschlussereignis anhängen.

Kopieren mit anschließendem Löschen ist ausdrücklich nicht Bestandteil dieses Vertrags. Ein Mountwechsel blockiert die Aktion.

## Wiederherstellung und Undo

Wiederherstellung erfolgt nur, wenn:

- Manifest vollständig, privat und schema-gültig ist,
- Transaktions-ID und Transaktionsordner übereinstimmen,
- Payload vorhanden, unverändert und auf demselben Dateisystem ist,
- ursprünglicher Elternordner sicher und beschreibbar ist,
- am Originalpfad kein Objekt existiert.

Undo hängt vor dem Restore ein `undo-intent` an und danach ein `undo`. Mehrere Undo-Schritte laufen ausschließlich in Rückwärtsreihenfolge. Ein `prepared`-Manifest mit vollständig vorhandenem Payload kann kontrolliert abgeglichen werden.

## Redo

Redo verwendet dieselbe Aktions-ID, aber eine neue Transaktions-ID. Dadurch bleibt das alte, bereits abgeschlossene Restore-Manifest unverändert. Redo läuft ausschließlich in ursprünglicher Vorwärtsreihenfolge.

## Fehlervertrag

Alle Blockaden verwenden `SafeOperationError` und damit den zentralen Sechs-Felder-Vertrag. Bei einem Fehler wird weder still überschrieben noch dauerhaft gelöscht. Beschädigte Manifeste, veränderte Payloads und Journalfehler bleiben zur Diagnose unverändert.

## Grenzen

- Die grafische Projekt- und Dateiauswahl bleibt bis zum geführten Projektworkflow gesperrt.
- Verzeichnisse werden als einzelnes Objekt atomar verschoben; eingebettete fremde Mounts werden derzeit nicht rekursiv analysiert.
- Projekte mit fremdem Eigentümer oder speziellen gemeinschaftlichen ACL-Modellen werden aktuell blockiert.
- Dauerhafte Papierkorbleerung ist nicht implementiert.
- Lange Operationen benötigen noch den Abbruch- und Wiederanlaufvertrag `P0-008`.

## Abnahme

- 17 Papierkorb-Regressionsfälle
- Vorschau verändert keine Datei
- Move und Restore sind atomar und wiederherstellbar
- zehn Aktionen werden rückwärts zurückgenommen und vorwärts erneut angewendet
- wiederholtes Undo/Redo erzeugt keine Doppeloperation
- Mount-, Symlink-, Hardlink-, Konflikt- und Speichermangelzustände blockieren
- beschädigtes Manifest, Journal oder Payload verändert keine Nutzdaten
- kein permanentes Löschen in API oder GUI-Vertrag
