# CHANGELOG

## 2026-08-04 – P0-007

### Hinzugefügt

- `src/undo_redo.py` als privates append-only Aktionsjournal
- eindeutige `MMTACTION-`, `MMTTRASH-`- und `MMTEVENT-`-Kennungen
- lückenlose Ereignisse `prepare`, `apply`, `cancel`, `undo-intent`, `undo`, `redo-intent` und `redo`
- SHA-256-Hashkette mit Sequenz-, Doppelungs- und Zustandsprüfung
- absturzsicheres Anhängen mit `O_APPEND`, `O_NOFOLLOW`, `flock` und `fsync`
- idempotentes, konfliktgeprüftes Undo in Rückwärtsreihenfolge
- idempotentes, konfliktgeprüftes Redo in Vorwärtsreihenfolge
- kontrollierter Intent-Abgleich nach unterbrochenem Apply oder Undo
- `src/transaction_overview.py` als rein lesende Übersicht für `prepared`, `trashed`, `restored` und `damaged`
- Qt-Filter und Detailansicht ohne Restore-, Reparatur-, Lösch-, Upload- oder Exportfunktion
- zehnstufiger Aktions-Rundlauf mit zehn Undo- und zehn Redo-Schritten

### Geändert

- Manifest auf Schema `1.4.0` erweitert und Laufzeitvalidator synchronisiert.
- Papierkorbansicht um Undo-/Redo-Vertrag und Transaktionsübersicht ergänzt.
- Repository- und CI-Vertrag prüfen Journal, Reihenfolge, Recovery und read-only Ansicht ausdrücklich.
- Fortschritt auf 29 erledigt, 38 offen, 67 gesamt und 43 Prozent aktualisiert.

### Sicherheitswirkung

Vorhandene Journalzeilen werden niemals verändert. Absolute Pfade sind verboten. Hashfehler, falsche Reihenfolge, widersprüchliche Manifestzustände oder eine unklare Redo-Kette blockieren weitere Aktionen ohne stilles Überschreiben oder Löschen.

## 2026-08-04 – P0-006

### Hinzugefügt

- `src/project_trash.py` als projektbezogene Papierkorb-Transaktionsschicht
- read-only Vorschau mit Quellfingerabdruck und eindeutiger `MMTTRASH-`-ID
- private Transaktionsverzeichnisse `0700` und Manifestdateien `0600`
- atomare Verschiebung und Wiederherstellung über `os.replace`
- Manifestzustände `prepared`, `trashed` und `restored`
- kontrollierte Wiederherstellung eines vollständigen Prepared-Zustands
- read-only Qt-Vertragspanel ohne Lösch- oder Leerungsfunktion
- 17 Papierkorb-Regressionsfälle
- Parallelstart-Stresstest mit 20 nahezu gleichzeitigen Zweitstarts

### Sicherheitswirkung

Kopieren mit anschließendem Löschen ist ausgeschlossen. Mountwechsel, Symlinks, Hardlinks, Speichermangel, Quelländerungen, Namenskonflikte, beschädigte Manifeste und veränderte Payloads blockieren die Transaktion.

## 2026-08-04 – P0-005

- sicherer Linux-Single-Instance-Koordinator über privaten Unix-Domain-Socket
- Linux-Peer-UID-Prüfung mit `SO_PEERCRED`
- sichere Erkennung veralteter und Blockade beschädigter Sperren
- rein lesende Diagnosezentrale mit Schweregrad- und Kennungsfilter
