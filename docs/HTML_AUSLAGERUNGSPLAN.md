# HTML-Auslagerungsplan

Stand: 2026-07-16

## Ziel

Die große Datei `dashboard-studio-ultimate-pro-v3.1.0.html` bleibt der stabile Startpunkt. Auslagerung passiert nur schrittweise und erst, wenn der betroffene Bereich einzeln geprüft werden kann.

## Schnittreihenfolge

1. **Styles**: zusammenhängende CSS-Blöcke ohne JavaScript-Abhängigkeit vorbereiten.
2. **Standarddaten**: statische Modulvorlagen und Hilfetexte in klar benannte Datenblöcke trennen.
3. **Speicherlogik**: Lesen, Schreiben, Backup und Import getrennt prüfbar halten.
4. **Modul-Renderer**: reine Anzeige zuerst auslagern; Speichern und Import bleiben bis zur separaten Prüfung in der App.
5. **Hilfsfunktionen**: kleine, reine Funktionen mit bestehenden Tests absichern.

## Sicherheitsgrenzen

- Keine Umbenennung der Startdatei.
- Kein Build-Schritt.
- Keine globale Umformatierung.
- Kein Entfernen alter Datenpfade ohne vorherige Backup- und Importprüfung.
- Jede Auslagerung muss einen Rückbaupfad nennen.

## Nächster kleinster Schritt

Als nächster Code-Schritt eignet sich eine Bereichstrennung der Hauptdatei ohne Build-System:

1. `assets/app.css` für globale Styles vorbereiten und die alte Inline-Fassung erst nach Sichtprüfung entfernen.
2. `data/default-modules.json` für Standardmodule und Vorlagen vorbereiten, aber die Haupt-App zunächst weiter als Rückfallquelle behalten.
3. Kleine reine JavaScript-Hilfen nach `assets/app-helpers.js` verschieben, sobald die vorhandenen Hilfslogik-Tests sie direkt prüfen können.

## Antwort zur Aufsplitterung

Ja, die Haupt-Modul-HTML kann nach Bereichen aufgeteilt werden. Sicher ist aber nur ein stufenweiser Schnitt: zuerst Styles, dann reine Daten, dann kleine getestete Hilfsfunktionen und erst danach Modul-Renderer. Die Startdatei bleibt dabei `dashboard-studio-ultimate-pro-v3.1.0.html`, damit ein Rückbau ohne Datenverlust möglich bleibt.
