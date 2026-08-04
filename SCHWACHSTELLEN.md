# SCHWACHSTELLEN

## Bewertungsmaßstab

- **kritisch:** möglicher Datenverlust, falsche Freigabe oder unkontrollierbarer Zustand
- **hoch:** blockiert sicheren produktiven Einsatz
- **mittel:** deutlicher Bedien-, Wartungs- oder Zuverlässigkeitsnachteil
- **niedrig:** begrenzte Auswirkung oder rein vorbereitender Mangel

## Aktive Schwachstellen

| ID | Stufe | Schwachstelle | Aktuelle Begrenzung | Gegenmaßnahme | Verknüpfte Aufgabe |
|---|---|---|---|---|---|
| S-001 | hoch | PySide6 muss noch manuell eingerichtet werden | kein echter Ein-Klick-Start auf frischem Kubuntu | geführte, prüfende Linux-Einrichtung | P0-001 |
| S-002 | kritisch | Linux-Nutzerdatenpfade sind noch nicht definiert | produktive Dateioperationen bleiben deaktiviert | XDG-konforme Pfadtrennung und Schreibprüfung | P0-002 |
| S-003 | kritisch | kein transaktionales Einstellungsformat | beschädigte Einstellungen wären nicht sicher rücksetzbar | Schema, Backup, atomarer Schreibvorgang | P0-003 |
| S-004 | hoch | kein globaler Fehler- und Wiederanlaufmanager | unerwartete Fehler wären nur über Konsole sichtbar | zentraler Fehlerdialog und Recoverybericht | P0-004 |
| S-005 | hoch | Papierkorb- und Undo-Vertrag fehlen | Löschen oder Verschieben darf nicht produktiv freigeschaltet werden | reversible Aktionsarchitektur | P0-006, P0-007 |
| S-006 | hoch | lange Aufgaben besitzen noch keinen Abbruchschutz | spätere Batchläufe könnten inkonsistent enden | Checkpoints und idempotenter Wiederanlauf | P0-008 |
| S-007 | mittel | Layout ist noch nicht auf Linux-Zielgrößen abgenommen | bei kleinen oder stark skalierten KDE-Fenstern können Bereiche gedrängt wirken | Zoom-, Fokus- und Responsive-Abnahme | P2-002, P2-007 |
| S-008 | mittel | keine echten Icons und keine vollständige Tastaturprüfung | Bedienung ist funktional nur als Gerüst bewertet | A11y- und Fokusprüfung unter KDE | P2-001, P2-005 |
| S-009 | mittel | CI prüft noch keine Abdeckung oder Komplexität | schleichende Qualitätsverluste wären möglich | Coverage- und statische Gates | P3-005, P3-006 |
| S-010 | hoch | kein installierbares oder signiertes Linux-Releaseartefakt | Start nur aus Quellbaum | reproduzierbares Linux-Paket und Release-Gate | P0-009, P3-009 |
| S-011 | mittel | Wayland- und X11-Verhalten ist noch nicht physisch abgenommen | Fenster-, Fokus- oder Dialogunterschiede können unentdeckt bleiben | getrennte Kubuntu-Abnahme unter X11 und Wayland | P4-009 |

## Bewusst nicht als Fehler bewertet

- Funktionskacheln führen noch keine Dateiaktionen aus. Das ist eine Sicherheitsentscheidung.
- Die Referenzgrafik enthält einen älteren Projektnamen. Dokumentation und Anwendung verwenden ausschließlich `MULTIMODULTOOL2026`.
- Der CI-Test installiert PySide6 nicht. Er prüft bewusst den manifest- und repositorybezogenen Kern ohne schwere GUI-Abhängigkeit.
- Nicht-Linux-Systeme werden nicht unterstützt. Das ist ein verbindlicher Projektvertrag, keine offene Schwachstelle.

## Pflegepflicht

Neue Schwachstellen werden nicht versteckt oder nur im Chat erwähnt. Sie erhalten ID, Stufe, Auswirkung, Begrenzung, Gegenmaßnahme und eine verknüpfte TODO-Aufgabe.
