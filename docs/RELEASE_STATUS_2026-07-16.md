# Release-Status 2026-07-16

Dieses Protokoll beschreibt den aktuellen Stand der Release-Fertigstellung. Es ersetzt keine echte Browserfreigabe, sondern hält nachvollziehbar fest, was lokal geprüft werden kann und was bewusst offen bleibt.

## Ergebnis

- Status: Release-Kandidat mit offener manueller Browserfreigabe; die lokale Vorprüfung ist vollständig abgedeckt.
- Nutzbarkeit: Die App bleibt ohne Build-Schritt nutzbar.
- Datenlage: Keine privaten Beispiel-, Import-, Export- oder Logdaten wurden für diese Freigabe ergänzt.
- Grenze: Eine echte Chromium- und Firefox-Sichtprüfung ist in dieser Containerumgebung nicht belegbar.

## Lokal belegbare Vorprüfung

Vor einer Weitergabe sollen diese Befehle im Repository erfolgreich laufen:

```sh
python3 tests/validate_progress_consistency.py
python3 tests/validate_module_manifests.py
python3 tests/test_html_helpers.py
python3 tests/validate_genres_module.py
python3 tests/validate_module_previews.py
python3 tests/validate_quicktext_snippets.py
python3 tests/test_start_local.py
python3 tests/scan_performance_hotspots.py
python3 tests/validate_release_gate.py
python3 -m py_compile tests/validate_progress_consistency.py tests/validate_module_manifests.py tests/test_html_helpers.py tests/validate_genres_module.py tests/validate_module_previews.py tests/validate_quicktext_snippets.py tests/test_start_local.py tests/scan_performance_hotspots.py tests/validate_release_gate.py
```

Zusätzlich kann der lokale Start ohne Browseröffnung technisch geprüft werden:

```sh
python3 -m http.server 8765 --bind 127.0.0.1
curl -I http://127.0.0.1:8765/dashboard-studio-ultimate-pro-v3.1.0.html
```

## Lokales Release-Gate

Das zusätzliche Release-Gate `python3 tests/validate_release_gate.py` prüft bewusst nur dokumentierte Freigabegrenzen und vorhandene Prüfbefehle. Es ersetzt keine sichtbare Browserprüfung. Dadurch bleibt maschinell belegbar, dass der Stand ein Release-Kandidat ist, alle vorhandenen lokalen Prüfscripte im Gate abgedeckt sind und die manuelle Browserfreigabe nicht versehentlich als erledigt markiert wurde.

Die vorhandenen lokalen Prüfbefehle sind zusätzlich in `.github/workflows/release-gate.yml` hinterlegt. Dadurch werden Pushes auf `work` und `main` sowie Pull Requests mit denselben statischen Release-Prüfungen abgesichert, ohne Browserfreigabe oder Build-Schritt vorzutäuschen.

## Manuell offen vor echter Freigabe

Diese Punkte bleiben offen, weil sie eine echte Browserumgebung mit sichtbarer Oberfläche brauchen:

1. App über `./scripts/start-local.sh` in Chromium starten.
2. App über `./scripts/start-local.sh` in Firefox starten.
3. Startansicht, Kontraste, Fokusrahmen und Tastaturbedienung sichtbar prüfen.
4. In den Einstellungen **Speicher prüfen** ausführen und Ergebnis kurz protokollieren.
5. Kleinen JSON-Import, Backup-Wiederherstellung und Exportdownload mit Testdaten prüfen.
6. Falls die Schnell-Text-Speicher-Vorschau im echten Loader geladen wird, CSS gemeinsam mit `module.html` sichtbar prüfen.

## Freigabeentscheidung

Der Stand darf als lokaler Release-Kandidat weitergegeben werden, wenn die lokale Vorprüfung vollständig bestanden ist und die offenen manuellen Browserpunkte als bekannte Grenze mitgegeben werden. Eine endgültige Freigabe darf erst markiert werden, wenn die Browserpunkte geprüft und dokumentiert sind.
