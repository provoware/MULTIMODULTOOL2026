# ENTWICKLERDOKU

## 1. Technischer Stand

- ausschließlich Linux-Desktop
- Kubuntu 22.04/24.04, KDE Plasma, X11/Wayland, x86-64
- Python 3.10+
- PySide6 / Qt Widgets
- Standardbibliothek für Setup-, Manifest-, XDG- und Repository-Prüfung
- Start: `./start.sh`
- Einrichtung: `./setup.sh`

## 2. Start- und Einrichtungsfluss

```text
start.sh
  ├─ Linux und Python prüfen
  ├─ .venv/PySide6 prüfen
  ├─ bei Bedarf setup.sh
  │    ├─ fehlendes Python optional nach Bestätigung per apt-get
  │    └─ tools/setup_assistant.py
  │         ├─ Python/venv/KDE/X11-Wayland/Schreibrechte prüfen
  │         ├─ Systempakete nur nach Bestätigung
  │         ├─ .venv.setup-* erzeugen
  │         ├─ requirements.txt installieren
  │         ├─ PySide6 importieren
  │         └─ Umgebung atomar aktivieren
  ├─ python -m src.main --validate-only
  │    └─ XDG-Pfadplan rein lesend prüfen
  └─ python -m src.main
       ├─ XDG-Pfade vorvalidieren
       ├─ App-Verzeichnisse mit 0700 anlegen
       ├─ Existenz, Schreibbarkeit und Symlinks nachvalidieren
       ├─ temporäre Schreibprobe ausführen und entfernen
       └─ GUI starten
```

## 3. Sicherheitsvertrag des Setups

- keine Ausführung mit `shell=True`
- Befehle als feste Argumentlisten
- `.venv`-Symlink blockiert
- temporäre Umgebung vor Umschaltung vollständig geprüft
- bestehende Umgebung erst nach erfolgreichem Neubau umbenannt
- Rollback bei fehlgeschlagener Umschaltung
- temporäre Umgebung bei Fehler bereinigt
- Systempakete ausschließlich nach sichtbarer Bestätigung
- keine automatische Verwendung von `sudo` für den App-Start
- keine GitHub-Geheimnisse im Repository

## 4. Wichtige Dateien

| Datei | Verantwortung |
|---|---|
| `setup.sh` | Linux-Einstieg, Python-Grundprüfung und kontrollierter Paketweg |
| `tools/setup_assistant.py` | Diagnose, KDialog/Terminalbestätigung und atomare `.venv` |
| `start.sh` | sichere Orchestrierung von Einrichtung, Manifestprüfung und GUI |
| `tests/test_setup_assistant.py` | Setup-Regressionsprüfungen |
| `tools/validate_repository.py` | gesamter Repository-, Setup-, XDG- und GitHub-Zugriffsvertrag |
| `docs/GITHUB_ZUGRIFF.md` | Grenzen externer Berechtigungen und Geheimnisschutz |
| `src/main.py` | Linux-Plattformblocker, Manifest-/XDG-Startfluss und workflow-fokussiertes Desktop-Grundgerüst |
| `src/xdg_paths.py` | zentrale XDG-Auflösung, Grenzprüfung, sichere Anlage, Rechte- und Schreibprüfung |
| `tests/test_xdg_paths.py` | XDG-Regressionsprüfungen |
| `docs/XDG_PFADVERTRAG.md` | verbindliche Speicherorte, Grenzen und Fehlerverhalten |

## 5. XDG-Pfadvertrag

Die Pfadschicht hat keine PySide6-Abhängigkeit und verwendet ausschließlich die Python-Standardbibliothek.

```text
XDG_CONFIG_HOME  -> <basis>/multimodultool2026
XDG_DATA_HOME    -> <basis>/multimodultool2026
XDG_CACHE_HOME   -> <basis>/multimodultool2026
XDG_STATE_HOME   -> <basis>/multimodultool2026
logs             -> state/logs
backups          -> data/backups
```

Fehlt eine Variable, gelten die Linux-Standardwerte unter `~/.config`, `~/.local/share`, `~/.cache` und `~/.local/state`.

Sicherheitsreihenfolge:

1. absolute XDG-Basen prüfen,
2. Ziel innerhalb der jeweiligen XDG-Grenze halten,
3. Überschneidung mit `PROJECT_ROOT` blockieren,
4. App-spezifische Symlinks und Nicht-Verzeichnisse blockieren,
5. Ziele nach Pfadtiefe anlegen,
6. Modus `0700` setzen,
7. Existenz und Schreibbarkeit nachprüfen,
8. je Verzeichnis temporäre Datei schreiben, `fsync` ausführen und Datei entfernen.

`--validate-only` verändert nichts. `--paths-only` zeigt den berechneten Plan. Der normale GUI-Start führt die sichere Anlage aus.

## 6. Setup-Rückgabecodes

- `0`: bereit oder erfolgreich eingerichtet
- `2`: blockierende Plattform-, Python- oder Schreibprüfung
- `3`: `--check-only` meldet unvollständige Einrichtung
- `4`: Systempakete nicht eingerichtet
- `5`: Nutzer hat Projektumgebung abgebrochen
- `6`: atomarer Umgebungsaufbau fehlgeschlagen
- `7`: Nachprüfung fehlgeschlagen

## 7. Lokale Prüfungen

```bash
python3 tools/setup_assistant.py --check-only
python3 -m src.main --validate-only
python3 tools/validate_repository.py
python3 -m unittest discover -s tests -v
python3 -m py_compile src/main.py src/xdg_paths.py tools/setup_assistant.py tools/validate_repository.py tests/test_setup_assistant.py tests/test_xdg_paths.py
```

## 8. GitHub-Rechte

Berechtigungen gehören zur GitHub-App und zum Konto. Vor Schreibaktionen werden Konto, Repository und Berechtigungsstufe geprüft. Tokens werden weder in Code noch Dokumentation gespeichert.

## 9. Nächste Architekturgrenze

P0-003 führt ein versioniertes Einstellungsformat im XDG-Konfigurationspfad ein. Schreibvorgänge müssen atomar erfolgen, vor Änderung sichern, gegen ein Schema prüfen und bei Fehler auf die letzte gültige Version zurückfallen.
