# CHANGELOG

## 2026-08-04 – P0-008

### Hinzugefügt

- `src/run_control.py` als projektbezogene transaktionale Laufsteuerung
- eindeutige `MMTRUN-`-Lauf-IDs
- unveränderliche, SHA-256-geprüfte Laufpläne
- atomar ersetzte und nachvalidierte Checkpoints
- private Laufordner `0700` und Laufdateien `0600`
- exklusive Linux-`flock`-Sperre je Lauf
- separate, atomare `cancel.request` ohne konkurrierenden Checkpointschreiber
- kontrollierte Abbruchpunkte vor Intent und nach vollständig bestätigtem Schritt
- idempotenter Wiederanlauf aus Checkpoint, Aktionsjournal, Manifest, Originalpfad und Payload
- Recovery für fehlenden Manifest- oder Journalabschluss ohne Wiederholung der Dateioperation
- echte zehnstufige `SIGKILL`-Prozessabbruchmatrix
- read-only Wiederanlaufvertrag in der bestehenden Papierkorb-/Transaktionsoberfläche

### Geändert

- Neun-Zonen-Oberfläche auf Checkpoint- und Wiederanlaufstatus fokussiert.
- Maschinenlesbares Manifest um `runControlPolicy` erweitert; Schema bleibt kompatibel bei `1.4.0`.
- Repository- und CI-Vertrag prüfen Laufsteuerung und Prozessabbruchmatrix ausdrücklich.
- Fortschritt auf 31 erledigt, 37 offen, 68 gesamt und 46 Prozent aktualisiert.

### Sicherheitswirkung

Abbruch und Prozessende können keine bereits ausgeführte Dateioperation erneut starten. Ein Neustart ergänzt ausschließlich nachweislich fehlende Abschlüsse oder setzt am gespeicherten sicheren Schritt fort. Widersprüchliche Zustände bleiben unverändert blockiert.

## 2026-08-04 – P0-007

- append-only Undo-/Redo-Journal mit SHA-256-Hashkette
- zehnfacher Undo-/Redo-Rundlauf
- rein lesende Transaktionsübersicht
- Fortschritt: 29 erledigt, 38 offen, 67 gesamt, 43 Prozent
