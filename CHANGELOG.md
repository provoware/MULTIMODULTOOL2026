# CHANGELOG

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
- Offscreen-Test für den sichtbaren Papierkorbvertrag

### Geändert

- Manifest auf Schema `1.3.0` erweitert.
- Repository- und CI-Vertrag prüfen Papierkorb, Stresstest und GUI-Vertrag ausdrücklich.
- Fortschritt auf 27 erledigt, 39 offen, 66 gesamt und 41 Prozent aktualisiert.

### Sicherheitswirkung

Kopieren mit anschließendem Löschen ist ausgeschlossen. Mountwechsel, Symlinks, Hardlinks, Speichermangel, Quelländerungen, Namenskonflikte, beschädigte Manifeste und veränderte Payloads blockieren die Transaktion, ohne Nutzdaten still zu überschreiben oder dauerhaft zu löschen.

## 2026-08-04 – P0-005

- sicherer Linux-Single-Instance-Koordinator über privaten Unix-Domain-Socket
- Linux-Peer-UID-Prüfung mit `SO_PEERCRED`
- sichere Erkennung veralteter und Blockade beschädigter Sperren
- rein lesende Diagnosezentrale mit Schweregrad- und Kennungsfilter
- Fortschritt: 25 erledigt, 40 offen, 65 gesamt, 38 Prozent
