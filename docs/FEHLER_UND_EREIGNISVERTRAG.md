# Fehler- und Ereignisvertrag – MULTIMODULTOOL2026

## Zweck

Diese Schicht übersetzt technische Fehler in einen eindeutigen, laienverständlichen und datensparsamen Sicherheitsbericht. Sie gilt für:

- unbehandelte Ausnahmen im Hauptthread,
- unbehandelte Ausnahmen in Worker-Threads,
- Ausnahmen während Qt-Ereignissen,
- Linux-, Manifest- und XDG-Fehler,
- Einstellungs-Recovery und blockierte Einstellungen,
- spätere Analyse-, Umbenennungs-, Verschiebe- und Löschfehler.

Ein Fehler darf nicht als unstrukturierter Traceback in der Oberfläche enden. Der betroffene Schritt wird kontrolliert beendet; abhängige Aktionen starten nicht.

## Sechs verpflichtende Nutzerfelder

Jeder globale Fehlerdialog und jede Konsolenausgabe enthält vollständig:

1. **Ursache** – was wurde erkannt?
2. **Folge** – welcher Schritt wurde blockiert oder beendet?
3. **Datenstand** – was blieb unverändert, was wurde gegebenenfalls isoliert?
4. **Lösung** – welche konkrete Korrektur ist möglich?
5. **Diagnosekennung** – eindeutige Kennung im Format `MMT-<KATEGORIE>-<UTC>-<ZUFALL>`.
6. **Sicherer nächster Schritt** – welcher geprüfte Schritt darf als Nächstes ausgeführt werden?

Keines dieser Felder darf leer sein oder ausschließlich aus einem technischen Fehlercode bestehen.

## Architektur

- `src/error_events.py` enthält das UI-unabhängige Ereignismodell, Diagnosekennungen, Geheimnisfilter, Exception-Hooks und das XDG-Ereignisjournal.
- `src/error_dialog.py` erzeugt den globalen Qt-Dialog mit allen sechs Pflichtfeldern.
- `src/main.py` übersetzt Bootstrap-, Manifest-, XDG-, Einstellungs- und Qt-Fehler in denselben Vertrag.
- `SafeOperationError` ist die verbindliche Fehlerklasse für spätere Dateioperationen.

## Ereignisjournal

Pfad:

```text
~/.local/state/multimodultool2026/logs/events.jsonl
```

Vertrag:

- Datei ist regulär und kein Symlink.
- Dateirechte sind `0600`.
- Jede Zeile ist ein vollständiges JSON-Objekt.
- Nach dem Schreiben erfolgt `fsync`.
- Das Journal wird nur im bereits validierten XDG-Logverzeichnis geöffnet.
- Ist das Journal unsicher oder nicht beschreibbar, wird der normale Start blockiert.

Eine spätere Rotation und Größenbegrenzung bleibt Aufgabe `P3-003`.

## Datenschutz und Reduktion

Vor Dialog und Journal werden:

- das Benutzerverzeichnis durch `~` ersetzt,
- typische Token-, Passwort-, Secret- und Bearer-Muster entfernt,
- Steuerzeichen entfernt,
- überlange technische Details begrenzt,
- private Dateiinhalte nicht übernommen.

Tokens, Passwörter, private Schlüssel und vollständige private Dateiinhalte sind im Ereignisjournal verboten.

## Unbehandelte Ausnahmen

- `sys.excepthook` erfasst unbehandelte Ausnahmen im Hauptthread.
- `threading.excepthook` erfasst unbehandelte Worker-Ausnahmen.
- eine sichere `QApplication.notify`-Schicht erfasst Qt-Ereignisausnahmen.
- Bootstrap-Ausnahmen werden durch `cli_entrypoint()` in einen vollständigen Fehlervertrag übersetzt.

Der Dialog wird im Qt-Hauptthread angezeigt. Kann Qt nicht geladen werden, erscheint derselbe Vertrag in der Konsole.

## Einstellungs-Recovery

Wurde `settings.json` aus Sicherung oder Standardwerten wiederhergestellt, erzeugt die zentrale Schicht ein Warnereignis. Es nennt:

- warum Recovery nötig war,
- welche Quelle aktiv ist,
- dass produktive Nutzerdaten unverändert blieben,
- welchen Status der Nutzer vor dem Fortsetzen prüfen soll.

## Failpoint-Matrix

`tests/test_settings_failpoints.py` simuliert Unterbrechungen an zehn Stellen:

1. vor temporärem Schreiben,
2. nach temporärem Schreiben,
3. vor Datei-`fsync`,
4. nach Datei-`fsync`,
5. vor Backup,
6. nach Backup,
7. vor `os.replace`,
8. nach `os.replace`,
9. vor Nachvalidierung,
10. nach Nachvalidierung.

Für jeden Punkt muss gelten:

- `settings.json` ist entweder die vollständige alte oder die vollständige neue Version,
- jede vorhandene Sicherung ist vollständig und schema-gültig,
- keine temporäre Datei bleibt zurück,
- der Failpoint wird eindeutig im Ergebnis genannt.

## Globaler Qt-Dialog

Der Dialog besitzt die Objektkennungen:

- `errorCause`
- `errorConsequence`
- `errorDataState`
- `errorSolution`
- `errorDiagnosticId`
- `errorNextStep`

Der Offscreen-GUI-Test prüft deren Existenz, Sichtbarkeit und Inhalt. Der Nutzer kann den vollständigen Bericht über **Diagnose kopieren** in die Zwischenablage übernehmen.

## Grenzen

- Das Ereignisjournal besitzt noch keine Rotation oder automatische Archivierung.
- Eine physische Abnahme unter KDE Plasma, X11, Wayland und mehreren DPI-Stufen bleibt erforderlich.
- Externe Crash-Dumps und Core-Dateien sind nicht Bestandteil dieses Vertrags.
- Produktive Dateioperationen bleiben bis Papierkorb, Undo und Wiederanlauf gesperrt.
