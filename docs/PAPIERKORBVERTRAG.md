# Projektpapierkorbvertrag – MULTIMODULTOOL2026

## Ziel

Reguläre Dateien und Verzeichnisse werden nicht dauerhaft gelöscht. Nach vollständiger Vorschau werden sie ausschließlich per `os.replace` innerhalb desselben Dateisystems in einen projektbezogenen Papierkorb verschoben.

## Struktur

```text
<Projekt>/.multimodultool2026/trash/transactions/<MMTTRASH-ID>/
├── manifest.json
└── payload
```

- Verzeichnisse: `0700`
- Manifest: `0600`
- Manifest-Schema: Version 1

## Vorprüfung

Geprüft werden Projektgrenze, Quelltyp, Symlink-Komponenten, Hardlinks, Mount- und Dateisystemgrenze, Schreibrechte, freier Speicher, unbelegte ID, stabiler Quellfingerabdruck und Wiederherstellbarkeit. Die Vorschau verändert nichts.

## Ausführung

1. Manifest `prepared` atomar schreiben und mit `fsync` bestätigen.
2. Quelle mit `os.replace` nach `payload` verschieben.
3. Quell- und Transaktionsverzeichnis mit `fsync` bestätigen.
4. Manifest atomar auf `trashed` setzen.
5. append-only Journalabschluss bestätigen.
6. bei langen Abläufen Laufcheckpoint auf den nächsten Schritt setzen.

Copy-delete-Fallback und dauerhafte Löschung sind verboten.

## Wiederherstellung

Restore benötigt gültiges privates Manifest, unveränderten Payload, dasselbe Dateisystem, sicheren Elternordner und freien Originalpfad. Auch Restore verwendet `os.replace`.

## Prozessende während einer Verschiebung

- Vor Dateioperation: derselbe Intent und dieselbe Transaktions-ID werden fortgesetzt.
- Nach Dateioperation, vor `fsync`: Verzeichnisse werden erneut synchronisiert.
- Nach `fsync`, vor Manifestabschluss: nur Manifest wird abgeschlossen.
- Nach Manifest, vor Journal: nur `apply` wird angehängt.
- Nach Journal, vor Laufcheckpoint: nur Checkpoint wird fortgeschrieben.

Eine bereits ausgeführte Verschiebung wird nicht wiederholt.

## Fehlervertrag

Alle Blockaden verwenden `SafeOperationError` mit Ursache, Folge, Datenstand, Lösung, Diagnosekennung und sicherem nächsten Schritt. Beschädigte Manifeste, veränderte Payloads und Konflikte bleiben unverändert.

## Grenzen

- eingebettete fremde Mounts werden noch nicht rekursiv analysiert,
- gemeinschaftliche ACL-Projekte werden restriktiv behandelt,
- dauerhafte Papierkorbleerung fehlt,
- produktive grafische Projekt- und Dateiauswahl bleibt gesperrt.
