# TODO – MULTIMODULTOOL2026

**Stand:** 2026-08-04

## Steuerungsregeln

- Jede Aufgabe besitzt eindeutige ID, Priorität, Abhängigkeit, Abnahmekriterium und Risiko.
- Erledigt bedeutet: Umsetzung, direkt relevante Prüfung, Dokumentation und GitHub-Commit sind bestätigt.
- Neue Aufgaben werden auf Doppelungen, Datenrisiko, Linux-Nutzen und versteckte Abhängigkeiten geprüft.
- Datensicherheit steht vor Komfort; ein kleiner reversibler Patch vor riskantem Großumbau.
- Das Projekt richtet sich ausschließlich an Linux-Desktop-Systeme.

## Fortschritt

- Erledigt: **29**
- Offen: **38**
- Gesamt: **67**
- Rechnerischer Entwicklungsfortschritt: **43 %**

## Erledigte Grundlagen

- [x] **D-001** – Repository bereinigt und neuen Projektstand auf `main` angelegt.
- [x] **D-002** – Visuelle UI-Referenz dauerhaft abgelegt.
- [x] **D-003** – Verbindlichen UI-Layoutstandard dokumentiert.
- [x] **D-004** – Maschinenlesbares `layout-manifest.json` eingeführt.
- [x] **D-005** – Neun feste Layoutzonen definiert.
- [x] **D-006** – GitHub-Synchronisierung als Iterationspflicht verankert.
- [x] **D-007** – README-Fortschrittsblock automatisch prüfbar gemacht.
- [x] **D-008** – Startbares PySide6-Grundgerüst erstellt.
- [x] **D-009** – Manifest-Validierung vor GUI-Start integriert.
- [x] **D-010** – Rein lesenden Modus `--validate-only` ergänzt.
- [x] **D-011** – Linux-Startroutine mit Ampelausgabe erstellt.
- [x] **D-012** – Automatischen Repository-Vertragsprüfer implementiert.
- [x] **D-013** – Unit-Tests für Manifest, Zonen und Repository ergänzt.
- [x] **D-014** – Ubuntu-GitHub-Actions-Prüfung eingerichtet.
- [x] **D-015** – Pflichtdokumentation angelegt.
- [x] **D-016** – Projektumfang auf Linux, Kubuntu und KDE Plasma begrenzt.
- [x] **D-017** – Nicht-Linux-Startblocker ergänzt.
- [x] **D-018** – Qt-Offscreen-GUI-Smoke-Test integriert.
- [x] **D-019** – Zehnstufige Failpoint-Matrix für Einstellungen ergänzt.
- [x] **D-020** – Rein lesende Diagnosezentrale mit Schweregrad-/Kennungsfilter und Kopierfunktion integriert. Abhängigkeit: `P0-004` | Abnahme: kein Löschen, Upload oder Auto-Export; Journalbytes bleiben unverändert. | Risiko: **niedrig**
- [x] **D-021** – Parallelstart-Stresstest mit 20 nahezu gleichzeitigen Zweitstarts ergänzt. Abhängigkeit: `P0-005` | Abnahme: genau eine Primärinstanz, jede Kennung höchstens einmal, keine Socket- oder Metadatenreste. | Risiko: **niedrig**
- [x] **D-022** – Rein lesende Transaktionsübersicht für `prepared`, `trashed`, `restored` und `damaged` integriert. Abhängigkeit: `P0-006` | Abnahme: Filter und Anzeige verändern keine Manifeste; kein Restore, Reparieren, Löschen, Upload oder Auto-Export. | Risiko: **niedrig**

## P0 – Startfähigkeit, Datensicherheit und Releaseblocker

- [x] **P0-001** – Geführte PySide6-/Linux-Einrichtung. | Risiko: **mittel**
- [x] **P0-002** – Sichere XDG-Pfadtrennung mit `0700`. | Risiko: **hoch**
- [x] **P0-003** – Versionierte transaktionale Einstellungen mit Backup und Rollback. | Risiko: **hoch**
- [x] **P0-004** – Zentrale Fehler- und Ereignisschicht mit globalem Dialog. | Risiko: **hoch**
- [x] **P0-005** – Sicherer Linux-Single-Instance-Schutz. Abhängigkeit: `P0-002,P0-004` | Abnahme: zweiter Start aktiviert die bestehende Instanz; nur erlaubte Nachrichten; Peer-UID-Prüfung; veraltete Sperren sicher wiederhergestellt; beschädigte Sperren unverändert blockiert. | Risiko: **hoch**
- [x] **P0-006** – Atomaren, projektbezogenen Papierkorbvertrag implementieren. Abhängigkeit: `P0-002,P0-004` | Abnahme: Vorschau bleibt read-only; reguläre Dateien/Ordner werden nur per `os.replace` innerhalb desselben Dateisystems verschoben; Transaktionsmanifest und Restore sind geprüft; Symlink-, Hardlink-, Mount-, Speicher- und Konfliktzustände blockieren. | Risiko: **hoch**
- [x] **P0-007** – Append-only Undo-/Redo-Journal mit eindeutigen Aktions- und Transaktions-IDs. Abhängigkeit: `P0-006` | Abnahme: private hashverkettete JSONL-Historie; Intent-/Abschlussereignisse; idempotentes konfliktgeprüftes Undo/Redo; zehn Aktionen vollständig rückwärts zurückgenommen und vorwärts erneut angewendet; Recovery nach unterbrochenem Apply und Undo. | Risiko: **hoch**
- [ ] **P0-008** – Abbruch- und Wiederanlaufvertrag für lange Operationen. Abhängigkeit: `P0-003,P0-004` | Abnahme: Abbruch bleibt konsistent; Wiederaufnahme erzeugt keine Doppeloperation. | Risiko: **hoch**
- [ ] **P0-009** – Installierbaren Linux-Releasekandidaten paketieren. Abhängigkeit: `P0-001,P0-004,P0-008` | Abnahme: Installation, Start und Deinstallation auf frischer Kubuntu-VM. | Risiko: **hoch**

## P1 – Laienoptimierter Kernworkflow

- [ ] **P1-001** – Geführten Startassistenten für Projektordner, Ziel und Sicherheitsmodus erstellen. | Risiko: **mittel**
- [ ] **P1-002** – Kachelbasierte Modulnavigation mit aktivem Zustand und Zurück-Pfad umsetzen. | Risiko: **niedrig**
- [ ] **P1-003** – Linux-Ordnerauswahl mit Rechte-, Mount- und Speicherprüfung ergänzen. | Risiko: **hoch**
- [ ] **P1-004** – Dateibestandsanalyse für Typ, Größe, Datum, Symlinks und Namensmuster entwickeln. | Risiko: **mittel**
- [ ] **P1-005** – Vollständige Vorher-/Nachher-Vorschau erstellen. | Risiko: **hoch**
- [ ] **P1-006** – Sicheren Massenumbenennungsworkflow implementieren. | Risiko: **hoch**
- [ ] **P1-007** – Hashbasierten read-only Duplikatfinder entwickeln. | Risiko: **mittel**
- [ ] **P1-008** – Regelbasiertes Sortieren/Verschieben mit Trockenlauf implementieren. | Risiko: **hoch**
- [ ] **P1-009** – Ergebnisbericht als JSON und Markdown erzeugen. | Risiko: **mittel**

## P2 – Bedienung, Barrierearmut und Transparenz

- [ ] **P2-001** – Vollständige Tastaturbedienung unter KDE prüfen. | Risiko: **mittel**
- [ ] **P2-002** – Schriftgrößen-/Zoomsystem von 80–200 % ohne Abschneiden implementieren. | Risiko: **mittel**
- [ ] **P2-003** – Kontrastprüfung für alle Themes automatisieren. | Risiko: **mittel**
- [ ] **P2-004** – Kontextbezogene Hilfe je Arbeitsschritt erstellen. | Risiko: **niedrig**
- [ ] **P2-005** – Ampelzustände immer zusätzlich mit Text und Symbol kennzeichnen. | Risiko: **niedrig**
- [ ] **P2-006** – Leere, Lade- und Fehlzustände aller Zonen definieren. | Risiko: **mittel**
- [ ] **P2-007** – Responsives Verhalten zwischen 1024×680 und 4K umsetzen. | Risiko: **mittel**
- [ ] **P2-008** – Bestätigungsdialoge nach Risikoklassen vereinheitlichen. | Risiko: **mittel**
- [ ] **P2-009** – Laien-Testprotokoll mit fünf Kubuntu-Szenarien erstellen. | Risiko: **niedrig**

## P3 – Architektur, Qualität und Wartbarkeit

- [ ] **P3-001** – Linux-Modulschnittstelle mit Manifest und isoliertem Datenbereich definieren. | Risiko: **hoch**
- [ ] **P3-002** – Zentrale Design-Tokens als einzige QSS-Quelle einführen. | Risiko: **mittel**
- [ ] **P3-003** – Ereignisjournal um Rotation, Größenlimit und Archivierung erweitern. | Risiko: **hoch**
- [ ] **P3-004** – Reproduzierbaren Linux-Testdaten-Generator entwickeln. | Risiko: **niedrig**
- [ ] **P3-005** – Testabdeckung sicherheitskritischer Module auf mindestens 80 % erhöhen. | Risiko: **mittel**
- [ ] **P3-006** – Komplexitäts- und statische Qualitätsgrenzen in CI ergänzen. | Risiko: **mittel**
- [ ] **P3-007** – Versioniertes Datenmigrationssystem entwickeln. | Risiko: **hoch**
- [ ] **P3-008** – Reproduzierbare Build-ID aus Version und Quellhash einführen. | Risiko: **mittel**
- [ ] **P3-009** – Signiertes Linux-Release-Gate definieren. | Risiko: **hoch**

## P4 – Erweiterungen nach stabilem Kern

- [ ] **P4-001** – Profilverwaltung für Organisationsregeln ergänzen. | Risiko: **mittel**
- [ ] **P4-002** – Linux-Metadaten- und Tagstrategie entwickeln. | Risiko: **mittel**
- [ ] **P4-003** – Bild-Miniaturen und sichere Medienvorschau implementieren. | Risiko: **mittel**
- [ ] **P4-004** – Audio-Vorhörfunktion mit Ressourcenlimit ergänzen. | Risiko: **mittel**
- [ ] **P4-005** – Regelvorlagen für große Linux-Sammlungen bereitstellen. | Risiko: **niedrig**
- [ ] **P4-006** – Exportcenter für Berichte, Profile und Diagnosedaten entwickeln. | Risiko: **mittel**
- [ ] **P4-007** – Linux-Plugin-Sandbox und Berechtigungsmodell untersuchen. | Risiko: **hoch**
- [ ] **P4-008** – Optionale portable Linux-Ausgabe ohne absolute Benutzerpfade entwickeln. | Risiko: **hoch**
- [ ] **P4-009** – Physische Abnahme auf Kubuntu, X11/Wayland und mehreren Auflösungen dokumentieren. | Risiko: **mittel**
