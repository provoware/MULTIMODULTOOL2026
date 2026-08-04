# CHANGELOG

## 2026-08-04 – P0-005

### Hinzugefügt

- sicherer Linux-Single-Instance-Koordinator über privaten Unix-Domain-Socket
- Linux-Peer-UID-Prüfung mit `SO_PEERCRED`
- erlaubte Aktivierungsnachrichten ohne Dateipfade oder freie Argumente
- sichere Erkennung veralteter und Blockade beschädigter Sperren
- rein lesende Diagnosezentrale mit Schweregrad- und Kennungsfilter
- Kopierfunktion für einzelne bereinigte Berichte
- Unit- und Qt-Offscreen-Tests für Instanz- und Diagnosevertrag

### Geändert

- Oberfläche zeigt Instanzstatus, Diagnoseanzahl und Aktivierungsstatus.
- Fortschritt: 25 erledigt, 40 offen, 65 gesamt, 38 Prozent.
- CI und Pflichtdokumente wurden synchronisiert.

### Sicherheitswirkung

Zweitstarts erzeugen keine konkurrierende GUI. Unsichere Sperren werden nicht automatisch gelöscht. Die Diagnoseansicht verändert das Ereignisjournal nicht und besitzt keine Upload-, Lösch- oder Auto-Exportfunktion.
