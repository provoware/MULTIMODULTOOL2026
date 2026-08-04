# TODO – MULTIMODULTOOL2026

**Stand:** 2026-08-04

## Steuerungsregeln

- Jede Aufgabe besitzt eine eindeutige ID, Priorität, Abhängigkeit, Abnahmekriterium und Risikostufe.
- Eine Aufgabe wird erst als erledigt markiert, wenn Umsetzung, direkt relevante Prüfung, Dokumentation und GitHub-Commit bestätigt sind.
- Neue Aufgaben werden vor Aufnahme auf Doppelungen, versteckte Abhängigkeiten, Datenrisiko und Bediennutzen geprüft.
- P0 blockiert den Release. P1 bildet den laiengerechten Kern. P2 verbessert Bedienung und Transparenz. P3 härtet Architektur und Qualität. P4 bleibt bis zum stabilen Kern nachgeordnet.
- Bei Zielkonflikten gilt: Datensicherheit vor Komfort, Nachvollziehbarkeit vor Geschwindigkeit, kleiner reversibler Patch vor riskantem Großumbau.
- Alle Aufgaben richten sich ausschließlich an Linux-Desktop-Systeme. Andere Betriebssysteme, Browser und PWA sind ausgeschlossen.

## Fortschritt

- Erledigt: **18**
- Offen: **44**
- Gesamt: **62**
- Rechnerischer Entwicklungsfortschritt: **29 %**

## Erledigte Grundlagen

- [x] **D-001** – Repository bereinigt und neuer Projektstand auf `main` angelegt.
- [x] **D-002** – Visuelle UI-Referenz dauerhaft im Repository abgelegt.
- [x] **D-003** – Verbindlichen UI-Layoutstandard dokumentiert.
- [x] **D-004** – Maschinenlesbares `layout-manifest.json` eingeführt.
- [x] **D-005** – Neun feste Layoutzonen mit Reihenfolge und Rollen definiert.
- [x] **D-006** – GitHub-Synchronisierung als Iterationspflicht in `AGENTS.md` verankert.
- [x] **D-007** – README-Fortschrittsblock mit automatisch prüfbaren Werten eingeführt.
- [x] **D-008** – Startbares PySide6-Desktop-Grundgerüst mit allen neun Zonen erstellt.
- [x] **D-009** – Manifest-Validierung vor jedem grafischen Start integriert.
- [x] **D-010** – Abhängigkeitsarmen Modus `--validate-only` für CI und Diagnose ergänzt.
- [x] **D-011** – Laiengerechte Linux-Startroutine `start.sh` mit Ampelausgabe erstellt.
- [x] **D-012** – Automatischen Repository-Vertragsprüfer implementiert.
- [x] **D-013** – Unit-Tests für Manifest, Zonenvertrag und Repository-Prüfung ergänzt.
- [x] **D-014** – GitHub-Actions-Prüfung auf Ubuntu bei jedem Push und Pull Request eingerichtet.
- [x] **D-015** – Pflichtdokumente für Anleitung, Änderungen, Risiken, Upgrades und Entwicklung angelegt.
- [x] **D-016** – Projektumfang verbindlich auf Linux-Desktop, Kubuntu und KDE Plasma begrenzt.
- [x] **D-017** – Nicht-Linux-Startblocker und maschinenlesbaren Linux-Plattformvertrag ergänzt.

## Offene, priorisierte Aufgaben

## P0 – Startfähigkeit, Datensicherheit und Releaseblocker

- [x] **P0-001** – PySide6-Installation über einen geführten Linux-Einrichtungsdialog automatisieren. Abhängigkeit: `D-011` | Abnahmekriterium: Frische Kubuntu-Installation startet nach höchstens zwei bestätigten Dialogen. | Risiko: **mittel** | Ergebnis: atomare `.venv`-Einrichtung, KDE-KDialog mit Terminal-Rückfall, System-, Sitzungs-, Rechte- und PySide6-Prüfung.
- [ ] **P0-002** – XDG-konforme Projekt- und Nutzerdatenpfade strikt vom Programmverzeichnis trennen. Abhängigkeit: `P0-001` | Abnahmekriterium: App nutzt sichere Linux-Benutzerpfade und schreibt nie ungefragt in den Quellbaum. | Risiko: **hoch**
- [ ] **P0-003** – Transaktionales Einstellungsformat mit Schema, Backup und Rollback einführen. Abhängigkeit: `P0-002` | Abnahmekriterium: Defekte Konfiguration wird erkannt und verlustfrei auf letzte gültige Version zurückgesetzt. | Risiko: **hoch**
- [ ] **P0-004** – Globalen Fehlerdialog mit Ursache, Folge, Lösung und unverändertem Datenstand erstellen. Abhängigkeit: `D-008` | Abnahmekriterium: Jede unbehandelte Ausnahme wird verständlich protokolliert und beendet die App kontrolliert. | Risiko: **hoch**
- [ ] **P0-005** – Linux-Single-Instance-Schutz und sichere Übergabe weiterer Startaufrufe implementieren. Abhängigkeit: `P0-002` | Abnahmekriterium: Zweiter Start öffnet das bestehende Fenster statt eine konkurrierende Instanz. | Risiko: **mittel**
- [ ] **P0-006** – Papierkorbvertrag für alle späteren destruktiven Dateiaktionen definieren und testen. Abhängigkeit: `P0-002` | Abnahmekriterium: Löschen bedeutet standardmäßig Verschieben in wiederherstellbaren Projektpapierkorb. | Risiko: **hoch**
- [ ] **P0-007** – Undo-/Redo-Protokoll mit eindeutigen Aktions-IDs und Grenzen entwerfen. Abhängigkeit: `P0-006` | Abnahmekriterium: Mindestens zehn reversible Testaktionen können in korrekter Reihenfolge zurückgenommen werden. | Risiko: **hoch**
- [ ] **P0-008** – Abbruch- und Wiederanlaufvertrag für lange Dateioperationen implementieren. Abhängigkeit: `P0-003` | Abnahmekriterium: Abbruch hinterlässt konsistenten Zustand; Wiederaufnahme erzeugt keine Doppeloperation. | Risiko: **hoch**
- [ ] **P0-009** – Ersten installierbaren Linux-Releasekandidaten für Kubuntu 22.04/24.04 paketieren. Abhängigkeit: `P0-001,P0-004,P0-008` | Abnahmekriterium: Saubere Kubuntu-VM installiert, startet, deinstalliert und hinterlässt keine privaten Daten. | Risiko: **hoch**

## P1 – Laienoptimierter Kernworkflow

- [ ] **P1-001** – Geführten Startassistenten für Projektordner, Ziel und Sicherheitsmodus erstellen. Abhängigkeit: `P0-002` | Abnahmekriterium: Neuer Nutzer erreicht ohne Freitexteingabe einen gültigen Startzustand. | Risiko: **mittel**
- [ ] **P1-002** – Kachelbasierte Modulnavigation mit aktivem Zustand und Zurück-Pfad umsetzen. Abhängigkeit: `D-008` | Abnahmekriterium: Jedes Modul ist mit höchstens zwei Klicks erreichbar und verlässt keinen Sackgassen-Zustand. | Risiko: **niedrig**
- [ ] **P1-003** – Linux-Ordnerauswahl mit Vorprüfung auf Rechte, Mountstatus, Erreichbarkeit und freien Speicher ergänzen. Abhängigkeit: `P1-001` | Abnahmekriterium: Ungültige Ziele werden vor Verarbeitung blockiert und mit Lösung erklärt. | Risiko: **hoch**
- [ ] **P1-004** – Dateibestandsanalyse für Typ, Größe, Datum, Symlinks und Namensmuster entwickeln. Abhängigkeit: `P1-003` | Abnahmekriterium: Testbestand wird vollständig gezählt; Summen stimmen bytegenau; Symlinks werden eindeutig behandelt. | Risiko: **mittel**
- [ ] **P1-005** – Vorschauansicht für geplante Änderungen mit Vorher-/Nachher-Vergleich erstellen. Abhängigkeit: `P1-004` | Abnahmekriterium: Keine Massenänderung kann ohne sichtbare vollständige Vorschau gestartet werden. | Risiko: **hoch**
- [ ] **P1-006** – Sicheren Massenumbenennungsworkflow mit Linux-Dateinamen- und Konfliktprüfung implementieren. Abhängigkeit: `P1-005,P0-007` | Abnahmekriterium: Doppelte Zielnamen werden vor Ausführung aufgelöst; Undo stellt Ursprungsnamen wieder her. | Risiko: **hoch**
- [ ] **P1-007** – Duplikatfinder zunächst hashbasiert und read-only entwickeln. Abhängigkeit: `P1-004` | Abnahmekriterium: Identische Testdateien werden erkannt; keine Datei wird automatisch gelöscht. | Risiko: **mittel**
- [ ] **P1-008** – Regelbasiertes Sortieren und Verschieben mit Trockenlauf implementieren. Abhängigkeit: `P1-005,P0-008` | Abnahmekriterium: Trockenlauf und echte Ausführung liefern dieselbe geplante Aktionsliste. | Risiko: **hoch**
- [ ] **P1-009** – Ergebnisbericht mit Änderungen, Fehlern, Rückfallweg und Export erzeugen. Abhängigkeit: `P1-006,P1-008` | Abnahmekriterium: Jede Operation erzeugt einen verständlichen Bericht als JSON und Markdown. | Risiko: **mittel**

## P2 – Bedienung, Barrierearmut und Transparenz

- [ ] **P2-001** – Tastaturreihenfolge, Fokusrahmen und vollständige Bedienung ohne Maus unter KDE prüfen. Abhängigkeit: `P1-002` | Abnahmekriterium: Alle Hauptaktionen sind per Tastatur erreichbar und sichtbar fokussiert. | Risiko: **mittel**
- [ ] **P2-002** – Linux-Schriftgrößen- und Zoomsystem ohne abgeschnittene Elemente implementieren. Abhängigkeit: `D-008` | Abnahmekriterium: Bei 80–200 Prozent Zoom bleiben Hauptaktionen und Status erreichbar. | Risiko: **mittel**
- [ ] **P2-003** – Kontrastprüfung für Standard-, Neon- und Hochkontrasttheme automatisieren. Abhängigkeit: `D-008` | Abnahmekriterium: Text- und Fokuskontraste erreichen die festgelegten Mindestwerte. | Risiko: **mittel**
- [ ] **P2-004** – Kontextbezogene Hilfe in der rechten Leiste für jeden Arbeitsschritt erstellen. Abhängigkeit: `P1-001` | Abnahmekriterium: Jeder Schritt erklärt Zweck, Eingabe, Risiko und nächsten Klick. | Risiko: **niedrig**
- [ ] **P2-005** – Statusmeldungen zusätzlich zu Farben mit Text und Symbol kennzeichnen. Abhängigkeit: `D-008` | Abnahmekriterium: Ampelzustände bleiben in Graustufen eindeutig verständlich. | Risiko: **niedrig**
- [ ] **P2-006** – Leere Zustände, Ladezustände und Fehlzustände für alle Hauptzonen definieren. Abhängigkeit: `P1-002` | Abnahmekriterium: Keine Zone zeigt unkommentierte Leere oder endloses Laden. | Risiko: **mittel**
- [ ] **P2-007** – Responsives Verhalten für kleine bis hochauflösende Linux-Desktopfenster umsetzen. Abhängigkeit: `P2-002` | Abnahmekriterium: Zwischen 1024 × 680 und 4K bleibt kein kritisches Element abgeschnitten. | Risiko: **mittel**
- [ ] **P2-008** – Bestätigungsdialoge nach Risikoklassen vereinheitlichen. Abhängigkeit: `P0-006` | Abnahmekriterium: Nur destruktive Aktionen verlangen starke Bestätigung; sichere Aktionen bleiben flüssig. | Risiko: **mittel**
- [ ] **P2-009** – Laien-Testprotokoll mit fünf realistischen Kubuntu-Erstnutzer-Szenarien erstellen. Abhängigkeit: `P1-009` | Abnahmekriterium: Mindestens vier von fünf Szenarien werden ohne externe Erklärung abgeschlossen. | Risiko: **niedrig**

## P3 – Architektur, Qualität und Wartbarkeit

- [ ] **P3-001** – Linux-Modulschnittstelle mit Manifest, Lebenszyklus und isoliertem Datenbereich definieren. Abhängigkeit: `P0-003` | Abnahmekriterium: Beispielmodul wird geladen, deaktiviert und aktualisiert, ohne Kerndaten zu verändern. | Risiko: **hoch**
- [ ] **P3-002** – Zentrale Design-Tokens als einzige Quelle für QSS und Dokumentation einführen. Abhängigkeit: `D-008` | Abnahmekriterium: Farben, Abstände und Typografie werden aus einer Quelldatei erzeugt. | Risiko: **mittel**
- [ ] **P3-003** – Logging mit Rotation, Datenschutzfilter, XDG-State-Pfad und verständlichen Ereigniscodes umsetzen. Abhängigkeit: `P0-004` | Abnahmekriterium: Logs enthalten keine privaten Dateiinhalte und überschreiten das Größenlimit nicht. | Risiko: **hoch**
- [ ] **P3-004** – Linux-Testdaten-Generator für große, konfliktbehaftete Dateibestände entwickeln. Abhängigkeit: `P1-004` | Abnahmekriterium: Reproduzierbarer Bestand mit Duplikaten, Symlinks, Sonderzeichen und Pfadgrenzen wird erzeugt. | Risiko: **niedrig**
- [ ] **P3-005** – Unit- und Integrationstestabdeckung auf mindestens 80 Prozent erhöhen. Abhängigkeit: `P3-004` | Abnahmekriterium: Messbericht erreicht mindestens 80 Prozent für sicherheitskritische Kernmodule. | Risiko: **mittel**
- [ ] **P3-006** – Komplexitätsgrenzen und statische Qualitätsprüfung in Ubuntu-CI ergänzen. Abhängigkeit: `D-014` | Abnahmekriterium: CI blockiert Syntaxfehler, hohe Komplexität und unsichere Standardmuster. | Risiko: **mittel**
- [ ] **P3-007** – Versioniertes Datenmigrationssystem mit Vor-/Nachvalidierung erstellen. Abhängigkeit: `P0-003` | Abnahmekriterium: Migrationen sind idempotent und können auf Testdaten zurückgerollt werden. | Risiko: **hoch**
- [ ] **P3-008** – Reproduzierbare Linux-Build-ID aus Version und Quellhash einführen. Abhängigkeit: `P0-009` | Abnahmekriterium: App und Prüfbericht zeigen identische, reproduzierbare Build-ID. | Risiko: **mittel**
- [ ] **P3-009** – Linux-Release-Gate mit signierten Prüfergebnissen und Artefakthashes definieren. Abhängigkeit: `P3-005,P3-008` | Abnahmekriterium: Release wird nur bei grünen Pflichtprüfungen und passenden Hashes freigegeben. | Risiko: **hoch**

## P4 – Erweiterungen nach stabilem Kern

- [ ] **P4-001** – Profilverwaltung für wiederkehrende Organisationsregeln ergänzen. Abhängigkeit: `P1-008` | Abnahmekriterium: Profile sind exportierbar, validiert und ohne versteckte Pfade portabel. | Risiko: **mittel**
- [ ] **P4-002** – Linux-Metadaten- und Tagstrategie für Wiederfindbarkeit entwickeln. Abhängigkeit: `P1-004` | Abnahmekriterium: Tags können gesucht, exportiert und konfliktfrei aktualisiert werden. | Risiko: **mittel**
- [ ] **P4-003** – Bild-Miniaturen und sichere Medienvorschau implementieren. Abhängigkeit: `P1-004` | Abnahmekriterium: Beschädigte Medien blockieren die Oberfläche nicht und werden gekennzeichnet. | Risiko: **mittel**
- [ ] **P4-004** – Audio-Vorhörfunktion mit Playlist und Ressourcenlimit ergänzen. Abhängigkeit: `P3-003` | Abnahmekriterium: Wiedergabe bleibt abbrechbar und überschreitet definierte Ressourcenlimits nicht. | Risiko: **mittel**
- [ ] **P4-005** – Regelvorlagen für typische große Linux-Sammlungen bereitstellen. Abhängigkeit: `P4-001` | Abnahmekriterium: Jede Vorlage erklärt Wirkung und startet standardmäßig im Trockenlauf. | Risiko: **niedrig**
- [ ] **P4-006** – Exportcenter für Berichte, Profile und Diagnosedaten entwickeln. Abhängigkeit: `P1-009` | Abnahmekriterium: Nutzer wählt Exporttyp und Ziel ausschließlich über sichere Dialoge. | Risiko: **mittel**
- [ ] **P4-007** – Linux-Plugin-Sandbox und Berechtigungsmodell untersuchen. Abhängigkeit: `P3-001` | Abnahmekriterium: Machbarkeitsbericht benennt Grenzen, Angriffsflächen und sichere Minimalvariante. | Risiko: **hoch**
- [ ] **P4-008** – Optionale portable Linux-Ausgabe ohne absolute Benutzerpfade entwickeln. Abhängigkeit: `P0-009,P3-007` | Abnahmekriterium: Projekt lässt sich auf zweitem Linux-Nutzerkonto ohne Pfadkorrektur öffnen. | Risiko: **hoch**
- [ ] **P4-009** – Physische Abnahme auf Kubuntu 22.04/24.04, X11/Wayland und mehreren Auflösungen dokumentieren. Abhängigkeit: `P2-007,P3-009` | Abnahmekriterium: Abnahmeprotokoll enthält Systemprofil, Sitzungstyp, Auflösung, Ergebnis, Mängel und Rückfallentscheidung. | Risiko: **mittel**

## Aufnahme neuer Aufgaben

Eine neue Aufgabe wird nur aufgenommen, wenn Linux-Nutzerproblem, betroffene Daten, Doppelungsprüfung, Abhängigkeiten, objektives Abnahmekriterium, Rückfallweg, Pflichtprüfung und betroffene Dokumente bekannt sind.

## Abschlussformat je Aufgabe

`ID | Ergebnis | Prüfung | betroffene Dokumente | Commit-SHA | verbleibendes Risiko`
