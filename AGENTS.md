# AGENTS.md – MULTIMODULTOOL2026

## Projektauftrag

Dieses Repository wird als modulares, laienoptimiertes, transparentes und datensicheres Linux-Desktop-Werkzeug entwickelt. Änderungen müssen verständlich, prüfbar, rückbaubar und mit dem aktuellen GitHub-Stand synchronisiert sein.

## Verbindlicher Plattformvertrag

1. Entwicklung, Tests, Dokumentation, Paketierung und Releases richten sich ausschließlich an Linux-Desktop-Systeme.
2. Primäre Zielsysteme sind Kubuntu 22.04 LTS und Kubuntu 24.04 LTS auf x86-64.
3. KDE Plasma unter X11 und Wayland muss berücksichtigt werden.
4. Windows, macOS, Android, iOS, Browser, PWA und Web-App sind ausgeschlossen.
5. Nicht-Linux-Systeme werden verständlich blockiert; Daten bleiben unverändert.
6. XDG-Verzeichnisse, POSIX-Pfade und sichere Linux-Dateirechte haben Vorrang.

## Verbindlicher XDG-Pfadvertrag

- Programmcode und private Laufzeitdaten bleiben getrennt.
- Konfiguration, Daten, Cache, Status, Logs und Sicherungen liegen ausschließlich in validierten XDG-Benutzerpfaden.
- App-Verzeichnisse verwenden `0700`.
- Relative Pfade, Ziele im Quellbaum, Symlinks, Doppelziele und unbeschreibbare Ziele blockieren den Start.
- Rein lesende Prüfungen dürfen keine XDG-Verzeichnisse anlegen.
- Details: `docs/XDG_PFADVERTRAG.md`.

## Verbindlicher Einstellungsvertrag

- Einstellungen liegen ausschließlich als `settings.json` im validierten XDG-Konfigurationspfad.
- `schemaVersion` 1, unbekannte Felder und inkompatible Werte werden blockiert.
- Aktive Datei und Sicherung verwenden `0600`.
- Jeder Schreibvorgang benötigt Vorvalidierung, temporäre Datei, `fsync`, Nachvalidierung und atomaren Austausch.
- Die letzte gültige Version bleibt als `settings.last-valid.json` erhalten.
- Beschädigte Dateien werden isoliert und automatisch wiederhergestellt.
- `--validate-only` und `--settings-only` bleiben rein lesend.
- Details: `docs/EINSTELLUNGSVERTRAG.md`.

## Verbindlicher Fehler- und Ereignisvertrag

- Unbehandelte Hauptthread-, Worker- und Qt-Ereignisausnahmen werden zentral erfasst.
- XDG-, Manifest-, Einstellungs-Recovery- und spätere Dateioperationsfehler verwenden denselben Ereignisvertrag.
- Jeder Dialog nennt **Ursache**, **Folge**, **Datenstand**, **Lösung**, **Diagnosekennung** und **Sicherer nächster Schritt**.
- Leere Pflichtfelder, unkommentierte Tracebacks oder reine Farbcodes sind unzulässig.
- Ereignisse liegen ausschließlich im validierten XDG-Logpfad; `events.jsonl` verwendet `0600` und darf kein Symlink sein.
- Private Pfade und typische Geheimnismuster werden vor Ausgabe und Logging reduziert.
- Spätere Dateioperationen verwenden `SafeOperationError` oder eine gleichwertige zentrale Übersetzung.
- Einstellungen werden mit der vollständigen Failpoint-Matrix vor/nach temporärem Schreiben, `fsync`, Backup, `os.replace` und Nachvalidierung geprüft.
- Details: `docs/FEHLER_UND_EREIGNISVERTRAG.md`.

## Verbindliche UI-Basis

Die Datei `assets/ui-reference/multimodultool2026-ui-layout-reference-2026.webp` ist die primäre visuelle Orientierung.

1. Grundaufbau und räumliche Anordnung bleiben erhalten.
2. Inhalte, Bezeichnungen, Icons, Farben und Funktionen dürfen projektbezogen angepasst werden.
3. Strukturelle Abweichungen benötigen ausdrückliche Nutzerfreigabe.
4. Jede UI-Iteration wird gegen `standards/UI_LAYOUT_STANDARD_2026.md` und `layout-manifest.json` geprüft.
5. Projektname ist ausschließlich `MULTIMODULTOOL2026`.

## GitHub-Zugriffsvertrag

- Schreibrechte entstehen durch die autorisierte GitHub-App und das angemeldete Konto.
- Tokens, Passwörter, private Schlüssel oder App-Geheimnisse werden niemals im Repository gespeichert.
- Vor jeder Schreibiteration werden Repository, Zielbranch, Konto und mindestens `push` geprüft.
- Destruktive Repository-Aktionen benötigen zusätzlich `admin`.
- Fehlender Zugriff blockiert die Iteration; kein erfundener Push- oder Commit-Erfolg.
- Details: `docs/GITHUB_ZUGRIFF.md`.

## Verbindlicher Ablauf jeder Iteration

### Vorprüfung

- Ziel, Nutzen und sichtbare Nutzerwirkung festlegen.
- Ausgangscommit, Zielbranch, Konto und Rechte prüfen.
- betroffene Dateien und exakte Änderungsbereiche bestimmen.
- Datenverlust-, Bedien-, Datenschutz-, Linux-, Fehler- und Rückfallrisiken bewerten.
- `TODO.md`, `SCHWACHSTELLEN.md` und `UPGRADE_POOL.md` auf Doppelungen und Abhängigkeiten prüfen.
- kleinsten vollständigen, nachvollziehbaren und reversiblen Patch planen.

### Umsetzung

- keine stillen Löschungen oder Überschreibungen
- keine globalen Umformatierungen ohne direkten Nutzen
- keine neue Abhängigkeit ohne dokumentierten Grund
- keine Nicht-Linux-Sonderlogik
- produktive Dateiaktionen nur nach Vorschau, Validierung und Rückfallweg
- neue Funktionen in kleine, testbare Module trennen
- keine Zugangsdaten oder privaten Dateiinhalte in Dateien, Logs oder Commits
- Fehler nicht direkt in Widgets behandeln, sondern über die zentrale Ereignisschicht übersetzen

### Nachvalidierung

- `python3 -m src.main --validate-only`
- bei Einstellungen: `python3 -m src.main --settings-only`
- `python3 tools/validate_repository.py`
- `python3 -m unittest discover -s tests -v`
- bei UI: `QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_gui_offscreen -v`
- bei Transaktionen: `tests/test_settings_failpoints.py`
- Fehlerdialog auf alle sechs Pflichtfelder prüfen
- Ergebnis, Restfehler und nicht geprüfte Bereiche offen dokumentieren

## Pflichtpflege der Dokumentation

In jeder Iteration werden folgende Dateien auf Änderungsbedarf geprüft; betroffene Dateien werden im selben Commit aktualisiert:

- `CHANGELOG.md`
- `ANLEITUNG_TOOL.md`
- `TODO.md`
- `SCHWACHSTELLEN.md`
- `UPGRADE_POOL.md`
- `ENTWICKLERDOKU.md`
- `docs/GITHUB_ZUGRIFF.md`
- `docs/XDG_PFADVERTRAG.md`
- `docs/EINSTELLUNGSVERTRAG.md`
- `docs/FEHLER_UND_EREIGNISVERTRAG.md`
- `README.md` mit **Entwicklungsfortschritt**, **Erledigte Punkte**, **Offene Punkte** und **Gesamtpunkte** aus `TODO.md`

Dokumente ohne Änderungsbedarf werden nicht künstlich verändert.

## Fortschrittsvertrag

- Quelle ist ausschließlich die Zahl der Checkbox-Aufgaben in `TODO.md`.
- `- [x]` zählt erledigt, `- [ ]` offen.
- Entwicklungsfortschritt = gerundet `erledigt / gesamt × 100`.
- README-Werte müssen exakt übereinstimmen.
- Eine Aufgabe gilt erst nach Umsetzung, Abnahme, Tests, Dokumentation und GitHub-Commit als erledigt.

## GitHub-Pflicht

Jede vollständig abgeschlossene Iteration wird auf `provoware/MULTIMODULTOOL2026` übertragen. Abschluss setzt vollständigen Patch, grüne relevante Prüfungen, aktualisierten Zielbranch, bestätigten Commit-SHA und konsistente README-/TODO-Werte voraus.

## Daten- und Bedienungssicherheit

- riskante Aktionen mit Ziel, Umfang, Wirkung und Rückfallweg anzeigen
- Undo, Papierkorb oder Backup vor destruktiven Eingriffen vorsehen
- Fehler in einfacher Sprache mit vollständigem Datenstand erklären
- Status nie ausschließlich über Farbe vermitteln
- absolute Benutzerpfade nicht in portablen Projektdateien speichern
- keine privaten Dateiinhalte oder Geheimnisse protokollieren

## Iterationsabschluss

Jeder Abschluss nennt mindestens:

- Commit-SHA und Zielbranch
- geänderte Dateien
- Prüfungen und Ergebnis
- Entwicklungsfortschritt
- erledigte und offene Punkte
- Restschwachstellen
- direkt folgenden technischen Entwicklungsschritt
- Alternative mit hohem Nutzen und geringem Risiko
