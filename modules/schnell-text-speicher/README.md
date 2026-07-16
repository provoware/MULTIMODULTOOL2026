# Schnell-Text-Speicher

Dieses Modul sammelt kurze, wiederverwendbare Textbausteine. Die Bausteine sind bewusst knapp formuliert, damit sie schnell kopiert, angepasst und in eigenen Arbeitsabläufen genutzt werden können.

## Textbausteine

### Coding

Begrenze lange Listen sichtbar statt Daten zu kürzen: Anzeige klein halten, vollständigen Export erhalten und dem Nutzer klar sagen, wie viele Einträge ausgeblendet sind.

Prüfe einen mittelgroßen Patch wie ein Paket: Teiländerungen einzeln lesen, gemeinsamen Zweck prüfen, unnötige Nebeneffekte markieren und erst danach die Sammelvalidierung starten.

Prüfe die Änderung in kleinen Schritten: erst Eingaben absichern, dann die kleinste passende Funktion ändern, danach nur die direkt betroffene Ausgabe testen. Vermeide globale Umbauten, solange der Fehler lokal begrenzt ist.

Formuliere vor dem Patch eine kurze Risikozeile: Welche Daten könnten betroffen sein, wie wird ein Abbruch erkannt und welche Prüfung zeigt danach, dass nichts Nebenliegendes beschädigt wurde?

Erstelle vor einer Freigabe eine knappe Prüfliste: Start, Speichern, Laden, Import, Export, Fehlermeldung und Rückbau. Markiere jeden Punkt mit bestanden, offen oder blockiert.

Verbessere eine Nutzer-Meldung so, dass sie vier Fragen beantwortet: Was ist passiert, warum ist es passiert, was soll ich tun und wurde etwas gespeichert oder verändert?

Vergleiche ähnliche Meldungen paarweise, bevor du Code änderst: Export, Import und Backup sollen gleich klar sein, aber nur echte Lücken bekommen neue Wörter.

Dokumentiere nach jeder kleinen Änderung genau eine Begründung: Welches Risiko wurde gesenkt, welche Datei wurde berührt und welche Prüfung reicht dafür aus?

Prüfe gekoppelte Statusangaben automatisch: Lies beide Quellen, validiere Wertebereich und Format und brich mit einer klaren Meldung ab, sobald die Angaben voneinander abweichen.
Erstelle eine Platzhalter-Inventur: Suche nach TODO, FIXME, Dummy, Stub, Beispieltexten und leeren Zuständen. Bearbeite nichts sofort, sondern schreibe zuerst eine nummerierte Liste mit Risiko und Prüfschritt.

Prüfe gekoppelte Statusangaben automatisch: Lies beide Quellen, validiere Wertebereich und Format und brich mit einer klaren Meldung ab, sobald die Angaben voneinander abweichen.
Prüfe ein Manifest wie einen Türsteher: Stimmen Pflichtfelder, Ordnername, erlaubte Einstiegspunkte und vorhandene Dateien? Lehne nur klar falsche Angaben ab und melde verständlich, was fehlt.

Erstelle vor einer Modul-Auslagerung eine Rückbauzeile: Welche Manifestangabe wird geändert, welche neue Datei kann entfernt werden und welche Prüfung beweist den alten stabilen Stand?

Kapsle Modul-CSS immer über eine eindeutige Hauptklasse. Prüfe danach, dass keine globale Überschrift, kein Button und kein Eingabefeld außerhalb des Moduls unbeabsichtigt anders aussieht.

### Prompting

Bitte verbessere eine Fehlermeldung nach vier Punkten: Ereignis, Ursache, nächster Schritt und Datenstatus. Ändere dabei keine Funktion, wenn nur der Text unklar ist.

Plane eine mittelgroße Änderung als Paket: ein Ziel, zwei bis vier zusammenhängende Teilaufgaben, klare Nicht-Ziele und eine gemeinsame Endprüfung. Stoppe, sobald ein Teil unsicher wird.

Ermittle Platzhalter nicht nur nach dem Wort „TODO“, sondern auch nach Beispielen, leeren Zuständen, Dummy-Daten und Stubs. Gib je Fundstelle Datei, Zweck, Risiko und nächsten Schritt an.

Beschreibe zuerst Ziel, gewünschtes Ausgabeformat, Eingabedaten und Ausschlüsse. Bitte danach um Rückfragen nur dann, wenn ohne Antwort ein falsches Ergebnis wahrscheinlich wäre.

Nutze diese Struktur: Rolle, Aufgabe, Kontext, harte Grenzen, gewünschte Prüfschritte und Ausgabeformat. Ergänze am Ende: Wenn etwas unsicher ist, nenne Annahme und Risiko statt zu raten.

Bitte prüfe meinen Entwurf wie ein Release-Reviewer: Nenne zuerst blockierende Fehler, dann kleine Verbesserungen und zuletzt genau die Punkte, die unverändert bleiben sollten.

Formuliere eine Fehlermeldung in einfacher Sprache. Nutze die Reihenfolge: Ereignis, Grund, nächster Schritt, Speicherstatus. Vermeide Schuldzuweisungen und unklare Wörter wie „Fehler 1“.

Bitte gleiche diese Meldung an vorhandene gute Beispiele an, ohne Funktion oder Datenformat zu ändern. Nenne danach kurz, welche Information vorher gefehlt hat.

Bitte erstelle eine knappe Änderungsanweisung mit Ziel, betroffenen Dateien, Nicht-Zielen und Abnahmekriterium. Halte sie so klein, dass ein Mini-Patch genügt.

Bitte prüfe diese Modulbeschreibung auf Konsistenz: Passt die ID zum Ordner, zeigen Einstiegsdateien auf echte Dateien und bleibt die Fehlermeldung für Laien verständlich?
Vergleiche alle Stellen, die denselben Kennwert nennen. Liefere Fundorte, abweichende Werte, maßgebliche Quelle und eine minimale Regel, die künftige Abweichungen automatisch verhindert.

Bewerte einen Modul-Kandidaten vor der Auslagerung: fachliche Aufgabe, geringe Kopplung, notwendige Dateien, Rückbaupfad und genau eine passende Prüfung.

Bitte prüfe diese CSS-Ergänzung wie einen sicheren Modulschritt: Ist sie auf den Modulbereich begrenzt, verbessert sie Lesbarkeit und bleibt der Rückbau über Manifest und Datei klar?

### Vibecoding

Wenn fünf kleine TODOs zusammenpassen, bündle sie über einen gemeinsamen Qualitätsgewinn: bessere Lesbarkeit, klarere Prüfung und weniger Wiederholung. Stoppe bei jedem Architekturumbau.

Bitte optimiere eine Arbeitsanweisung auf Effizienz: entferne Wiederholungen, bündle passende Schritte und behalte alle Sicherheits- und Prüfregeln ausdrücklich bei.

Wenn du Platzhalter findest, widerstehe dem Reflex zum Sofortumbau. Sammle sie zuerst nummeriert, ordne sie nach Risiko und bearbeite danach nur den obersten kleinen Punkt.

Arbeite im Rhythmus Plan → Mini-Patch → gezielte Prüfung → kurze Notiz. Wenn ein Patch größer wird als gedacht, stoppe und teile ihn in zwei verständliche Schritte.

Baue zuerst den kleinsten sichtbaren Nutzen ein, beschreibe danach die nächste sinnvolle Ausbaustufe und lasse bewusst alles weg, was nur schön, aber nicht nötig ist.

Wenn der Stand fast freigabereif ist, ändere nur noch Dinge, die ein echtes Risiko senken. Verschiebe Komfortideen in eine spätere Liste, damit der Release stabil bleibt.

Nimm dir pro Runde nur einen sichtbaren Qualitätsgewinn vor, zum Beispiel bessere Statusmeldungen. Wenn die Funktion schon läuft, ändere Ablauf und Datenformat nicht mit.

Wenn eine manuelle Prüfung in der Umgebung nicht möglich ist, dokumentiere ehrlich die Grenze und ergänze den kleinsten nächsten Prüfschritt statt ein Ergebnis zu erfinden.

Halte die kreative Energie gezielt: Sammle drei Ideen, wähle eine risikoarme Idee aus und setze nur den kleinsten sichtbaren Teil davon um.

Behandle Prüfcode wie Sicherheitsgeländer: Er soll klare Fehltritte verhindern, aber keine funktionierende Übergangslösung unnötig blockieren.
Suche zuerst nach einer kleinen Inkonsistenz, die Vertrauen kostet. Korrigiere sie an der Quelle und ergänze genau einen einfachen Test, der denselben Fehler künftig sichtbar macht.

Starte eine Modul-Auslagerung nicht mit dem großen Umbau. Erstelle zuerst eine kleine echte Moduldatei, verknüpfe sie im Manifest und prüfe nur diesen Pfad.

Wenn ein Modul Gestaltung braucht, beginne mit einer gekapselten CSS-Datei statt mit neuer Logik. Sichtbarer Nutzen, kleiner Rückbau und Manifestprüfung reichen für den nächsten sicheren Schritt.

### KI-Bildgenerierung

Erzeuge eine sachliche Statuschip-Vorschau: dunkle Oberfläche, gut lesbare helle Pillen, dezente Linien, keine Warnfarben und keine winzigen Beschriftungen.

Arbeite in mittelgroßen Kreativschritten: erst grobe Richtung, dann ein sichtbarer Qualitätsgewinn, danach gezielte Korrektur. Vermeide spontane Komplettumbauten, wenn ein Detailpatch reicht.

Erstelle eine klare Platzhalter-Grafik für einen leeren Modulzustand: freundliche Karte, dezentes Plus-Symbol, kurze visuelle Anleitung, hoher Kontrast, kein echter Text und keine Warnstimmung.

Erzeuge ein ruhiges, kontrastreiches Vorschaubild mit klar erkennbarem Hauptmotiv, einfacher Lichtführung und wenigen Ablenkungen. Nenne Stil, Kameraperspektive, Farbpalette und was ausdrücklich nicht im Bild erscheinen soll.

Erstelle ein quadratisches Titelbild für ein lokales Dashboard: dunkler Hintergrund, leuchtende Modul-Karten, klare Kanten, freundliche technische Stimmung, keine Logos, keine echten Personen, kein unlesbarer Kleinsttext.

Erzeuge ein schlichtes Release-Banner: ruhige dunkle Fläche, eine klare Checkliste mit Häkchen als Symbolik, dezente blaue Akzente, viel Abstand, keine Markenlogos und kein kleiner Fließtext.

Gestalte eine freundliche Hinweisgrafik für eine lokale Backup-Funktion: sicherer Tresor, kleine Datei-Karte, ruhige Blautöne, klare Symbole, keine Angststimmung, kein winziger Text.

Erzeuge eine kleine Import-Hinweisgrafik: geöffnete Datei, prüfendes Häkchen, dezenter Sicherheitsschild, klare helle Akzente, keine Warnpanik und keine schwer lesbaren Details.

Gestalte eine ruhige Modul-Vorschau: sechs Karten in sauberem Raster, leichte Tiefe, klare Überschriften als Formen angedeutet, freundliche Akzente und kein echter Produktname.

Erzeuge ein klares Symbolbild für Manifest-Prüfung: Ordner, Häkchen, kleine Dateikarten und dezenter Schutzrahmen, ruhige Blautöne, keine bedrohliche Warnoptik und kein lesbarer Kleinsttext.
Visualisiere Datenkonsistenz als zwei Dokumentkarten mit identischer Prozentanzeige, verbunden durch ein geprüftes Häkchen; klare Kontraste, sachliche technische Optik, keine Warnsymbole und kein Kleinsttext.

Erzeuge eine klare Modul-Kachel für Schnelltexte: kompakte Karten, geordnete Notizzettel, ruhige Blautöne, deutliche Leseflächen, keine privaten Inhalte und kein Kleinsttext.

Gestalte eine schmale Vorschau für gekapseltes Modul-CSS: ein einzelner heller Rahmen im dunklen Dashboard, drei klare Karten, ruhige Akzente, keine Logos und kein lesbarer Fließtext.

### KI-Musikgenerierung

Beschreibe einen ruhigen Aufräum-Loop für TODO-Abschluss: 72 Sekunden, warmer Puls, leichte Häkchen-Akzente, keine Stimme, kein dramatischer Aufbau.

Beschreibe einen produktiven Iterations-Loop als Musik: 75 Sekunden, moderater Puls, klare kleine Akzente, warme Pads, keine Stimme und ein ruhiger Abschluss nach erfolgreicher Prüfung.

Beschreibe einen kurzen Denkpausen-Loop für Aufräumarbeiten: 60 Sekunden, ruhiger Puls, helle leichte Akkorde, keine Stimme, nicht ablenkend und passend zum strukturierten Prüfen von Listen.

Erstelle einen 90-Sekunden-Entwurf mit klarer Songstruktur: kurzes Intro, prägnante Strophe, wiedererkennbare Hook und weiches Outro. Halte Tempo, Stimmung, Instrumente und gewünschte Produktionsqualität eindeutig fest.

Beschreibe einen konzentrierten Arbeits-Loop: 100 BPM, warme Synth-Flächen, leise Percussion, dezenter Bass, keine dominanten Vocals, nahtlos wiederholbar und geeignet für ruhige Schreibphasen.

Erzeuge eine kurze Release-Fanfare ohne Übertreibung: 20 Sekunden, warme Akkorde, sanfter Puls, heller Abschluss, keine lauten Drums und passend für ein ruhiges Produktvideo.

Erstelle einen ruhigen Sicherheits-Jingle: 30 Sekunden, sanfte Marimba, warmer Bass, dezente Pads, optimistische Auflösung, keine dramatischen Warnklänge und geeignet für Backup-Hinweise.

Beschreibe einen kurzen Bestätigungs-Sound für erfolgreichen Import: 8 Sekunden, zwei warme Akkorde, leichter Glockenakzent, ruhiger Ausklang, nicht laut und passend zu sachlichen Statusmeldungen.

Erzeuge einen fokussierten Review-Loop: 70 Sekunden, leiser Puls, weiche E-Piano-Akkorde, kaum Höhen, keine Stimme und gut geeignet für ruhiges Lesen von Prüflisten.

Beschreibe einen sanften Validierungs-Loop: 80 Sekunden, ruhiger Klick-Puls, warme Pads, kurze helle Bestätigungstöne, keine Stimme und passend zum konzentrierten Prüfen von Manifesten.
Erzeuge einen 12-sekündigen Prüfklang: zwei synchrone Pulse, kurzer heller Bestätigungston, ruhiger Ausklang, keine Stimme, keine Alarmwirkung und geeignet für erfolgreich abgeglichene Projektwerte.

Beschreibe einen ruhigen Textbaustein-Loop: 64 Sekunden, weiche Tasten, leiser Puls, kurze helle Markierungen für geprüfte Abschnitte, keine Stimme und nahtlos wiederholbar.

Erzeuge einen 45-sekündigen Modul-Styling-Loop: dezenter Bass, klare Klicks für Prüfschritte, warme Fläche, keine Stimme, kein dramatischer Aufbau und ein sauberer Abschluss.

### KI-Contentcreation

Schreibe eine kurze Abschlussnotiz für fünf erledigte Aufgaben: je ein Nutzenpunkt, eine geprüfte Grenze, ein unveränderter Bereich und ein konkreter nächster Schritt.

Schreibe ein kompaktes Iterationsprotokoll: gebündelte Teilaufgaben, erreichter Effizienzgewinn, geprüfte Dateien, unveränderte Grenzen und zwei nächste Schritte.

Erstelle aus einer Platzhalter-Liste eine umsetzbare Aufgabenübersicht: zuerst Risiko, dann Nutzerwirkung, dann kleinster nächster Schritt und zuletzt ein klares Abnahmekriterium.

Schreibe den Inhalt zuerst als kurze Kernbotschaft, dann als Nutzenversprechen und zuletzt als klare Handlungsaufforderung. Halte Sprache einfach, konkret und ohne unnötige Fachbegriffe.

Erstelle aus einer technischen Änderung drei Fassungen: eine kurze Nutzerinfo, eine sachliche Release-Notiz und eine interne Prüfliste. Jede Fassung soll klar sagen, was neu ist und was unverändert bleibt.

Schreibe eine Release-Notiz in einfacher Sprache: Was wurde verbessert, welche Nutzer profitieren davon, welche Grenzen bleiben bekannt und welche Prüfung wurde durchgeführt?

Erstelle eine Nutzerinfo für verbesserte Meldungen: Beschreibe kurz, dass Hinweise jetzt Grund, Lösung und Speicherstatus nennen. Nenne auch, dass keine Arbeitsweise geändert wurde.

Schreibe ein kompaktes Prüfprotokoll: Was wurde im Browser geprüft, was war wegen Umgebung offen, welche Daten wurden nicht verändert und welcher nächste Schritt ist empfohlen.

Erstelle eine kurze Fortschrittsmeldung: ein Satz zum Nutzen, ein Satz zur geprüften Grenze und ein Satz mit dem nächsten sinnvollen Schritt ohne Werbesprache.

Schreibe eine kurze Prüferklärung für Nicht-Techniker: Ein Manifest ist der Steckbrief eines Moduls; geprüft wurden Name, Ordner, erlaubte Dateien und fehlende Verweise.
Schreibe eine knappe Änderungsnotiz zur Datenkonsistenz: vorherige Abweichung, festgelegter gemeinsamer Wert, neue automatische Prüfung und ausdrücklich unveränderte Laufzeitfunktion.

Schreibe eine knappe Modul-Vorbereitungsnotiz: ausgewählter Kandidat, neue Datei, Manifest-Verweis, Rückbauweg, geprüfte Grenze und unveränderte Haupt-App.

Schreibe eine kurze Styling-Notiz für ein Modul: welche Klasse kapselt die Gestaltung, welche Lesbarkeit verbessert wurde, welche App-Bereiche unverändert bleiben und welche Prüfung das absichert.
