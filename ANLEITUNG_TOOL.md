# ANLEITUNG_TOOL

## 1. Zweck des aktuellen Stands

MULTIMODULTOOL2026 ist ein startbares Linux-Desktop-Grundgerüst mit geführter Einrichtung, XDG-Speichertrennung, transaktionalen Einstellungen und zentraler Fehler-/Ereignisschicht. Produktive Dateioperationen sind weiterhin deaktiviert.

## 2. Unterstützte Systeme

- Kubuntu 22.04 LTS, x86-64
- Kubuntu 24.04 LTS, x86-64
- KDE Plasma unter X11 oder Wayland
- Python 3.10 oder neuer

Nicht unterstützt: Windows, macOS, Android, iOS, Browser und PWA.

## 3. Einfacher Start

```bash
chmod +x start.sh setup.sh
./start.sh
```

Fehlt eine Abhängigkeit, startet der Einrichtungsassistent. Systempakete und `.venv` werden nur nach Bestätigung eingerichtet.

## 4. Rein lesende Prüfungen

```bash
./setup.sh --check-only
python3 -m src.main --validate-only
python3 -m src.main --paths-only
python3 -m src.main --settings-only
```

Diese Modi dürfen keine XDG-Verzeichnisse oder Einstellungsdateien anlegen, verändern, umbenennen oder löschen.

## 5. Sichere Speicherorte

- Konfiguration: `~/.config/multimodultool2026`
- Nutzerdaten: `~/.local/share/multimodultool2026`
- Cache: `~/.cache/multimodultool2026`
- Status: `~/.local/state/multimodultool2026`
- Logs: `~/.local/state/multimodultool2026/logs`
- Sicherungen: `~/.local/share/multimodultool2026/backups`

App-Verzeichnisse verwenden `0700`. Einstellungs- und Ereignisdateien verwenden `0600`.

## 6. Globaler Fehlerdialog

Bei einem kontrolliert erfassten Fehler erscheint ein Dialog mit sechs Bereichen:

1. **Ursache** – welcher Fehler wurde erkannt?
2. **Folge** – welcher Schritt wurde beendet oder blockiert?
3. **Datenstand** – was ist unverändert, was wurde isoliert?
4. **Lösung** – welche Korrektur ist möglich?
5. **Diagnosekennung** – eindeutige Kennung für Bericht und Logsuche.
6. **Sicherer nächster Schritt** – welcher geprüfte Schritt darf folgen?

Über **Diagnose kopieren** wird der vollständige Bericht in die Zwischenablage übernommen.

### Vorgehen nach einem Fehler

1. Datenstand lesen; nicht blind erneut starten.
2. Diagnosekennung notieren oder kopieren.
3. vorgeschlagene Lösung ausführen.
4. passenden rein lesenden Diagnosebefehl starten.
5. normalen Workflow erst bei grünem Ergebnis fortsetzen.

## 7. Ereignisjournal

Datei:

```text
~/.local/state/multimodultool2026/logs/events.jsonl
```

Jede Zeile enthält ein vollständiges JSON-Ereignis. Die Datei ist privat (`0600`). Benutzerpfade werden verkürzt und typische Geheimnismuster entfernt.

Das Journal darf nicht durch einen Symlink ersetzt werden. Ist es unsicher oder unbeschreibbar, blockiert das Tool den normalen Start.

## 8. Einstellungen und Recovery

Aktive Datei:

```text
~/.config/multimodultool2026/settings.json
```

Sicherung:

```text
~/.config/multimodultool2026/settings.last-valid.json
```

Bei Beschädigung wird die aktive Datei isoliert. Danach wird die Sicherung oder eine sichere Standardkonfiguration atomar aktiviert. Der globale Dialog erklärt Ursache, verwendete Quelle und unveränderten Nutzerdatenstand.

## 9. Failpoint-Prüfung

Die Entwicklungstests simulieren Unterbrechungen vor und nach:

- temporärem Schreiben,
- Datei-`fsync`,
- Backup,
- `os.replace`,
- Nachvalidierung.

Diese Failpoints sind Testhilfen und werden im normalen Start nicht aktiviert. Sie beweisen, dass immer eine vollständige alte oder neue Konfiguration erhalten bleibt.

## 10. Typische Fehler

### Ereignisjournal ist unsicher

**Ursache:** Logdatei ist Symlink, Spezialdatei, zu offen oder nicht beschreibbar.  
**Folge:** Normaler Start wird blockiert.  
**Datenstand:** Einstellungen und Nutzerdaten bleiben unverändert.  
**Lösung:** `events.jsonl` entfernen oder auf reguläre Datei mit `0600` korrigieren.  
**Nächster Schritt:** XDG-Logpfad prüfen und `./start.sh` erneut ausführen.

### Einstellungen wurden wiederhergestellt

**Ursache:** Aktive JSON-Datei war beschädigt oder inkompatibel.  
**Folge:** Sicherung oder Standardwerte wurden aktiviert.  
**Datenstand:** Produktive Nutzerdaten blieben unverändert.  
**Lösung:** Wiederhergestellte Einstellungen prüfen.  
**Nächster Schritt:** `python3 -m src.main --settings-only` ausführen.

### PySide6 fehlt

```bash
./setup.sh
```

## 11. Entwicklerprüfungen

```bash
python3 tools/validate_repository.py
python3 -m unittest discover -s tests -v
python3 -m unittest tests.test_settings_failpoints -v
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_gui_offscreen -v
```

## 12. Aktuelle Grenze

Noch keine privaten oder unersetzlichen Dateibestände bearbeiten. Produktive Funktionen folgen erst nach Single-Instance-Schutz, Papierkorb, Undo und Wiederanlauf.
