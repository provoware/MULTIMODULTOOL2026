# Browser-Freigabeprotokoll 2026-07-16

Dieses Protokoll ist die ausfüllbare Vorlage für die echte Freigabeprüfung. Es ersetzt keine Prüfung: Erst wenn alle Prüffelder mit Datum, Browser, Ergebnis und kurzer Beobachtung ausgefüllt sind, darf die Browserfreigabe als erledigt markiert werden.

## Regeln für die Durchführung

- Nur kleine, nicht private Testdaten verwenden.
- App über `./scripts/start-local.sh` starten, damit Moduldateien über den lokalen Server geladen werden.
- Pro Browser eine frische sichtbare Sitzung nutzen oder vorhandene Testdaten vorher bewusst sichern.
- Fehler nicht beschönigen: kurze Meldung, betroffener Schritt und nächster Versuch reichen aus.
- Screenshots sind hilfreich, aber ein kurzes Prüfprotokoll mit Datum und Ergebnis genügt.

## Ergebnisübersicht

| Bereich | Status | Kurznotiz |
| --- | --- | --- |
| Chromium-Start | offen | Noch nicht geprüft. |
| Firefox-Start | offen | Noch nicht geprüft. |
| Kontrast und Fokus | offen | Noch nicht geprüft. |
| Tastaturbedienung | offen | Noch nicht geprüft. |
| Speicherprüfung | offen | Noch nicht geprüft. |
| JSON-Import | offen | Noch nicht geprüft. |
| Backup-Wiederherstellung | offen | Noch nicht geprüft. |
| Exportdownload | offen | Noch nicht geprüft. |

## Prüfschritte Chromium

| Schritt | Erwartung | Ergebnis |
| --- | --- | --- |
| `./scripts/start-local.sh` öffnet die App in Chromium. | Startansicht erscheint ohne technische Fehlermeldung. | offen |
| Startübersicht ansehen. | Speicherort, Datum/Uhrzeit, letzte Schritte und Einstellungen sind verständlich sichtbar. | offen |
| Kontrast und Fokus prüfen. | Kleine Texte, Statuschips, Eingabefelder und Fokusrahmen sind gut erkennbar. | offen |
| Tastaturbedienung prüfen. | Modulkarte per Eingabe/Leertaste öffnen; platziertes Modul per Pfeiltasten, Pos1 und Ende bewegen. | offen |
| Einstellungen → **Speicher prüfen** ausführen. | Meldung nennt Schreibtest, Speicher-Schätzung, Backup-Lesetest und dass Nutzdaten unverändert bleiben. | offen |

## Prüfschritte Firefox

| Schritt | Erwartung | Ergebnis |
| --- | --- | --- |
| `./scripts/start-local.sh` öffnet die App in Firefox. | Startansicht erscheint ohne technische Fehlermeldung. | offen |
| Startübersicht ansehen. | Speicherort, Datum/Uhrzeit, letzte Schritte und Einstellungen sind verständlich sichtbar. | offen |
| Kontrast und Fokus prüfen. | Kleine Texte, Statuschips, Eingabefelder und Fokusrahmen sind gut erkennbar. | offen |
| Tastaturbedienung prüfen. | Modulkarte per Eingabe/Leertaste öffnen; platziertes Modul per Pfeiltasten, Pos1 und Ende bewegen. | offen |
| Einstellungen → **Speicher prüfen** ausführen. | Meldung nennt Schreibtest, Speicher-Schätzung, Backup-Lesetest und dass Nutzdaten unverändert bleiben. | offen |

## Datenprüfung mit kleinen Testdaten

| Schritt | Erwartung | Ergebnis |
| --- | --- | --- |
| Kleinen JSON-Import starten. | App prüft Größe und Inhalt vor dem Speichern und zeigt eine verständliche Bestätigung. | offen |
| Import abbrechen. | Meldung nennt Abbruchgrund, Lösung und dass nichts verändert wurde. | offen |
| Import mit Testdaten bestätigen. | Vor dem Speichern wird ein Backup-Hinweis angezeigt; danach ist der Teststand sichtbar. | offen |
| Backup-Wiederherstellung mit Testdaten prüfen. | Wiederherstellung verlangt Bestätigung und meldet Erfolg oder verständlichen Fehler. | offen |
| Exportdownload ausführen. | Datei wird mit nachvollziehbarem Namen heruntergeladen; Erfolgsmeldung ist sichtbar. | offen |

## Abschlussentscheidung

Die Freigabe bleibt offen, solange ein Prüfschritt den Status `offen` oder `fehlgeschlagen` hat.

Nach vollständiger Prüfung hier eintragen:

- Datum/Uhrzeit:
- Prüfer:
- Chromium-Version:
- Firefox-Version:
- Gesamtergebnis:
- Bekannte Restgrenzen:
