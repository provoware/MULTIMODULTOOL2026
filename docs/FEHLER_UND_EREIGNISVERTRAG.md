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
- Undo-/Redo-Intent, Journalabschluss, Hashkette und Reihenfolgekonflikte
- read-only Transaktionsübersicht
- spätere Dateioperationen über `SafeOperationError`

## Papierkorbereignisse

`src/project_trash.py` verwendet `SafeOperationError(category="project-trash")`. Typische Ursachen sind Projektgrenze, Symlink, Hardlink, Mountwechsel, Speichermangel, veränderte Quelle, Konflikt, beschädigtes Manifest, veränderter Payload oder fehlgeschlagene atomare Umbenennung.

Der Datenstand muss präzise nennen, ob das Objekt vollständig am Originalpfad oder vollständig im privaten Transaktionsordner liegt. Dauerhaftes Löschen ist kein Fehler-Rückfallweg.

## Undo-/Redo-Ereignisse

`src/undo_redo.py` verwendet `SafeOperationError(category="undo-redo-journal")`. Blockiert werden insbesondere:

- ungültige oder doppelte Aktions-, Transaktions- oder Ereignis-ID
- Lücke in der Sequenz
- unterbrochene SHA-256-Hashkette
- unbekannte oder unzulässige Zustandsfolge
- Undo außerhalb der Rückwärtsreihenfolge
- Redo außerhalb der Vorwärtsreihenfolge
- neue Aktion bei vorhandener Redo-Kette
- unsicherer Journalpfad, Symlink, Hardlink, Eigentümer oder Modus
- widersprüchlicher Intent-, Manifest-, Payload- und Originalzustand
- Journalgrößen- oder Ereignislimit überschritten

Der Fehlerbericht muss nennen, ob die Dateioperation bereits vollständig durchgeführt wurde und lediglich das Abschlussereignis fehlt oder ob keine Dateiänderung stattfand. Vorhandene Journalzeilen dürfen nicht zur Fehlerbehebung verändert werden.

## Transaktionsübersicht

Ungültige Transaktionsverzeichnisse und beschädigte Manifeste werden in der Übersicht als `damaged` markiert. Dies ist eine read-only Diagnoseklassifizierung und keine automatische Reparatur. Manifestbytes, Payloads und Journal bleiben unverändert.

## Instanzereignisse

- `single-instance-runtime`: kein sicherer XDG-Laufzeitpfad
- `single-instance`: beschädigte, fremde, lebende oder nicht eindeutig veraltete Sperre
- `single-instance-recovery`: eindeutig veraltete Sperre wurde sicher entfernt

Beschädigte Sperren werden niemals nur aufgrund eines Verbindungsfehlers gelöscht.

## Ereignisjournal der Anwendung

```text
~/.local/state/multimodultool2026/logs/events.jsonl
```

Reguläre Datei, ein Hardlink, aktueller Eigentümer, keine Symlinks, Modus `0600`, JSONL und `fsync` je Eintrag. Private Pfade und typische Geheimnismuster werden reduziert.

Das Projekt-Aktionsjournal unter `.multimodultool2026/history/actions.jsonl` ist davon getrennt. Es dokumentiert reversible Dateioperationen und speichert ausschließlich relative Projektpfade.

## Diagnoseansicht

Die Diagnosezentrale liest das App-Ereignisjournal nur mit `O_RDONLY` und `O_NOFOLLOW`. Sie verändert, repariert, löscht oder exportiert es nicht automatisch.

## Grenzen

App-Journalrotation folgt `P3-003`. Prozessbasierte Kill-/Stromausfalltests, physische KDE-X11-/Wayland-Abnahme sowie reale Sonder-Mount- und ACL-Tests bleiben offen.
