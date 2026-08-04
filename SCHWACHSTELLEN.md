# SCHWACHSTELLEN

## Bewertungsmaßstab

- **kritisch:** möglicher Datenverlust, falsche Freigabe oder unkontrollierbarer Zustand
- **hoch:** blockiert sicheren produktiven Einsatz
- **mittel:** deutlicher Bedien-, Wartungs- oder Zuverlässigkeitsnachteil
- **niedrig:** begrenzte Auswirkung oder vorbereitender Mangel

## Aktive Schwachstellen

| ID | Stufe | Schwachstelle | Aktuelle Begrenzung | Gegenmaßnahme | Aufgabe |
|---|---|---|---|---|---|
| S-004 | hoch | kein globaler Fehler- und Wiederanlaufmanager | unerwartete GUI-Fehler sind noch nicht zentral erklärt | Fehlerdialog, Ereignismodell und Recoverybericht | P0-004 |
| S-005 | hoch | Papierkorb- und Undo-Vertrag fehlen | Löschen oder Verschieben bleibt gesperrt | reversible Aktionsarchitektur | P0-006, P0-007 |
| S-006 | hoch | lange Aufgaben besitzen keinen Abbruchschutz | spätere Batchläufe könnten inkonsistent enden | Checkpoints und idempotenter Wiederanlauf | P0-008 |
| S-007 | mittel | Layout ist nicht physisch auf allen Linux-Zielgrößen abgenommen | Offscreen-Test ersetzt keine reale DPI-/Fensterprüfung | Zoom-, Fokus- und Responsive-Abnahme | P2-002, P2-007 |
| S-009 | mittel | CI prüft noch keine Abdeckung oder Komplexität | schleichende Qualitätsverluste möglich | Coverage- und statische Gates | P3-005, P3-006 |
| S-010 | hoch | kein installierbares signiertes Linux-Artefakt | Start weiterhin aus Quellbaum | reproduzierbares Paket und Release-Gate | P0-009, P3-009 |
| S-011 | mittel | Wayland- und X11-Verhalten nicht physisch abgenommen | Dialog-, Fokus- oder Skalierungsunterschiede möglich | getrennte Kubuntu-Abnahme | P4-009 |
| S-012 | mittel | Ersteinrichtung lädt PySide6 aus dem Internet | Offline-Erstinstallation nicht möglich | geprüftes Wheelhouse oder Releasepaket | U-013 |
| S-013 | mittel | Setup noch nicht auf frischen Kubuntu-VMs vollständig abgenommen | Distributionseigenheiten können unentdeckt bleiben | reale 22.04/24.04-Abnahme | P4-009 |
| S-014 | mittel | Einstellungsformat besitzt noch keine Migrationsengine für Version 2+ | zukünftige Schemaänderungen müssen bis P3-007 blockiert bleiben | idempotente Migrationen mit Rollback | P3-007 |
| S-015 | niedrig | beschädigte Einstellungen werden lokal quarantänisiert, aber noch nicht in einer GUI erklärt | Recovery ist in Konsole und Statusbereich sichtbar | Integration in globale Fehlerzentrale | P0-004 |

## Behobene Schwachstellen

| ID | Ergebnis | Prüfung |
|---|---|---|
| S-001 | manuelle PySide6-Einrichtung durch geführten Assistenten ersetzt | Setup-Unit-Tests und atomarer `.venv`-Vertrag |
| S-002 | private Laufzeitpfade strikt vom Quellbaum getrennt | XDG-Vor-/Nachvalidierung, 0700, Schreibproben und Tests |
| S-003 | versioniertes transaktionales Einstellungsformat eingeführt | 15 Unit-Tests, 0600, Backup, Quarantäne und automatischer Rollback |
| S-008 | grundlegende UI-Struktur automatisch prüfbar gemacht | Offscreen-Smoke-Test für Z01–Z09, Scrollbarkeit, Status und Sperren |

## Bewusste Grenzen

- Funktionskacheln führen noch keine Dateiaktionen aus.
- Nicht-Linux-Systeme werden nicht unterstützt.
- GitHub-Schreibrechte werden extern durch Konto und App verwaltet.
- Einstellungsdateien enthalten keine Geheimnisse.
- Offscreen-Tests sind keine vollständige physische KDE-Abnahme.

## Pflegepflicht

Neue Schwachstellen erhalten ID, Stufe, Auswirkung, Begrenzung, Gegenmaßnahme und verknüpfte Aufgabe.
