# Release-Checkliste

Diese Checkliste beschreibt die kleinste sichere Freigabeprüfung für die lokale Single-File-App. Sie ist bewusst kurz gehalten, damit eine Version vor einer Weitergabe nachvollziehbar geprüft werden kann.

## 1. Vorbereitung

- Aktuellen Stand in `README.md` und `todo.txt` prüfen.
- Sicherstellen, dass keine privaten Daten in `data/`, `imports/`, `exports/` oder `logs/` liegen.
- Offene Risiken aus `todo.txt` lesen und entscheiden, ob sie die Freigabe blockieren.

## 2. Lokaler Start

- App über `./scripts/start-local.sh` öffnen.
- Alternativ die HTML-Datei direkt im Browser öffnen, wenn kein lokaler Server benötigt wird.
- Prüfen, ob die Startansicht ohne Fehlermeldung sichtbar ist.

## 3. Kernfunktionen

- Ein aktives Modul per Tastatur öffnen: Modulkarte fokussieren, Eingabe oder Leertaste drücken.
- Ein platziertes Modul per Tastatur verschieben: Panel fokussieren, Pfeiltasten für Nachbarfelder oder Pos1/Ende für erstes/letztes Rasterfeld nutzen.
- Ein kleines Textelement anlegen, ändern und wieder entfernen.
- Eine Testnotiz oder Aufgabe speichern und nach dem Neuladen wiederfinden.
- Export mit Testdaten ausführen und prüfen, ob eine verständliche Erfolgsmeldung erscheint.
- Import nur mit kleinen, geprüften Testdaten ausführen.

## 4. Daten- und Backup-Sicherheit

- In den Einstellungen **Speicher prüfen** ausführen; die Meldung muss Schreibtest, Speicher-Schätzung, Backup-Zustand und den Hinweis „Nutzdaten bleiben unverändert“ sinngemäß enthalten.
- Vor Import oder Wiederherstellung prüfen, ob ein Backup-Hinweis angezeigt wird.
- Bei absichtlich ungültigen Daten muss die App verständlich erklären, was passiert ist und was der Nutzer tun kann.
- Keine stillen Überschreibungen akzeptieren.

## 5. Modul- und Manifestprüfung

- Bei Änderungen unter `modules/` oder `manifests/` die Manifestprüfung ausführen.
- Ungültige Module dürfen nicht still übernommen werden.
- Fehlermeldungen sollen einfach sagen, welches Modul betroffen ist und wie weiter geprüft werden kann.

## 6. Sicht- und Kontrastprüfung

Stand 2026-07-16: Die App wurde für Tastaturplatzierung und sichtbare Fokuszustände vorbereitet. Eine echte Chromium-/Firefox-Sichtprüfung muss auf einer Browserinstallation nachgeholt werden; im Container waren Snap-Browser und Playwright-Browserdownloads blockiert. Die vollständige Speicher-/Importprüfung bleibt ein eigener Freigabeschritt und darf nicht durch diese Sichtprüfung ersetzt werden.

## 7. Freigabeentscheidung

Eine lokale Freigabe ist möglich, wenn:

- die App startet,
- direkt betroffene Prüfungen bestanden sind,
- bekannte Grenzen in `todo.txt` stehen,
- keine privaten Daten im Commit enthalten sind,
- und die Änderung ohne Build-Schritt nutzbar bleibt.

Wenn einer dieser Punkte offen ist, wird keine Freigabe markiert. Stattdessen wird der Grund in `todo.txt` dokumentiert.
