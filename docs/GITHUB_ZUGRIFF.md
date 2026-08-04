# GitHub-Zugriff – MULTIMODULTOOL2026

## Aktueller geprüfter Zustand

Stand: 2026-08-04

- verbundenes GitHub-Konto: `provoware`
- Repository: `provoware/MULTIMODULTOOL2026`
- geprüfte Berechtigung: **Admin-Rechte**
- Zielbranch abgeschlossener Iterationen: `main`

## Was dauerhaft möglich ist

Die GitHub-App kann auf dieses Repository schreiben, solange sie weiterhin installiert und autorisiert ist, die Repository-Freigabe nicht entzogen wird, Branch-Regeln den Schreibweg zulassen und die Verbindung im jeweiligen Chat verfügbar ist.

## Was nicht im Repository verankert werden kann

GitHub-Rechte entstehen außerhalb des Repository-Inhalts. Eine Datei, ein Commit oder ein Skript kann keine dauerhaften Admin- oder Schreibrechte erzeugen oder garantieren.

Zugangsdaten werden **nicht im Repository gespeichert**. Verboten sind insbesondere persönliche Zugriffstokens, OAuth- oder GitHub-App-Tokens, private Schlüssel, Passwörter und Sessiondaten.

## Verbindliche Prüfung vor Schreibaktionen

Vor jeder GitHub-Iteration werden geprüft:

1. angemeldetes Konto,
2. exaktes Repository,
3. aktueller Zielbranch,
4. erforderliche Berechtigungsstufe,
5. aktueller Ausgangscommit.

Für normale Dateiänderungen ist mindestens `push` erforderlich. Für destruktive Repository-Aktionen muss `admin` bestätigt sein.

## Verhalten bei fehlendem Zugriff

- keine Änderung wird als erfolgreich bezeichnet,
- keine erfundene Commit-SHA wird ausgegeben,
- der blockierende Punkt wird genannt,
- Projektdaten werden nicht verändert,
- die GitHub-App kann erneut verbunden oder für das Repository freigegeben werden.

## Sicherheitsfazit

Die aktuelle Verbindung besitzt Admin-Rechte. Diese Rechte sind an GitHub-Konto und GitHub-App gebunden, nicht an den Quellcode. Der sichere Weg ist: externe Rechte beibehalten, vor jeder Iteration prüfen und niemals Zugangsdaten committen.
