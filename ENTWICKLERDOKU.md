# ENTWICKLERDOKU

## 1. Technischer Stand

- ausschließlich Linux-Desktop
- Kubuntu 22.04/24.04, KDE Plasma, X11/Wayland, x86-64
- Python 3.10+
- PySide6 / Qt Widgets
- Standardbibliothek für Setup-, Manifest- und Repository-Prüfung
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
  └─ python -m src.main
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
| `start.sh` | Einrichtung, Manifestprüfung und GUI-Start |
| `tests/test_setup_assistant.py` | Setup-Regressionsprüfungen |
| `tools/validate_repository.py` | Repository-, Setup- und GitHub-Zugriffsvertrag |
| `docs/GITHUB_ZUGRIFF.md` | Grenzen externer Berechtigungen und Geheimnisschutz |
| `src/main.py` | Linux-Plattformblocker und Desktop-Grundgerüst |

## 5. Setup-Rückgabecodes

- `0`: bereit oder erfolgreich eingerichtet
- `2`: blockierende Plattform-, Python- oder Schreibprüfung
- `3`: `--check-only` meldet unvollständige Einrichtung
- `4`: Systempakete nicht eingerichtet
- `5`: Nutzer hat Projektumgebung abgebrochen
- `6`: atomarer Umgebungsaufbau fehlgeschlagen
- `7`: Nachprüfung fehlgeschlagen

## 6. Lokale Prüfungen

```bash
python3 tools/setup_assistant.py --check-only
python3 -m src.main --validate-only
python3 tools/validate_repository.py
python3 -m unittest discover -s tests -v
python3 -m py_compile tools/setup_assistant.py tools/validate_repository.py tests/test_setup_assistant.py
```

## 7. GitHub-Rechte

Berechtigungen gehören zur GitHub-App und zum Konto. Vor Schreibaktionen werden Konto, Repository und Berechtigungsstufe geprüft. Tokens werden weder in Code noch Dokumentation gespeichert.

## 8. Nächste Architekturgrenze

P0-002 führt eine zentrale XDG-Pfadschicht ein. Erst danach dürfen Einstellungen, Logs oder Nutzerdaten außerhalb klar definierter Linux-Benutzerverzeichnisse geschrieben werden.
