# Fehler- und Ereignisvertrag – MULTIMODULTOOL2026

## Pflichtfelder

Jeder globale Fehlerbericht enthält Ursache, Folge, Datenstand, Lösung, Diagnosekennung und sicheren nächsten Schritt.

## Erfasste Bereiche

- Hauptthread-, Worker- und Qt-Ausnahmen
- Manifest-, XDG- und Einstellungsfehler
- Einstellungs-Recovery
- Single-Instance-Laufzeit-, Socket-, Metadaten- und Nachrichtenfehler
- sichere Wiederherstellung veralteter Instanzsperren
- spätere Dateioperationen über `SafeOperationError`

## Instanzereignisse

- `single-instance-runtime`: kein sicherer XDG-Laufzeitpfad
- `single-instance`: beschädigte, fremde, lebende oder nicht eindeutig veraltete Sperre
- `single-instance-recovery`: eindeutig veraltete Sperre wurde sicher entfernt

Beschädigte Sperren werden niemals nur aufgrund eines Verbindungsfehlers gelöscht.

## Ereignisjournal

```text
~/.local/state/multimodultool2026/logs/events.jsonl
```

Reguläre Datei, ein Hardlink, aktueller Eigentümer, keine Symlinks, Modus `0600`, JSONL und `fsync` je Eintrag. Private Pfade und typische Geheimnismuster werden reduziert.

## Diagnoseansicht

Die Diagnosezentrale liest dasselbe Journal nur mit `O_RDONLY` und `O_NOFOLLOW`. Sie verändert, repariert oder exportiert es nicht automatisch. Ungültige Zeilen werden übersprungen und als Hinweis angezeigt.

## Grenzen

Journalrotation folgt `P3-003`. Physische KDE-X11-/Wayland-Abnahme bleibt offen.
