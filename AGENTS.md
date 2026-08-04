# AGENTS.md – MULTIMODULTOOL2026

## Projektauftrag

Dieses Repository wird als modulares, laienoptimiertes, transparentes und datensicheres Linux-Desktop-Werkzeug entwickelt. Änderungen müssen verständlich, prüfbar, rückbaubar und mit dem aktuellen GitHub-Stand synchronisiert sein.

## Verbindlicher Plattformvertrag

1. Entwicklung, Tests, Dokumentation, Paketierung und Releases richten sich ausschließlich an Linux-Desktop-Systeme.
2. Primäre Zielsysteme sind Kubuntu 22.04 LTS und Kubuntu 24.04 LTS auf x86-64.
3. KDE Plasma unter X11 und Wayland muss berücksichtigt werden.
4. Windows, macOS, Android, iOS, Browser, PWA und Web-App sind nicht Teil des Projektumfangs.
5. Keine plattformübergreifenden Kompatibilitätsschichten, Installer oder Sonderpfade ohne ausdrückliche Nutzerfreigabe.
6. Nicht-Linux-Systeme werden beim Start verständlich blockiert; es werden keine Daten verändert.
7. Linux-native Standards wie XDG-Verzeichnisse, POSIX-Pfade, Desktop-Dateien und sichere Dateirechte haben Vorrang.

## Verbindliche UI-Basis

Die Datei `assets/ui-reference/multimodultool2026-ui-layout-reference-2026.webp` ist die primäre visuelle Orientierung.

1. Grundaufbau und räumliche Anordnung bleiben erhalten.
2. Projektbezogene Inhalte, Bezeichnungen, Icons, Farben und Funktionen dürfen angepasst werden.
3. Größere Abweichungen an Navigation, Zonenfolge oder Hauptanordnung erfolgen nur nach ausdrücklichem Nutzerwunsch.
4. Jede UI-Iteration wird gegen `standards/UI_LAYOUT_STANDARD_2026.md` und `layout-manifest.json` geprüft.
5. Verwendeter Projektname ist ausschließlich `MULTIMODULTOOL2026`.

## GitHub-Zugriffsvertrag

- Schreibrechte werden ausschließlich durch die autorisierte GitHub-App und das angemeldete GitHub-Konto bereitgestellt.
- Tokens, Passwörter, private Schlüssel oder App-Geheimnisse werden niemals im Repository gespeichert.
- Vor jeder Schreibiteration werden Repository, Zielbranch, angemeldetes Konto und mindestens `push`-Berechtigung geprüft.
- Für destruktive Repository-Aktionen wird zusätzlich `admin` geprüft.
- Ein fehlgeschlagener oder entzogener Zugriff blockiert die Iteration; es wird niemals ein erfolgreicher Push behauptet.
- Repository-Dateien können Berechtigungen dokumentieren und prüfen, aber keine GitHub-Rechte dauerhaft erzwingen.
- Verbindliche Erläuterung: `docs/GITHUB_ZUGRIFF.md`.

## Verbindlicher Ablauf jeder Iteration

### Vorprüfung

- Ziel, Nutzen und sichtbare Nutzerwirkung festlegen.
- Ausgangscommit und Zielbranch prüfen.
- GitHub-Konto und erforderliche Repository-Berechtigung prüfen.
- betroffene Dateien und exakte Änderungsbereiche bestimmen.
- Datenverlust-, Bedien-, Datenschutz-, Linux-Kompatibilitäts- und Rückfallrisiken bewerten.
- `TODO.md`, `SCHWACHSTELLEN.md` und `UPGRADE_POOL.md` auf Doppelungen und Abhängigkeiten prüfen.
- kleinsten vollständigen, nachvollziehbaren und reversiblen Patch planen.

### Umsetzung

- keine stillen Löschungen oder Überschreibungen
- keine globalen Umformatierungen ohne direkten Nutzen
- keine neuen Abhängigkeiten ohne dokumentierten Grund
- keine Windows-, macOS-, Android-, iOS- oder Browser-Sonderlogik einbauen
- manuelle Eingaben vermeiden, wenn sichere Auswahlfelder, Schalter oder Dialoge möglich sind
- produktive Dateiaktionen erst nach Vorschau, Validierung und definiertem Rückfallweg
- neue Funktionen in kleine, testbare Linux-Module trennen
- keine Zugangsdaten oder GitHub-Tokens in Dateien, Logs oder Commits aufnehmen

### Nachvalidierung

- direkt betroffene Syntax, Formate und Funktionen prüfen
- `python3 -m src.main --validate-only` ausführen
- `python3 tools/validate_repository.py` ausführen
- relevante Unit-Tests ausführen
- auf Kubuntu, KDE Plasma, X11 und Wayland bezogene Auswirkungen prüfen, wenn Laufzeit oder UI betroffen sind
- Layouttreue, Fokus, Kontrast, Skalierung und abgeschnittene Elemente prüfen, wenn UI betroffen ist
- Ergebnis, Restfehler und nicht geprüfte Bereiche offen dokumentieren

## Pflichtpflege der Dokumentation

In jeder Iteration werden alle folgenden Dateien auf Änderungsbedarf geprüft. Betroffene Dateien müssen im selben Entwicklungsstand aktualisiert werden:

- `CHANGELOG.md`: bei jeder Änderung an Code, Verhalten, Struktur, Prüfung, Plattformvertrag oder Dokumentation ergänzen
- `ANLEITUNG_TOOL.md`: bei Änderungen an Linux-Installation, Start, Bedienung, Dialogen oder Fehlerbehebung aktualisieren
- `TODO.md`: erledigte Aufgaben markieren, neue Aufgaben entdoppeln, priorisieren und mit Abhängigkeit, Abnahmekriterium sowie Risiko ergänzen
- `SCHWACHSTELLEN.md`: Fehler, Linux-Kompatibilitätsgrenzen, Sicherheitsrisiken und technische Schulden aktualisieren
- `UPGRADE_POOL.md`: nur Linux-bezogene optionale Ideen bewerten
- `ENTWICKLERDOKU.md`: bei Änderungen an Architektur, Schnittstellen, Linux-Datenfluss, Build, Tests oder Abhängigkeiten aktualisieren
- `docs/GITHUB_ZUGRIFF.md`: bei Änderungen an Zugriffsmodell, App-Installation, Berechtigungsprüfung oder Sicherheitsregeln aktualisieren
- `README.md`: Fortschrittsblock mit **Entwicklungsfortschritt**, **Erledigte Punkte**, **Offene Punkte** und **Gesamtpunkte** aus `TODO.md` aktualisieren

Ist bei einem Dokument keine Änderung nötig, wird es nicht künstlich verändert.

## Fortschrittsvertrag

- Fortschrittsquelle ist ausschließlich die Zahl der Checkbox-Aufgaben in `TODO.md`.
- `- [x]` zählt als erledigt, `- [ ]` zählt als offen.
- Entwicklungsfortschritt = gerundeter Wert `erledigt / gesamt × 100`.
- README-Werte müssen exakt mit `TODO.md` übereinstimmen.
- Eine Aufgabe gilt nur als erledigt, wenn Umsetzung, Abnahmekriterium, Prüfung, Dokumentation und GitHub-Commit vorliegen.
- Sammelaufgaben ohne objektives Abnahmekriterium sind unzulässig.

## GitHub-Pflicht

Jede vollständig abgeschlossene Iteration wird auf `provoware/MULTIMODULTOOL2026` übertragen.

Eine Iteration ist erst abgeschlossen, wenn:

- der vollständige Patch enthalten ist
- die direkt relevante Validierung grün ist
- der Zielbranch erfolgreich aktualisiert wurde
- der neue Commit-SHA bestätigt wurde
- README und TODO konsistent sind
- Prüfergebnis, offene Punkte und bekannte Grenzen ausgegeben wurden

Keine Abschlussbehauptung bei fehlgeschlagenem Push, unklarem Branchzustand, ungeprüften Änderungen oder inkonsistenter Dokumentation.

## Daten- und Bedienungssicherheit

- riskante Aktionen mit Ziel, Umfang, Wirkung und Rückfallmöglichkeit anzeigen
- Undo, Papierkorb oder Backup vor destruktiven Eingriffen vorsehen
- Fehler in einfacher Sprache mit Ursache, Folge, Lösung und unverändertem Datenstand erklären
- Status, Fortschritt und Ergebnis sichtbar halten
- Status nie ausschließlich über Farbe vermitteln
- absolute Benutzerpfade nicht dauerhaft in portablen Projektdateien speichern
- XDG-Verzeichnisse und Linux-Dateirechte kontrolliert verwenden
- keine privaten Dateiinhalte, Geheimnisse oder unnötigen vollständigen Pfade protokollieren

## Iterationsabschluss

Jeder Entwicklungsabschluss nennt mindestens:

- Commit-SHA und Zielbranch
- geänderte Dateien
- ausgeführte Prüfungen und deren Ergebnis
- Entwicklungsfortschritt in Prozent
- Anzahl erledigter und offener Punkte
- bekannte Restschwachstellen
- direkt folgenden technischen Entwicklungsschritt
- alternative Verbesserung mit hohem Nutzen und geringem Risiko
