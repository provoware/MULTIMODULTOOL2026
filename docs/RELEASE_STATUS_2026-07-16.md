# Release-Status 2026-07-16

Dieses Protokoll beschreibt den aktuellen Stand der Release-Fertigstellung. Es ersetzt keine echte Browserfreigabe, sondern hält nachvollziehbar fest, was lokal geprüft werden kann und was bewusst offen bleibt.

## Ergebnis

- Status: lokal finalisierter Release-Kandidat mit offener manueller Browserfreigabe; die lokale Vorprüfung ist vollständig abgedeckt.
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

Das zusätzliche Release-Gate `python3 tests/validate_release_gate.py` prüft bewusst nur dokumentierte Freigabegrenzen, die ausfüllbare Browser-Protokollvorlage, vorhandene Prüfbefehle und den vollständigen Sammel-Syntaxcheck. Es ersetzt keine sichtbare Browserprüfung. Dadurch bleibt maschinell belegbar, dass der Stand ein Release-Kandidat ist, alle vorhandenen lokalen Prüfscripte im Gate abgedeckt sind und die manuelle Browserfreigabe nicht versehentlich als erledigt markiert wurde.

Die vorhandenen lokalen Prüfbefehle sind zusätzlich in `.github/workflows/release-gate.yml` hinterlegt. Dadurch werden Pushes auf `work` und `main` sowie Pull Requests mit denselben statischen Release-Prüfungen abgesichert, ohne Browserfreigabe oder Build-Schritt vorzutäuschen.


## Optional automatisierbare Browser-Smoke-Prüfung

Ja, ein großer Teil der offenen Browserpunkte kann zusätzlich vollautomatisch geprüft werden. Dafür liegt `tests/browser_release_smoke.py` bereit. Der Test startet einen lokalen HTTP-Server, öffnet die App in Playwright-Browsern, prüft den App-Start, führt die Speicherprüfung aus, erstellt und lädt ein lokales Backup, importiert einen kleinen JSON-Teststand aus dem aktuellen Browser-Speicher und kontrolliert einen Exportdownload.

Beispiel für eine strenge Freigabeumgebung mit installierten Browsern:

```sh
python3 tests/browser_release_smoke.py --browser chromium --require-browser
python3 tests/browser_release_smoke.py --browser firefox --require-browser
```

Ohne `--require-browser` überspringt der Test fehlende Browser oder fehlendes Playwright bewusst mit einer klaren Meldung und beendet den Lauf ohne Freigabefehler. Das ist für Entwicklungscontainer hilfreich, ersetzt aber keine Freigabe. Mit `--require-browser` bleibt der Lauf streng: fehlendes Playwright, ein fehlender Browser oder kein tatsächlich ausgeführter Browser-Test führen zu einem Fehler. Die automatische Prüfung bewertet außerdem keine menschliche Lesbarkeit, keinen echten Kontrasteindruck und keine Bedienqualität mit sichtbarer Oberfläche; diese Sichtprüfung bleibt im Browser-Freigabeprotokoll offen, bis sie auf einem echten Chromium- und Firefox-Arbeitsplatz dokumentiert wurde.

## Manuell offen vor echter Freigabe

Diese Punkte bleiben offen, weil sie eine echte Browserumgebung mit sichtbarer Oberfläche brauchen. Die ausfüllbare Vorlage liegt in `docs/BROWSER_RELEASE_PROTOCOL_2026-07-16.md` und darf erst nach tatsächlicher Prüfung abgeschlossen werden:

1. App über `./scripts/start-local.sh` in Chromium starten.
2. App über `./scripts/start-local.sh` in Firefox starten.
3. Startansicht, Kontraste, Fokusrahmen und Tastaturbedienung sichtbar prüfen.
4. In den Einstellungen **Speicher prüfen** ausführen und Ergebnis kurz protokollieren.
5. Kleinen JSON-Import, Backup-Wiederherstellung und Exportdownload mit Testdaten prüfen.
6. Falls die Schnell-Text-Speicher-Vorschau im echten Loader geladen wird, CSS gemeinsam mit `module.html` sichtbar prüfen.

## Freigabeentscheidung

Der Stand darf als lokal finalisierter Release-Kandidat weitergegeben werden, wenn die lokale Vorprüfung vollständig bestanden ist und die offenen manuellen Browserpunkte als bekannte Grenze mitgegeben werden. Eine endgültige Freigabe darf erst markiert werden, wenn die Browserpunkte geprüft und dokumentiert sind. Die Dokumentation erfolgt in `docs/BROWSER_RELEASE_PROTOCOL_2026-07-16.md`.
