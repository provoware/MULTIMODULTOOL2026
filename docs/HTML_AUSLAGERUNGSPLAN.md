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

Als nächster Code-Schritt eignet sich ein lesender Modul-Renderer-Prototyp, der nur `module.html` und `module.css` anzeigt. Modul-JavaScript wird dabei noch nicht ausgeführt.
