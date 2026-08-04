# Abbruch- und Wiederanlaufvertrag – MULTIMODULTOOL2026

## Ziel

Lange Operationen müssen kontrolliert unterbrechbar und nach normalem Abbruch, Ausnahme oder Prozessende eindeutig fortsetzbar sein. Kein Neustart darf eine bereits ausgeführte Dateioperation doppelt anwenden, einen bestätigten Journalabschluss verlieren oder einen widersprüchlichen Zwischenzustand automatisch übergehen.

## Speicherstruktur

```text
<Projekt>/.multimodultool2026/runs/<MMTRUN-ID>/
├── plan.json
├── checkpoint.json
├── run.lock
└── cancel.request
```

- Laufverzeichnis: `0700`
- Plan, Checkpoint, Sperre und Abbruchanforderung: `0600`
- Lauf-ID: `MMTRUN-YYYYMMDDTHHMMSS-<12 HEX>`
- Schema: Version 1
- maximal 1.000 Arbeitsschritte je Lauf
- absolute Projektpfade: verboten

## Unveränderlicher Plan

`plan.json` enthält ausschließlich:

- Schemaversion,
- Lauf-ID,
- Operationstyp,
- Erstellungszeit,
- lückenlose Schrittindizes,
- relative Projektpfade,
- SHA-256-Hash des vollständigen Plans.

Eine Änderung am Plan oder seiner Reihenfolge blockiert den Lauf. Der Plan wird nicht als Fortschrittsdatei verwendet und nach der Erstellung nicht ersetzt.

## Atomarer Checkpoint

`checkpoint.json` enthält:

- Lauf- und Planhash,
- Zustand `prepared`, `running`, `cancelled`, `completed` oder `blocked`,
- nächsten Schritt,
- lückenlose abgeschlossene Schrittindizes,
- Versuchszähler,
- aktuellen Schritt mit Aktions- und Transaktions-ID,
- monotone Checkpointgeneration,
- Erstellungs- und Aktualisierungszeit,
- Abbruchstatus und verständliche Statusmeldung.

Jede Aktualisierung erfolgt über eine private temporäre Datei, vollständiges Schreiben, Datei-`fsync`, atomaren `os.replace`, Verzeichnis-`fsync` und anschließende JSON-Nachvalidierung. Temporäre Dateien werden in jedem kontrollierten Fehlerpfad entfernt.

## Exklusive Laufressource

`run.lock` verwendet Linux-`flock`. Genau ein Prozess darf einen Lauf verändern. Ein konkurrierender Wiederanlauf wird blockiert, ohne Checkpoint, Journal, Manifest oder Nutzdaten zu verändern.

Die Abbruchanforderung verwendet bewusst nicht dieselbe Sperre. Sie schreibt nur `cancel.request`; ausschließlich der aktive Laufprozess verändert den Checkpoint. Dadurch kann ein anderer Prozess einen laufenden Vorgang anhalten, ohne Fortschrittsdaten zu überschreiben.

## Kontrollierte Abbruchpunkte

Eine Abbruchanforderung wird nur an sicheren Grenzen bestätigt:

1. vor dem Intent eines neuen Schritts,
2. nach vollständig bestätigter Dateioperation,
3. nach Verzeichnis-`fsync`,
4. nach Manifestabschluss,
5. nach Journalabschluss,
6. nach atomarem Checkpoint des abgeschlossenen Schritts.

Ein Schritt mit bereits angehängtem Intent wird bis zu einem eindeutig bestätigten Zustand abgeschlossen. Es gibt keinen Abbruch zwischen `os.replace` und den zugehörigen Konsistenzbestätigungen.

## Wiederanlaufentscheidung

Für den aktuellen Schritt werden Checkpoint, Aktionsjournal, Manifest, Originalpfad und Payload gemeinsam ausgewertet.

### Noch kein Intent

Checkpoint enthält Aktions- und Transaktions-ID, Quelle liegt am Originalpfad und es gibt weder Journalaktion noch Transaktionsordner. Der gleiche Schritt wird mit denselben IDs fortgesetzt.

### Intent, aber noch keine Transaktion

Das append-only Journal enthält `prepare`, die Quelle liegt unverändert am Originalpfad und der Transaktionsordner fehlt. Der gleiche Intent wird nicht erneut angehängt; die Transaktion wird mit der gespeicherten ID fortgesetzt.

### Vorbereitetes Manifest, Datei noch nicht verschoben

Manifest ist `prepared`, Quelle liegt am Originalpfad und Payload fehlt. Fingerabdruck und Pfade werden erneut geprüft; danach wird die atomare Dateioperation fortgesetzt.

### Datei bereits verschoben

Payload ist vorhanden, Originalpfad frei und Manifest ist `prepared` oder `trashed`. Bei `prepared` werden Verzeichnisse erneut mit `fsync` bestätigt und das Manifest auf `trashed` abgeschlossen. Danach wird ausschließlich das fehlende `apply`-Journalereignis ergänzt.

### Journal bereits abgeschlossen

Ist `apply` vorhanden, wird nur der Laufcheckpoint auf den nächsten Schritt gesetzt. Die Dateioperation wird nicht wiederholt.

### Widerspruch

Mehrere Objekte, veränderter Payload, belegter Originalpfad, beschädigte Hashkette, fremde IDs oder unpassende Manifestzustände blockieren. Es erfolgt keine automatische Reparatur, Löschung oder neue Transaktion.

## Idempotenz

- abgeschlossener Lauf: erneuter Aufruf ist ein No-op,
- abgeschlossener Schritt: nur fehlender Checkpoint wird ergänzt,
- vollständige Dateioperation ohne Manifestabschluss: nur `fsync` und Manifestabschluss,
- vollständiges Manifest ohne Journalabschluss: nur Journalabschluss,
- Intent ohne Dateioperation: Fortsetzung mit derselben Aktions- und Transaktions-ID,
- kein Wiederanlauf erzeugt einen zweiten Payload derselben Aktion.

## Ressourcenfreigabe

- `flock` und Dateideskriptoren werden über Kontextgrenzen freigegeben,
- temporäre Plan- und Checkpointdateien werden entfernt,
- bestätigte Abbruchanforderungen werden nach Checkpoint-`fsync` entfernt,
- persistente `run.lock`-Datei darf bestehen bleiben; maßgeblich ist die Kernel-Sperre,
- ein Neustart muss die Sperre erneut erwerben können.

## `SIGKILL`-Prozessabbruchmatrix

Ein isolierter Linux-Prozess wird an zehn Stellen beendet:

1. `before-intent`
2. `after-intent`
3. `before-file-operation`
4. `after-file-operation`
5. `before-fsync`
6. `after-fsync`
7. `before-manifest-completion`
8. `after-manifest-completion`
9. `before-journal-completion`
10. `after-journal-completion`

Nach jedem Neustart wird verlangt:

- Laufzustand `completed`,
- genau ein abgeschlossener Schritt,
- genau eine aktive Journalaktion,
- gültige Hashkette,
- genau ein Transaktionsordner mit einem Payload,
- gültiges Manifest `trashed`,
- Originalpfad frei,
- unveränderter Payloadinhalt,
- keine temporären Dateien,
- erneut erwerbbare Laufsperre,
- zweiter Wiederanlauf als No-op.

## Grenzen

- Aktuell ist nur die sequenzielle Projektpapierkorbserie als langer Lauf freigegeben.
- Checkpointmigrationen folgen dem späteren Datenmigrationssystem.
- Ein bewusstes Verwerfen oder Verzweigen bestehender Laufpläne ist nicht implementiert.
- `SIGKILL` prüft Prozessende, nicht Stromverlust oder beschädigte Hardware-Schreibcaches.
- Physische Abnahme auf realen Sonder-Mounts, ACL-Projekten und stark ausgelasteten KDE-Sitzungen bleibt offen.
