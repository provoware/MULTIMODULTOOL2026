# JSON- und Config-Reparaturhilfe

Diese kurze Hilfe ist für fehlerhafte Dashboard-Importe gedacht. Sie verändert keine Nutzdaten und dient nur als sichere Prüfliste.

## Häufige Ursachen

1. Die Datei ist leer oder nicht vollständig kopiert.
2. Ein Komma zwischen zwei Einträgen fehlt oder ist zu viel.
3. Schlüssel oder Texte stehen nicht in doppelten Anführungszeichen.
4. Geschweifte Klammern `{}` oder eckige Klammern `[]` sind nicht geschlossen.
5. Die oberste Ebene ist keine Konfiguration als Objekt.

## Sicherer Reparaturablauf

1. Vor der Reparatur die Originaldatei kopieren.
2. Datei als reine Textdatei öffnen.
3. Prüfen, ob die Datei mit `{` beginnt und mit `}` endet.
4. Fehlermeldung der App lesen und die genannte Stelle zuerst prüfen.
5. Nach jeder kleinen Korrektur erneut importieren.
6. Wenn der Import weiter scheitert, nur gültige Bereiche in eine neue Datei kopieren.

## Minimal gültige Struktur

Eine reparierte Config braucht mindestens ein Objekt. Fehlende App-Bereiche ergänzt das Tool beim Import mit sicheren Standardwerten.

Siehe Beispiel: `imports/reparatur-json-config-beispiel.json`.
