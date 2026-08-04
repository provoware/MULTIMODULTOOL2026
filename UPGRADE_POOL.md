# UPGRADE_POOL

Der Upgrade-Pool enthält ausschließlich Linux-bezogene Ideen außerhalb des verbindlichen Kernplans.

## Bewertungslogik

Nutzen, Risiko und Aufwand werden jeweils als niedrig, mittel oder hoch bewertet. Eine Übernahme in `TODO.md` benötigt ein objektives Abnahmekriterium und bekannte Abhängigkeiten.

## Ausschluss

Windows-, macOS-, Android-, iOS-, Browser- und PWA-Varianten werden nicht aufgenommen.

## Aktueller Pool

| ID | Idee | Nutzen | Risiko | Aufwand | Voraussetzung | Entscheidung |
|---|---|---:|---:|---:|---|---|
| U-001 | zentrale Design-Tokens erzeugen QSS und Dokumentation | hoch | niedrig | mittel | stabiles Grundtheme | vorbereiten |
| U-002 | portable Linux-Ausgabe ohne absolute Benutzerpfade | hoch | mittel | groß | stabiles Datenmodell | später prüfen |
| U-003 | A/B-Update-Slots mit atomarem Linux-Rückfall | hoch | mittel | groß | installierbares Release | beobachten |
| U-004 | optionale Miniatur- und Audio-Vorschau | mittel | mittel | groß | Ressourcen- und Fehlergrenzen | später prüfen |
| U-005 | lokale regelbasierte Vorschläge aus Dateinamen und Metadaten | hoch | mittel | groß | sicherer Analyse-Kern | beobachten |
| U-006 | Profile für wiederkehrende Organisationsstrategien | hoch | niedrig | mittel | stabile Regelengine | vorbereiten |
| U-007 | signierte Modulmanifeste | mittel | mittel | groß | definierte Modulschnittstelle | beobachten |
| U-008 | exportierbarer Diagnosebericht ohne private Daten | hoch | niedrig | klein | Loggingvertrag | vorbereiten |
| U-009 | Hochkontrast-, Neon- und ruhiges KDE-Theme | mittel | niedrig | mittel | Design-Tokens | vorbereiten |
| U-010 | geführter Laienmodus und transparenter Expertenmodus | hoch | niedrig | mittel | stabile Kernworkflows | später prüfen |
| U-011 | AppImage- und Debian-Paket parallel | hoch | mittel | groß | reproduzierbarer Build | später prüfen |
| U-012 | systemd-Userdienste für geplante lokale Aufgaben | mittel | mittel | groß | stabiler Worker-Vertrag | beobachten |
| U-013 | signiertes Offline-Wheelhouse für PySide6-Ersteinrichtung | hoch | mittel | groß | reproduzierbarer Releaseprozess | vorbereiten |

## Ergebnis dieser Iteration

Die XDG-Pfadschicht ist als P0-002 abgeschlossen. Sie schafft die Grundlage für portable Linux-Ausgaben ohne gespeicherte Benutzerpfade (`U-002`) und datensparsame Diagnoseexporte (`U-008`). Diese Erweiterungen bleiben getrennt, bis Einstellungs-, Logging- und Releaseverträge stabil sind.

## Aufnahme in TODO.md

Eine Idee wechselt nur bei konkretem Linux-Nutzergewinn, fehlender Doppelung, bekannten Abhängigkeiten, Rückfallweg und objektivem Abnahmekriterium.
