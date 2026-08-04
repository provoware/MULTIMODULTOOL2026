# ENTWICKLERDOKU

## 1. Technischer Stand

- Plattformvertrag: ausschließlich Linux-Desktop
- Primäre Distributionen: Kubuntu 22.04 LTS und Kubuntu 24.04 LTS
- Desktop: KDE Plasma unter X11 und Wayland
- Architektur: x86-64
- Sprache: Python 3.10+
- Desktop-Framework: PySide6 / Qt Widgets
- Manifest- und Repository-Prüfung: reine Python-Standardbibliothek
- Startpunkt: `python3 -m src.main`
- sichere Linux-Startroutine: `./start.sh`

Nicht unterstützt: Windows, macOS, Android, iOS, Browser und PWA.

## 2. Startfluss

```text
start.sh
  ├─ Linux-Shell und Python-Version prüfen
  ├─ lokale .venv bevorzugen
  ├─ python -m src.main --validate-only
  │    ├─ Linux-Plattform prüfen
  │    └─ src/manifest_validator.py
  │         ├─ JSON lesen
  │         ├─ Linux-Plattformvertrag prüfen
  │         ├─ Projektname prüfen
  │         ├─ Referenzpfad absichern
  │         ├─ neun Zonen prüfen
  │         └─ Iterationsvertrag prüfen
  ├─ PySide6-Verfügbarkeit prüfen
  └─ python -m src.main
       └─ Qt-Oberfläche mit Z01–Z09
```

Der Import von PySide6 erfolgt absichtlich erst nach erfolgreicher Plattform- und Manifestprüfung. Dadurch funktionieren CI, Diagnose und Repository-Prüfung ohne installierte GUI-Bibliothek.

## 3. Dateien und Verantwortung

| Datei | Verantwortung |
|---|---|
| `src/main.py` | Linux-Plattformblocker, Argumente, Startablauf und sichtbares Desktop-Grundgerüst |
| `src/manifest_validator.py` | reine, testbare Prüfung von Linux- und Layoutvertrag |
| `src/theme.qss` | aktuelles Qt-Grundtheme |
| `layout-manifest.json` | maschinenlesbarer Plattform-, Zonen-, Sicherheits- und Iterationsvertrag |
| `tools/validate_repository.py` | Pflichtdateien, Plattformvertrag, Fortschritt, Dokumentation, Syntax und Startvertrag |
| `tests/test_repository_contract.py` | Regressionstests für Linux-, Manifest- und Repository-Vertrag |
| `.github/workflows/repository-contract.yml` | automatische Prüfung auf Ubuntu bei Push und Pull Request |

## 4. Linux-Regeln

- Laufzeitpfade werden später XDG-konform unter `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_CACHE_HOME` und `XDG_STATE_HOME` abgelegt.
- Pfade werden mit `pathlib.Path` verarbeitet; keine Windows-Laufwerksbuchstaben oder Backslash-Sonderlogik.
- Dateirechte, Symlinks, Mountpoints und Groß-/Kleinschreibung müssen explizit geprüft werden.
- KDE-Dateidialoge, X11 und Wayland werden getrennt abgenommen.
- Paketziele sind zunächst ein Debian-Paket und optional AppImage. Andere Betriebssystempakete sind ausgeschlossen.

## 5. Layoutzonen

Die IDs `Z01` bis `Z09` und ihre Reihenfolge sind verbindlich. Interne Widgets dürfen sich ändern, solange Rolle, Erreichbarkeit und Grundposition erhalten bleiben. Strukturelle Abweichungen benötigen ausdrückliche Nutzerfreigabe und eine Manifestanpassung.

## 6. Fortschrittsberechnung

`TODO.md` ist die einzige Quelle:

```text
erledigt = Anzahl "- [x]"
offen    = Anzahl "- [ ]"
gesamt   = erledigt + offen
prozent  = round(erledigt / gesamt * 100)
```

`tools/validate_repository.py` blockiert inkonsistente README-Werte.

## 7. Lokale Prüfungen

```bash
python3 -m src.main --validate-only
python3 tools/validate_repository.py
python3 -m unittest discover -s tests -v
python3 -m py_compile src/main.py src/manifest_validator.py tools/validate_repository.py tests/test_repository_contract.py
```

Für einen GUI-Smoke-Test wird PySide6 benötigt:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m src.main
```

Der aktuelle Stand beendet sich dabei nicht automatisch; ein automatisierter Linux-GUI-Smoke-Test folgt in einer späteren Aufgabe.

## 8. Entwicklungsregeln

- Prüflogik bleibt von PySide6 unabhängig.
- Geschäftslogik darf nicht direkt in Widgets wachsen.
- Dateisystemänderungen benötigen Vorschau, Transaktion, Protokoll und Rückfallweg.
- Keine absolute Benutzerpfade in portablen Projektdateien.
- Fehlertexte müssen Ursache, Folge, Lösung und Datenzustand nennen.
- Neue Abhängigkeiten werden in README, Anleitung, Entwicklerdoku, Schwachstellen und Changelog bewertet.
- Änderungen an Aufgabenstatus aktualisieren README und TODO im selben Commit.
- Keine nicht-linuxbezogenen Abstraktionen oder Paketziele ohne ausdrückliche Freigabe.

## 9. Nächste Architekturgrenze

Vor echten Dateioperationen werden zuerst folgende Linux-Basisschichten eingeführt:

1. XDG-konforme Pfad- und Arbeitsverzeichnisverwaltung
2. versionierte Einstellungen mit atomarem Schreiben
3. zentrales Fehler- und Ereignismodell
4. Papierkorb-, Undo- und Aktionsjournal
5. abbrechbare Worker für lange Operationen

Erst danach werden Analyse-, Umbenennungs-, Duplikat- und Sortiermodule produktiv freigeschaltet.
