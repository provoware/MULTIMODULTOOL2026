# AGENTS.md – MULTIMODULTOOL2026

## Projektauftrag

Dieses Repository wird als modulares, laienoptimiertes, transparentes und datensicheres Linux-Desktop-Werkzeug entwickelt. Änderungen müssen verständlich, prüfbar, rückbaubar und mit dem aktuellen GitHub-Stand synchronisiert sein.

## Plattformvertrag

- ausschließlich Linux-Desktop
- primär Kubuntu 22.04/24.04, KDE Plasma, X11 und Wayland, x86-64
- keine Windows-, macOS-, Android-, iOS-, Browser- oder PWA-Sonderlogik
- Nicht-Linux-Systeme werden vor Datenänderungen blockiert

## XDG- und Dateirechtevertrag

- Programmcode und private Laufzeitdaten bleiben getrennt.
- Konfiguration, Daten, Cache, Status, Logs und Sicherungen liegen in validierten XDG-Benutzerpfaden.
- App-Verzeichnisse verwenden `0700`; private Dateien `0600`.
- Relative Pfade, Ziele im Quellbaum, Symlinks, falsche Eigentümer, zusätzliche Hardlinks und unsichere Dateitypen blockieren den Start.
- Rein lesende Prüfungen dürfen keine Dateien oder Verzeichnisse erzeugen.

## Einstellungsvertrag

- `settings.json` verwendet `schemaVersion` 1 und liegt ausschließlich im XDG-Konfigurationspfad.
- Schreiben benötigt Vorvalidierung, temporäre Datei, `fsync`, Nachvalidierung und atomaren Austausch.
- Letzte gültige Version bleibt als `settings.last-valid.json` erhalten.
- Failpoint-Matrix prüft alte oder neue vollständige Konfiguration an zehn Unterbrechungsstellen.

## Fehler- und Ereignisvertrag

Jeder globale Fehlerbericht nennt vollständig:

1. Ursache
2. Folge
3. Datenstand
4. Lösung
5. Diagnosekennung
6. sicheren nächsten Schritt

Unbehandelte Hauptthread-, Worker- und Qt-Ausnahmen sowie Manifest-, XDG-, Einstellungs-, Instanz- und spätere Dateioperationsfehler verwenden denselben Vertrag. Private Pfade und typische Geheimnismuster werden vor Dialog und Journal reduziert.

## Single-Instance-Vertrag

- Normale GUI-Starts verwenden genau eine primäre Linux-Instanz.
- Koordination erfolgt über privaten Unix-Domain-Socket unter `$XDG_RUNTIME_DIR/multimodultool2026`.
- Server prüft Linux-Peer-UID mittels `SO_PEERCRED`.
- Erlaubte Nachrichten: `activate` und `show-diagnostics`; optional eine validierte Diagnosekennung.
- Dateipfade, freie Argumentlisten, private Inhalte und beliebige Befehle sind verboten.
- Veraltete Sperren werden nur bei eindeutigem totem Prozess oder anderer Boot-Kennung entfernt.
- Beschädigte, fremde oder zweifelhafte Sperren bleiben unverändert und blockieren den Start mit vollständigem Fehlervertrag.
- Rein lesende CLI-Prüfmodi umgehen den GUI-Instanzschutz und bleiben parallel nutzbar.

## Diagnosevertrag

- Diagnosezentrale liest ausschließlich das lokale bereinigte Ereignisjournal.
- Filter erlaubt nur Schweregrad und Diagnosekennung.
- Einzelne bereinigte Berichte dürfen kopiert werden.
- Löschen, Upload, automatischer Export und Journalreparatur sind in der Diagnosezentrale verboten.
- Größen- und Datensatzgrenzen verhindern unkontrolliertes Laden.
- Ungültige Zeilen werden übersprungen und gemeldet, aber nie verändert.

## Verbindliche UI-Basis

Die visuelle Referenz unter `assets/ui-reference/` bleibt primäre Orientierung. Neun Zonen, linke Navigation, zentrale Arbeitsfläche, rechte Kontextleiste und untere Sicherheitsbereiche bleiben erhalten. Strukturelle Abweichungen benötigen ausdrückliche Nutzerfreigabe.

## Ablauf jeder Iteration

### Vorprüfung

- Ziel, Nutzen und Nutzerwirkung festlegen
- Ausgangscommit, Zielbranch, Konto und mindestens `push` prüfen
- Datenverlust-, Datenschutz-, Linux-, UI- und Rückfallrisiken bewerten
- TODO, Schwachstellen und Upgrade-Pool auf Doppelungen prüfen
- kleinsten vollständigen reversiblen Patch planen

### Umsetzung

- keine stillen Löschungen oder Überschreibungen
- keine neue Abhängigkeit ohne dokumentierten Grund
- produktive Dateiaktionen erst nach Vorschau, Validierung und Rückfallweg
- neue Funktionen in kleine testbare Linux-Module trennen
- keine Zugangsdaten, privaten Dateiinhalte oder unnötigen vollständigen Pfade protokollieren
- Fehler ausschließlich über die zentrale Ereignisschicht erklären

### Nachvalidierung

```bash
python3 -m src.main --validate-only
python3 tools/validate_repository.py
python3 -m unittest discover -s tests -v
python3 -m unittest tests.test_single_instance -v
python3 -m unittest tests.test_diagnostics_center -v
python3 -m unittest tests.test_settings_failpoints -v
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_gui_offscreen -v
```

Bei UI-/Laufzeitänderungen sind KDE, X11, Wayland, Fokus, Skalierung und abgeschnittene Inhalte zu bewerten. Nicht physisch geprüfte Bereiche werden offen benannt.

## Pflichtpflege jeder Iteration

Auf Änderungsbedarf prüfen und betroffene Dateien im selben Commit aktualisieren:

- `CHANGELOG.md`
- `ANLEITUNG_TOOL.md`
- `TODO.md`
- `SCHWACHSTELLEN.md`
- `UPGRADE_POOL.md`
- `ENTWICKLERDOKU.md`
- `README.md`
- `docs/GITHUB_ZUGRIFF.md`
- `docs/XDG_PFADVERTRAG.md`
- `docs/EINSTELLUNGSVERTRAG.md`
- `docs/FEHLER_UND_EREIGNISVERTRAG.md`
- `docs/SINGLE_INSTANCE_UND_DIAGNOSEVERTRAG.md`

Dokumente ohne Änderungsbedarf werden nicht künstlich verändert.

## Fortschrittsvertrag

- Quelle ist ausschließlich die Checkbox-Zahl in `TODO.md`.
- `- [x]` zählt erledigt, `- [ ]` offen.
- Fortschritt = gerundet `erledigt / gesamt × 100`.
- README und TODO müssen exakt übereinstimmen.
- Eine Aufgabe gilt erst nach Umsetzung, Abnahme, Dokumentation, grünem CI-Lauf und GitHub-Commit als erledigt.

## GitHub-Pflicht

Jede abgeschlossene Iteration wird auf `provoware/MULTIMODULTOOL2026` übertragen. Abschluss benötigt Zielbranch, Commit-SHA, grüne relevante Prüfungen, konsistente Fortschrittswerte, bekannte Grenzen, nächsten technischen Schritt und risikoarme Alternative. Tokens oder GitHub-Geheimnisse dürfen niemals im Repository liegen.
