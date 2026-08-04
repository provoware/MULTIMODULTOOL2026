# ANLEITUNG_TOOL

## Unterstützte Systeme

Kubuntu 22.04/24.04, KDE Plasma, X11 oder Wayland, x86-64. Andere Systeme werden kontrolliert blockiert.

## Start

```bash
chmod +x start.sh setup.sh
./start.sh
```

Beim ersten Start werden Linux, Python, PySide6, XDG-Pfade, Einstellungen, Ereignisjournal und privater Laufzeitpfad geprüft.

## Zweiter Start

Ein zweiter normaler Start öffnet kein zweites Hauptfenster. Er sucht den privaten Unix-Socket, prüft die Linux-Nutzerkennung, überträgt nur die erlaubte Aktivierung und macht das vorhandene Fenster sichtbar.

Diagnose öffnen:

```bash
python3 -m src.main --show-diagnostics
```

Diagnosekennung fokussieren:

```bash
python3 -m src.main --show-diagnostics --diagnostic-id MMT-XDG-20260804-ABCD1234
```

Dateipfade, freie Argumentlisten und beliebige Befehle können nicht übergeben werden.

## Veraltete Sperre

Eine Sperre wird nur entfernt, wenn Socket und Metadaten dem aktuellen Nutzer gehören, sichere Dateitypen sind und Prozess- oder Boot-Kennung eindeutig belegen, dass keine aktive Instanz mehr besteht. Danach wird ein Recovery-Ereignis protokolliert.

## Beschädigte oder zweifelhafte Sperre

Der Start wird blockiert. Die Sperre bleibt unverändert. Der Fehlerbericht nennt Ursache, Folge, Datenstand, Lösung, Diagnosekennung und sicheren nächsten Schritt. Das Tool nicht mit `sudo` starten und Sperren nicht blind löschen.

## Diagnosezentrale

1. Schweregrad auswählen.
2. Optional Diagnosekennung eingeben.
3. Ereignis auswählen.
4. Vollständigen bereinigten Bericht lesen.
5. Bei Bedarf **Bereinigten Bericht kopieren** drücken.

Nicht vorhanden: Löschen, Upload, automatischer Export oder Journalreparatur.

## Rein lesende Prüfungen

```bash
python3 -m src.main --validate-only
python3 -m src.main --paths-only
python3 -m src.main --settings-only
```

Diese Modi erzeugen keine zweite GUI-Instanz.

## Typische Fehler

### XDG_RUNTIME_DIR unsicher

**Folge:** GUI-Start blockiert.  
**Datenstand:** Keine Sperre und keine Nutzerdaten verändert.  
**Lösung:** KDE-Sitzung als normaler Nutzer starten und `/run/user/<UID>` prüfen.

### Instanz antwortet nicht

Eine lebende, aber nicht antwortende Instanz wird nicht überschrieben. Vorhandenen Prozess und Diagnosekennung prüfen.

### Ereignisjournal unsicher

Symlink, falscher Eigentümer, Hardlink, falscher Dateityp oder Rechte offener als `0600` blockieren den Zugriff. Das Journal bleibt unverändert.
