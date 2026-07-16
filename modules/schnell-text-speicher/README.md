# Schnell-Text-Speicher

Dieses Modul sammelt kurze, wiederverwendbare Textbausteine. Die Bausteine sind bewusst knapp formuliert, damit sie schnell kopiert, angepasst und in eigenen Arbeitsabläufen genutzt werden können.

## Textbausteine

### Coding

Prüfe die Änderung in kleinen Schritten: erst Eingaben absichern, dann die kleinste passende Funktion ändern, danach nur die direkt betroffene Ausgabe testen. Vermeide globale Umbauten, solange der Fehler lokal begrenzt ist.

Formuliere vor dem Patch eine kurze Risikozeile: Welche Daten könnten betroffen sein, wie wird ein Abbruch erkannt und welche Prüfung zeigt danach, dass nichts Nebenliegendes beschädigt wurde?

Erstelle vor einer Freigabe eine knappe Prüfliste: Start, Speichern, Laden, Import, Export, Fehlermeldung und Rückbau. Markiere jeden Punkt mit bestanden, offen oder blockiert.

Verbessere eine Nutzer-Meldung so, dass sie vier Fragen beantwortet: Was ist passiert, warum ist es passiert, was soll ich tun und wurde etwas gespeichert oder verändert?

Vergleiche ähnliche Meldungen paarweise, bevor du Code änderst: Export, Import und Backup sollen gleich klar sein, aber nur echte Lücken bekommen neue Wörter.

Dokumentiere nach jeder kleinen Änderung genau eine Begründung: Welches Risiko wurde gesenkt, welche Datei wurde berührt und welche Prüfung reicht dafür aus?

Erstelle eine Platzhalter-Inventur: Suche nach TODO, FIXME, Dummy, Stub, Beispieltexten und leeren Zuständen. Bearbeite nichts sofort, sondern schreibe zuerst eine nummerierte Liste mit Risiko und Prüfschritt.

Prüfe gekoppelte Statusangaben automatisch: Lies beide Quellen, validiere Wertebereich und Format und brich mit einer klaren Meldung ab, sobald die Angaben voneinander abweichen.

### Prompting

Ermittle Platzhalter nicht nur nach dem Wort „TODO“, sondern auch nach Beispielen, leeren Zuständen, Dummy-Daten und Stubs. Gib je Fundstelle Datei, Zweck, Risiko und nächsten Schritt an.

Beschreibe zuerst Ziel, gewünschtes Ausgabeformat, Eingabedaten und Ausschlüsse. Bitte danach um Rückfragen nur dann, wenn ohne Antwort ein falsches Ergebnis wahrscheinlich wäre.

Nutze diese Struktur: Rolle, Aufgabe, Kontext, harte Grenzen, gewünschte Prüfschritte und Ausgabeformat. Ergänze am Ende: Wenn etwas unsicher ist, nenne Annahme und Risiko statt zu raten.

Bitte prüfe meinen Entwurf wie ein Release-Reviewer: Nenne zuerst blockierende Fehler, dann kleine Verbesserungen und zuletzt genau die Punkte, die unverändert bleiben sollten.

Formuliere eine Fehlermeldung in einfacher Sprache. Nutze die Reihenfolge: Ereignis, Grund, nächster Schritt, Speicherstatus. Vermeide Schuldzuweisungen und unklare Wörter wie „Fehler 1“.

Bitte gleiche diese Meldung an vorhandene gute Beispiele an, ohne Funktion oder Datenformat zu ändern. Nenne danach kurz, welche Information vorher gefehlt hat.

Bitte erstelle eine knappe Änderungsanweisung mit Ziel, betroffenen Dateien, Nicht-Zielen und Abnahmekriterium. Halte sie so klein, dass ein Mini-Patch genügt.

Vergleiche alle Stellen, die denselben Kennwert nennen. Liefere Fundorte, abweichende Werte, maßgebliche Quelle und eine minimale Regel, die künftige Abweichungen automatisch verhindert.

### Vibecoding

Wenn du Platzhalter findest, widerstehe dem Reflex zum Sofortumbau. Sammle sie zuerst nummeriert, ordne sie nach Risiko und bearbeite danach nur den obersten kleinen Punkt.

Arbeite im Rhythmus Plan → Mini-Patch → gezielte Prüfung → kurze Notiz. Wenn ein Patch größer wird als gedacht, stoppe und teile ihn in zwei verständliche Schritte.

Baue zuerst den kleinsten sichtbaren Nutzen ein, beschreibe danach die nächste sinnvolle Ausbaustufe und lasse bewusst alles weg, was nur schön, aber nicht nötig ist.

Wenn der Stand fast freigabereif ist, ändere nur noch Dinge, die ein echtes Risiko senken. Verschiebe Komfortideen in eine spätere Liste, damit der Release stabil bleibt.

Nimm dir pro Runde nur einen sichtbaren Qualitätsgewinn vor, zum Beispiel bessere Statusmeldungen. Wenn die Funktion schon läuft, ändere Ablauf und Datenformat nicht mit.

Wenn eine manuelle Prüfung in der Umgebung nicht möglich ist, dokumentiere ehrlich die Grenze und ergänze den kleinsten nächsten Prüfschritt statt ein Ergebnis zu erfinden.

Halte die kreative Energie gezielt: Sammle drei Ideen, wähle eine risikoarme Idee aus und setze nur den kleinsten sichtbaren Teil davon um.

Suche zuerst nach einer kleinen Inkonsistenz, die Vertrauen kostet. Korrigiere sie an der Quelle und ergänze genau einen einfachen Test, der denselben Fehler künftig sichtbar macht.

### KI-Bildgenerierung

Erstelle eine klare Platzhalter-Grafik für einen leeren Modulzustand: freundliche Karte, dezentes Plus-Symbol, kurze visuelle Anleitung, hoher Kontrast, kein echter Text und keine Warnstimmung.

Erzeuge ein ruhiges, kontrastreiches Vorschaubild mit klar erkennbarem Hauptmotiv, einfacher Lichtführung und wenigen Ablenkungen. Nenne Stil, Kameraperspektive, Farbpalette und was ausdrücklich nicht im Bild erscheinen soll.

Erstelle ein quadratisches Titelbild für ein lokales Dashboard: dunkler Hintergrund, leuchtende Modul-Karten, klare Kanten, freundliche technische Stimmung, keine Logos, keine echten Personen, kein unlesbarer Kleinsttext.

Erzeuge ein schlichtes Release-Banner: ruhige dunkle Fläche, eine klare Checkliste mit Häkchen als Symbolik, dezente blaue Akzente, viel Abstand, keine Markenlogos und kein kleiner Fließtext.

Gestalte eine freundliche Hinweisgrafik für eine lokale Backup-Funktion: sicherer Tresor, kleine Datei-Karte, ruhige Blautöne, klare Symbole, keine Angststimmung, kein winziger Text.

Erzeuge eine kleine Import-Hinweisgrafik: geöffnete Datei, prüfendes Häkchen, dezenter Sicherheitsschild, klare helle Akzente, keine Warnpanik und keine schwer lesbaren Details.

Gestalte eine ruhige Modul-Vorschau: sechs Karten in sauberem Raster, leichte Tiefe, klare Überschriften als Formen angedeutet, freundliche Akzente und kein echter Produktname.

Visualisiere Datenkonsistenz als zwei Dokumentkarten mit identischer Prozentanzeige, verbunden durch ein geprüftes Häkchen; klare Kontraste, sachliche technische Optik, keine Warnsymbole und kein Kleinsttext.

### KI-Musikgenerierung

Beschreibe einen kurzen Denkpausen-Loop für Aufräumarbeiten: 60 Sekunden, ruhiger Puls, helle leichte Akkorde, keine Stimme, nicht ablenkend und passend zum strukturierten Prüfen von Listen.

Erstelle einen 90-Sekunden-Entwurf mit klarer Songstruktur: kurzes Intro, prägnante Strophe, wiedererkennbare Hook und weiches Outro. Halte Tempo, Stimmung, Instrumente und gewünschte Produktionsqualität eindeutig fest.

Beschreibe einen konzentrierten Arbeits-Loop: 100 BPM, warme Synth-Flächen, leise Percussion, dezenter Bass, keine dominanten Vocals, nahtlos wiederholbar und geeignet für ruhige Schreibphasen.

Erzeuge eine kurze Release-Fanfare ohne Übertreibung: 20 Sekunden, warme Akkorde, sanfter Puls, heller Abschluss, keine lauten Drums und passend für ein ruhiges Produktvideo.

Erstelle einen ruhigen Sicherheits-Jingle: 30 Sekunden, sanfte Marimba, warmer Bass, dezente Pads, optimistische Auflösung, keine dramatischen Warnklänge und geeignet für Backup-Hinweise.

Beschreibe einen kurzen Bestätigungs-Sound für erfolgreichen Import: 8 Sekunden, zwei warme Akkorde, leichter Glockenakzent, ruhiger Ausklang, nicht laut und passend zu sachlichen Statusmeldungen.

Erzeuge einen fokussierten Review-Loop: 70 Sekunden, leiser Puls, weiche E-Piano-Akkorde, kaum Höhen, keine Stimme und gut geeignet für ruhiges Lesen von Prüflisten.

Erzeuge einen 12-sekündigen Prüfklang: zwei synchrone Pulse, kurzer heller Bestätigungston, ruhiger Ausklang, keine Stimme, keine Alarmwirkung und geeignet für erfolgreich abgeglichene Projektwerte.

### KI-Contentcreation

Erstelle aus einer Platzhalter-Liste eine umsetzbare Aufgabenübersicht: zuerst Risiko, dann Nutzerwirkung, dann kleinster nächster Schritt und zuletzt ein klares Abnahmekriterium.

Schreibe den Inhalt zuerst als kurze Kernbotschaft, dann als Nutzenversprechen und zuletzt als klare Handlungsaufforderung. Halte Sprache einfach, konkret und ohne unnötige Fachbegriffe.

Erstelle aus einer technischen Änderung drei Fassungen: eine kurze Nutzerinfo, eine sachliche Release-Notiz und eine interne Prüfliste. Jede Fassung soll klar sagen, was neu ist und was unverändert bleibt.

Schreibe eine Release-Notiz in einfacher Sprache: Was wurde verbessert, welche Nutzer profitieren davon, welche Grenzen bleiben bekannt und welche Prüfung wurde durchgeführt?

Erstelle eine Nutzerinfo für verbesserte Meldungen: Beschreibe kurz, dass Hinweise jetzt Grund, Lösung und Speicherstatus nennen. Nenne auch, dass keine Arbeitsweise geändert wurde.

Schreibe ein kompaktes Prüfprotokoll: Was wurde im Browser geprüft, was war wegen Umgebung offen, welche Daten wurden nicht verändert und welcher nächste Schritt ist empfohlen.

Erstelle eine kurze Fortschrittsmeldung: ein Satz zum Nutzen, ein Satz zur geprüften Grenze und ein Satz mit dem nächsten sinnvollen Schritt ohne Werbesprache.

Schreibe eine knappe Änderungsnotiz zur Datenkonsistenz: vorherige Abweichung, festgelegter gemeinsamer Wert, neue automatische Prüfung und ausdrücklich unveränderte Laufzeitfunktion.
