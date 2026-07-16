# Repository-Audit 2026-07-16

## Ergebnis

1. **Start-Race im lokalen Startskript – behoben.** Der Browser wurde vor dem eigentlichen Serverstart geöffnet. Das konnte sporadisch eine nicht erreichbare Seite anzeigen. Der Server startet nun zuerst, wird per HTTP geprüft und erst danach geöffnet.
2. **Fehlende Startbereitschaftsprüfung – behoben.** Das Skript wartet jetzt bis zu acht Sekunden auf eine erfolgreiche HTTP-Antwort der Startdatei und bricht mit einer verständlichen Diagnose ab.
3. **Unvollständige Pflichtdateiprüfung – behoben.** Zusätzlich werden Manifest-Schema und GenreTool-Manifest geprüft.
4. **Ungültige Portwerte – behoben.** `MULTIMODULTOOL_PORT` wird auf Ganzzahl und Bereich 1 bis 65535 validiert.
5. **Unklare Python-Anforderung – behoben.** Das Skript verlangt nun ausdrücklich Python 3.8 oder neuer.
6. **Fehlende automatisierbare Startprüfung – behoben.** `MULTIMODULTOOL_NO_BROWSER=1` erlaubt Tests ohne grafische Browseröffnung. `tests/test_start_local.py` prüft den vollständigen Startweg über HTTP.
7. **Serverprozess bei Abbruch – verbessert.** Signal- und Exit-Behandlung räumt den gestarteten Serverprozess kontrolliert auf.
8. **Monolithische Hauptdatei – offen, hohes Wartungsrisiko.** Die HTML-Datei umfasst rund 5.856 Zeilen mit Oberfläche, Zustand, Speicherung, Modullader und Fachlogik. Weitere Auslagerung sollte schnittstellenweise erfolgen; kein riskanter Komplettumbau.
9. **Manifest-Modul lädt JavaScript per `script.textContent` – offen, hohes Vertrauensrisiko.** Lokale Moduldateien erhalten vollen Zugriff auf App und Browser-Kontext. Vor weiteren Drittmodulen braucht es Vertrauensstufen, Hash-Prüfung oder eine isolierte iframe-Laufzeit.
10. **Hilfslogik-Test dupliziert Produktionslogik – offen.** `tests/test_html_helpers.py` führt nachgebildete Funktionen aus und prüft nur zusätzlich, ob Funktionsnamen in der HTML-Datei vorkommen. Dadurch kann Produktionscode abweichen, während der Test weiterhin besteht. Nächster Schritt: echte Funktionsblöcke extrahieren oder testbare Kernlogik in eine gemeinsame Datei auslagern.
11. **Dokumentationsinkonsistenz in `AGENTS.md` – behoben.** Der Runtime-Ansatz nennt jetzt das empfohlene Startskript mit lokalem Server und den direkten Datei-Start nur noch als eingeschränkten Rückfall.
12. **Beschädigtes Qualitäts-Gate in `AGENTS.md` – behoben.** Tippfehler, unklare Pflichtpunkte und der leere Punkt 12 wurden durch prüfbare Abschlusskriterien ersetzt.
13. **Entwicklerdokumentation veraltet – behoben.** Die Tastaturplatzierung ist jetzt als vorhandene Funktion beschrieben; Startweg und relevante Prüfungen sind an den aktuellen Projektstand angepasst.
14. **Keine sichtbare CI-Konfiguration ermittelt – offen.** Die vorhandenen Python-Prüfungen sollten bei Push und Pull Request automatisiert ausgeführt werden.
15. **Release-Status bleibt korrekt eingeschränkt.** Eine echte Chromium- und Firefox-Sichtprüfung ist weiterhin erforderlich; statische und HTTP-Tests ersetzen keine Bedien- und Kontrastprüfung.

## Geänderte Dateien

- `scripts/start-local.sh`
- `tests/test_start_local.py`
- `docs/REPOSITORY_AUDIT_2026-07-16.md`
- `AGENTS.md`
- `docs/DEVELOPER_GUIDE.md`

## Prüfung

```sh
python3 tests/test_start_local.py
python3 tests/validate_progress_consistency.py
python3 tests/validate_module_manifests.py
python3 tests/test_html_helpers.py
python3 tests/validate_genres_module.py
python3 tests/validate_module_previews.py
python3 tests/scan_performance_hotspots.py
```

## Nächste Priorität

1. Produktionsnahe Tests statt kopierter Hilfsfunktionen.
2. Vertrauensgrenze für manifestbasierte JavaScript-Module.
3. CI-Workflow für alle vorhandenen Prüfungen vorbereiten.
4. Manuelle Browserfreigabe getrennt dokumentieren, weil automatisierte Prüfungen sie nicht ersetzen.
