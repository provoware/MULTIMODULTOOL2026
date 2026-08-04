# UPGRADE_POOL

Der Upgrade-Pool enthält optionale Linux-Ideen außerhalb des verbindlichen Pflichtumfangs. Aufnahme in `TODO.md` erfolgt nur nach Nutzen-, Risiko-, Abhängigkeits- und Wartungsprüfung.

| ID | Idee | Nutzen | Risiko | Aufwand | Voraussetzung | Entscheidung |
|---|---|---:|---:|---:|---|---|
| U-001 | Design-Tokens erzeugen QSS und Dokumentation | hoch | niedrig | mittel | stabiles Grundtheme | vorbereiten |
| U-002 | portable Linux-Ausgabe ohne absolute Benutzerpfade | hoch | mittel | groß | stabiles Datenmodell | später prüfen |
| U-003 | A/B-Update-Slots mit atomarem Rückfall | hoch | mittel | groß | installierbares Release | beobachten |
| U-004 | optionale Miniatur- und Audio-Vorschau | mittel | mittel | groß | Ressourcen- und Fehlergrenzen | später prüfen |
| U-005 | lokale regelbasierte Vorschläge aus Metadaten | hoch | mittel | groß | sicherer Analyse-Kern | beobachten |
| U-006 | Profile für Organisationsstrategien | hoch | niedrig | mittel | stabile Regelengine | vorbereiten |
| U-007 | signierte Modulmanifeste | mittel | mittel | groß | definierte Modulschnittstelle | beobachten |
| U-008 | exportierbarer Diagnosebericht ohne private Daten | hoch | niedrig | klein | P0-004 und Datenschutzfilter | vorbereiten |
| U-009 | Hochkontrast-, Neon- und ruhiges KDE-Theme | mittel | niedrig | mittel | Design-Tokens | vorbereiten |
| U-010 | geführter Laienmodus und Expertenmodus | hoch | niedrig | mittel | stabile Workflows | später prüfen |
| U-011 | AppImage und Debian-Paket parallel | hoch | mittel | groß | reproduzierbarer Build | später prüfen |
| U-012 | systemd-Userdienste für geplante lokale Aufgaben | mittel | mittel | groß | Worker-/Berechtigungsvertrag | beobachten |
| U-013 | Diagnose-Paket mit ausgewählten Ereignissen und Systemprofil | hoch | mittel | mittel | P3-003 Rotation, explizite Vorschau und Exportdialog | vorbereiten |
| U-014 | lokale Fehlerhäufigkeitsstatistik ohne Dateiinhalte | mittel | niedrig | klein | rotierendes Ereignisjournal | später prüfen |

## Ausschluss

Keine Windows-, macOS-, Android-, iOS-, Browser- oder PWA-Varianten. Keine automatische Cloud-Übertragung von Diagnosedaten.
