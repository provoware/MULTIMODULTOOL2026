# Fehler- und Ereignisvertrag – MULTIMODULTOOL2026

## Pflichtfelder

Jeder globale Fehlerbericht enthält vollständig:

1. Ursache
2. Folge
3. unveränderten oder kontrolliert veränderten Datenstand
4. Lösung
5. Diagnosekennung
6. sicheren nächsten Schritt

## Erfasste Bereiche

- Hauptthread-, Worker- und Qt-Ausnahmen
- Manifest-, XDG- und Einstellungsfehler
- Einstellungs-Recovery
- Single-Instance-Laufzeit-, Socket-, Metadaten- und Nachrichtenfehler
- Projektpapierkorb-Vorschau, Transaktion und Wiederherstellung
- spätere Dateioperationen über `SafeOperationError`

## Papierkorbereignisse

`src/project_trash.py` verwendet ausschließlich `SafeOperationError(category="project-trash")`. Typische Ursachen sind:

- Quelle außerhalb der Projektgrenze
- Symlink oder Symlink-Komponente
- zusätzlicher Hardlink
- Mount- oder Dateisystemwechsel
- unzureichender freier Speicher
- Quelle seit der Vorschau verändert
- belegte Transaktions-ID oder belegter Restore-Pfad
- beschädigtes oder zu offenes Manifest
- fehlender oder veränderter Payload
- fehlgeschlagene atomare Umbenennung

Der Datenstand muss präzise nennen, ob das Objekt vollständig am Originalpfad oder vollständig im privaten Transaktionsordner liegt. Unklare Zustände dürfen nicht als erfolgreich gemeldet werden. Dauerhaftes Löschen ist kein Fehler-Rückfallweg.

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

Die Diagnosezentrale liest dasselbe Journal nur mit `O_RDONLY` und `O_NOFOLLOW`. Sie verändert, repariert, löscht oder exportiert es nicht automatisch.

## Grenzen

Journalrotation folgt `P3-003`. Physische KDE-X11-/Wayland-Abnahme sowie reale Sonder-Mount- und ACL-Tests bleiben offen.
