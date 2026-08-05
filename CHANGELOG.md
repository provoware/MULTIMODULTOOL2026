# CHANGELOG

## 2026-08-05 – Releasefinalisierung, Bereinigung und P2-004

### Hinzugefügt

- `release/release-status.json` als verbindliche Trennung zwischen fertigen Releaseausgaben, Testartefakten und offenen Produktbereichen
- atomarer Finalizer `tools/finalize_release_artifacts.py`
- sechs eindeutig gekennzeichnete `_save_`-Releaseausgaben nach vollständig grüner Kubuntu-Matrix
- Regressionen für Hashbindung, Symlinkblockade, Dateirechte und rückstandsfreien Austausch des generierten Zielordners
- funktionaler, rein lesender Hilfe-Dialog mit Sicherheitsgrenzen und sicheren nächsten Schritten
- konkrete Tooltips, Statushinweise, `What’s This`-Texte und zugängliche Beschreibungen für gesperrte Aktionen
- Workflowartefakte für Rohprotokoll, letzte Phase sowie inneren und äußeren Exit-Code jedes Kubuntu-Laufs

### Geändert

- Kubuntu-Lebenszyklus in klar benannte Phasen zerlegt.
- `${Status}` wird wörtlich an `dpkg-query` in der inneren Container-Shell übergeben.
- Lebenszyklus erhält ein kontrolliertes 74-Minuten-Limit innerhalb des 80-Minuten-Jobs, damit Zeit für `if: always()`-Evidenzupload bleibt.
- README vollständig verdichtet und um eine zweispaltige Tabelle mit fertigen und unfertigen Bereichen ergänzt.
- Anleitung, Releasevertrag, Schwachstellenliste und Upgrade-Pool entdoppelt und auf eindeutige Zuständigkeiten ausgerichtet.
- GUI-Fortschritt, README und TODO auf 33 erledigt, 35 offen, 68 gesamt und 49 Prozent synchronisiert.
- Hilfe- und Tooltipkontrast erhöht; deaktivierte Aktionen bleiben lesbar und begründen ihre Sperre.
- Repositoryvalidator erkennt typische versionierte Überreste und verbietet `_save_` in kanonischen Quelldateinamen.

### Sicherheitswirkung

- Releasefähige Quelldateien werden nicht blind umbenannt; Python-Imports, Manifeste und Startpfade bleiben stabil.
- `_save_` entsteht ausschließlich auf nachvalidierten Kopien nach erfolgreicher Kubuntu-22.04-/24.04-Matrix.
- Ein fehlerhafter Lebenszyklus behält seinen ursprünglichen Exit-Code; der Evidenzupload kann den Fehler nicht verdecken.
- Vorhandene generierte Releaseausgaben werden erst nach vollständiger Vorvalidierung atomar ersetzt; alte Reste werden nicht übernommen.
- `_save_` wird ausdrücklich nicht mit einer kryptografischen Stable-Signatur gleichgesetzt.

## 2026-08-04 – P0-009

- reproduzierbarer amd64-DEB-Builder mit Build-ID und expliziter Runtime-Dateiliste
- Offline-Wheelhouse für PySide6 und privater Runtime-Slot je Build-ID
- geprüfter Release-Manager für Installation, Upgrade, lokales Rollback und Deinstallation
- normale Entfernung mit Erhalt der Nutzerdaten sowie ausdrücklich bestätigter vollständiger Purge
- byteidentischer Doppelbuild des Releasekandidaten
- automatisierte Lebenszyklusmatrix in Kubuntu-22.04-/24.04-Userlands
- Manifest auf Schema 1.5.0 aktualisiert

## 2026-08-04 – P0-008

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

## 2026-08-04 – P0-007

- append-only Undo-/Redo-Journal mit SHA-256-Hashkette
- zehnfacher Undo-/Redo-Rundlauf
- rein lesende Transaktionsübersicht
