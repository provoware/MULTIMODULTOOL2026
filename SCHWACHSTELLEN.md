# SCHWACHSTELLEN

## Bewertungsmaßstab

- **kritisch:** möglicher Datenverlust, falsche Freigabe oder unkontrollierbarer Zustand
- **hoch:** blockiert sicheren produktiven Einsatz
- **mittel:** deutlicher Bedien-, Wartungs- oder Zuverlässigkeitsnachteil
- **niedrig:** begrenzte Auswirkung oder vorbereitender Mangel

## Aktive Schwachstellen

| ID | Stufe | Schwachstelle | Aktuelle Begrenzung | Gegenmaßnahme | Aufgabe |
|---|---|---|---|---|---|
| S-003 | kritisch | kein transaktionales Einstellungsformat | beschädigte Einstellungen wären nicht sicher rücksetzbar | Schema, Backup, atomarer Schreibvorgang | P0-003 |
| S-004 | hoch | kein globaler Fehler- und Wiederanlaufmanager | unerwartete GUI-Fehler wären nur über Konsole sichtbar | zentraler Fehlerdialog und Recoverybericht | P0-004 |
| S-005 | hoch | Papierkorb- und Undo-Vertrag fehlen | Löschen oder Verschieben bleibt gesperrt | reversible Aktionsarchitektur | P0-006, P0-007 |
| S-006 | hoch | lange Aufgaben besitzen keinen Abbruchschutz | spätere Batchläufe könnten inkonsistent enden | Checkpoints und idempotenter Wiederanlauf | P0-008 |
| S-007 | mittel | Layout ist noch nicht auf Linux-Zielgrößen abgenommen | stark skalierte KDE-Fenster können gedrängt wirken | Zoom-, Fokus- und Responsive-Abnahme | P2-002, P2-007 |
| S-009 | mittel | CI prüft noch keine Abdeckung oder Komplexität | schleichende Qualitätsverluste möglich | Coverage- und statische Gates | P3-005, P3-006 |
| S-010 | hoch | kein installierbares signiertes Linux-Artefakt | Start weiterhin aus Quellbaum | reproduzierbares Paket und Release-Gate | P0-009, P3-009 |
| S-011 | mittel | Wayland- und X11-Verhalten nicht physisch abgenommen | Dialog- oder Fokusunterschiede können fehlen | getrennte Kubuntu-Abnahme | P4-009 |
| S-012 | mittel | Ersteinrichtung lädt PySide6 aktuell aus dem Internet | Offline-Erstinstallation nicht möglich | späteres geprüftes Wheelhouse oder Releasepaket | U-013 |
| S-013 | mittel | P0-001 ist automatisiert, aber noch nicht auf frischen Kubuntu-VMs physisch abgenommen | Distributionseigenheiten können unentdeckt bleiben | reale 22.04/24.04-Abnahme protokollieren | P4-009 |
| S-014 | niedrig | XDG-Pfadschicht ist automatisiert getestet, aber noch nicht mit benutzerdefinierten XDG-Umgebungen auf echten Kubuntu-Systemen abgenommen | seltene Mount-, ACL- oder Home-Sonderfälle können fehlen | physische XDG-Abnahme mit Standard- und benutzerdefinierten Pfaden | P4-009 |

## Behobene Schwachstellen

| ID | Ergebnis | Prüfung |
|---|---|---|
| S-001 | manuelle PySide6-Einrichtung durch geführten Assistenten ersetzt | sechs neue Unit-Tests, atomarer Setup-Vertrag, Repository-Prüfung |
| S-002 | Konfiguration, Daten, Cache, Status, Logs und Sicherungen aus dem Quellbaum in XDG-Benutzerpfade getrennt | sieben XDG-Unit-Tests, Vor-/Nachvalidierung, Modus `0700`, Symlink- und Schreibprüfung |

## Bewusste Grenzen

- Funktionskacheln führen noch keine Dateiaktionen aus; dies ist eine Sicherheitsentscheidung.
- Nicht-Linux-Systeme werden nicht unterstützt.
- GitHub-Schreibrechte können nicht durch Quellcode garantiert werden; sie werden extern geprüft.
- Der Assistent speichert keine GitHub-Tokens oder Zugangsdaten.

## Pflegepflicht

Neue Schwachstellen erhalten ID, Stufe, Auswirkung, Begrenzung, Gegenmaßnahme und verknüpfte Aufgabe.
