# UPGRADE_POOL

Der Upgrade-Pool enthält ausschließlich Linux-bezogene Ideen, die nicht automatisch zum verbindlichen Entwicklungsumfang gehören. Eine Idee wird erst nach Nutzen-, Risiko-, Abhängigkeits- und Wartungsprüfung in `TODO.md` übernommen.

## Bewertungslogik

- Nutzen: niedrig / mittel / hoch
- Risiko: niedrig / mittel / hoch
- Aufwand: klein / mittel / groß
- Entscheidung: beobachten / vorbereiten / später prüfen / verwerfen

## Ausschluss

Windows-, macOS-, Android-, iOS-, Browser- und PWA-Varianten werden nicht aufgenommen. Plattformübergreifende Kompatibilität ist kein Optimierungsziel.

## Aktueller Pool

| ID | Idee | Nutzen | Risiko | Aufwand | Voraussetzung | Entscheidung |
|---|---|---:|---:|---:|---|---|
| U-001 | zentrale Design-Tokens erzeugen QSS und Dokumentation | hoch | niedrig | mittel | stabiles Grundtheme | vorbereiten |
| U-002 | portable Linux-Ausgabe ohne absolute Benutzerpfade | hoch | mittel | groß | stabiles Daten- und Migrationsmodell | später prüfen |
| U-003 | A/B-Update-Slots mit atomarem Linux-Rückfall | hoch | mittel | groß | installierbares Linux-Release | beobachten |
| U-004 | optionale Miniatur- und Audio-Vorschau | mittel | mittel | groß | Ressourcen- und Fehlergrenzen | später prüfen |
| U-005 | lokale regelbasierte Vorschläge aus Dateinamen und Metadaten | hoch | mittel | groß | sicherer Analyse-Kern | beobachten |
| U-006 | Profile für wiederkehrende Organisationsstrategien | hoch | niedrig | mittel | stabile Regelengine | vorbereiten |
| U-007 | signierte Modulmanifeste | mittel | mittel | groß | definierte Modulschnittstelle | beobachten |
| U-008 | exportierbarer Diagnosebericht ohne private Daten | hoch | niedrig | klein | Loggingvertrag | vorbereiten |
| U-009 | Hochkontrast-, Neon- und ruhiges KDE-Theme | mittel | niedrig | mittel | Design-Tokens | vorbereiten |
| U-010 | geführter Laienmodus und transparenter Expertenmodus | hoch | niedrig | mittel | stabile Kernworkflows | später prüfen |
| U-011 | AppImage- und Debian-Paket als parallele Linux-Ausgabe | hoch | mittel | groß | reproduzierbarer Build | später prüfen |
| U-012 | optionale systemd-Userdienste für geplante lokale Aufgaben | mittel | mittel | groß | stabiler Worker- und Berechtigungsvertrag | beobachten |

## Aufnahme in TODO.md

Eine Idee wechselt nur dann in `TODO.md`, wenn:

1. der konkrete Linux-Nutzergewinn beschrieben ist,
2. keine Doppelung mit vorhandenen Aufgaben besteht,
3. Abhängigkeiten und Rückfallweg bekannt sind,
4. ein objektives Abnahmekriterium formuliert ist,
5. das Risiko den aktuellen Projektstand nicht destabilisiert.
