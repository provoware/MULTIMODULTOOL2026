# MULTIMODULTOOL2026

> **Entwicklungsfortschritt: 49 %**  
> **Erledigte Punkte: 33**  
> **Offene Punkte: 35**  
> **Gesamtpunkte: 68**  
> **Aktuelle Phase:** produktiver P1-Dateikern und P3-009 in Releaseabnahme  
> **Letzte Fortschrittsprüfung:** 2026-08-05

> **Plattformvertrag:** ausschließlich Linux-Desktop; primär Kubuntu 22.04 LTS und Kubuntu 24.04 LTS unter KDE Plasma, X11 oder Wayland auf x86-64.

MULTIMODULTOOL2026 ist ein lokal arbeitendes Linux-Desktop-Werkzeug für sichere Dateiorganisation. Der Schutzkern für XDG-Pfade, Einstellungen, Fehlerereignisse, Single-Instance, Projektpapierkorb, Undo/Redo, Abbruch, Wiederanlauf und reproduzierbare Debian-Pakete bleibt erhalten. Neu hinzugekommen sind ein produktiver, vorschaugebundener Dateiworkflow sowie ein schlüsselloses Sigstore-Release-Gate.

Die formale Fortschrittszahl bleibt bis zum vollständig signierten `main`-Nachweis und der getrennten P1-001-Startassistentenabnahme konservativ unverändert.

## Schnellstart

```bash
chmod +x start.sh setup.sh
./start.sh
```

Rein lesende Prüfungen:

```bash
python3 -m src.main --validate-only
python3 -m src.main --paths-only
python3 -m src.main --settings-only
python3 -m src.main --show-diagnostics
python3 -m src.main --help
```

## Produktiver Arbeitsablauf

1. **Projektordner wählen:** Eigentümer, Rechte, Symlink-Komponenten, Mountgrenzen und freier Speicher werden geprüft.
2. **Bestand analysieren:** Typ, Größe, Änderungszeit, Dateiendung, Kategorie und Namenshinweise werden rein lesend erfasst.
3. **Duplikate suchen:** Nur reguläre größenidentische Dateien werden streamend per SHA-256 verglichen. Es erfolgt keine automatische Löschung.
4. **Vorschau erzeugen:** Organisation oder Massenumbenennung zeigt jeden Vorher-/Nachher-Pfad und bindet ihn an einen Planhash.
5. **Ausdrücklich bestätigen:** Doppelte, belegte, unsichere oder zyklische Ziele blockieren den gesamten Plan.
6. **Ausführen und nachprüfen:** Jeder Schritt nutzt `os.replace`, einen privaten Checkpoint und einen gebundenen Dateifingerabdruck.
7. **Fortsetzen oder rückgängig:** Nach einer Unterbrechung werden Quelle und Ziel abgeglichen. Undo arbeitet rückwärts und nur bei unveränderten Dateien.
8. **Bericht speichern:** JSON und Markdown enthalten ausschließlich projekt-relative Pfade.

### Harte Dateigrenzen

- kein stilles Überschreiben
- keine Symlinkverfolgung
- keine produktive Verarbeitung von Mehrfach-Hardlinks
- kein Wechsel über Dateisystem- oder Mountgrenzen
- keine produktive Verarbeitung des internen Steuerordners
- private Operationsordner `0700`, private Plan-/Checkpointdateien `0600`
- Fingerabdruck aus Geräte-ID, Inode, Modus, Größe, Änderungszeit und Linkanzahl

`P1-001` bleibt teilweise offen: Ein eigener Startassistent mit separat wählbarem Ziel und Sicherheitsmodus folgt als kleine Bedieniteration. Die jetzt produktiven Operationen bleiben absichtlich innerhalb eines geprüften Projektordners.

## Release-Dateistatus

Die Kennzeichnung `_save_` wird ausschließlich auf geprüfte Releaseausgaben angewendet. **Quelldateien werden nicht umbenannt**, weil zusätzliche Namensanhänge Python-Imports, Startpfade, Desktopdateien, Paketmanifeste und Wartungsskripte beschädigen würden.

| Fertige Dateien nach grüner Kubuntu-Matrix | Unfertig oder nicht freigegeben |
|---|---|
| `multimodultool2026_<version>_amd64_save_.deb` | P1-001: eigener Ziel-/Sicherheitsmodus im Startassistenten |
| `multimodultool2026_<version>_amd64_save_.deb.sha256` | P2: vollständige Tastatur-, Zoom-, Kontrast- und Responsive-Abnahme |
| `multimodultool2026-<version>-amd64_save_.tar.gz` | P3: Journalrotation, Modulgrenzen, Abdeckung, Qualität und Migration |
| `release-manager_save_.sh` | P4: optionale Medien-, Plugin- und portable Funktionen |
| `CANDIDATE_BUILD_RESULT_save_.json` | Physische KDE-/X11-/Wayland-Abnahme |
| `RELEASE_STATUS_save_.json` | Veröffentlichung als endgültiges Stable-Release |

Nicht fertige Baseline-Pakete, Rohlogs, Phasendateien und Exit-Code-Nachweise bleiben Test- beziehungsweise Diagnoseartefakte und erhalten bewusst kein `_save_`.

Verbindliche Klassifikation: [`release/release-status.json`](release/release-status.json)

## P3-009: kryptografisch signierte Ausgabe

Nach reproduzierbarem Build, grüner Kubuntu-22.04-/24.04-Matrix und `_save_`-Finalisierung signiert ein isolierter GitHub-Actions-Job exakt die sechs Primärdateien:

- Sigstore/Cosign **keyless OIDC**
- kein langlebiger privater Schlüssel im Repository
- je Primärdatei `<datei>.sigstore.json`
- `SIGNED_RELEASE_MANIFEST_save_.json` mit SHA-256 und Dateigröße
- `SIGNED_RELEASE_MANIFEST_save_.json.sigstore.json`
- Prüfung der Workflowidentität und des Ausstellers `https://token.actions.githubusercontent.com`
- insgesamt exakt 14 Dateien im signierten Workflowartefakt

Lokale Prüfung eines Bundles:

```bash
cosign verify-blob \
  --bundle '<datei>.sigstore.json' \
  --certificate-identity-regexp '^https://github.com/provoware/MULTIMODULTOOL2026/.github/workflows/release-candidate.yml@refs/(heads/main|tags/v.*)$' \
  --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' \
  '<datei>'
```

Vollständige automatisierte Prüfung:

```bash
python3 tools/sign_release_artifacts.py verify \
  --directory dist/release-signed \
  --identity-regexp '^https://github.com/provoware/MULTIMODULTOOL2026/.github/workflows/release-candidate.yml@refs/(heads/main|tags/v.*)$' \
  --issuer 'https://token.actions.githubusercontent.com'
```

## Automatische Prüfungen

```bash
python3 tools/validate_repository.py
python3 -m unittest tests.test_productive_workflow -v
python3 -m unittest tests.test_sign_release_artifacts -v
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_gui_offscreen -v
python3 -m unittest discover -s tests -p "test_*.py" -v
```

Der Releaseworkflow baut Baseline und Kandidat reproduzierbar, vergleicht den Kandidaten byteidentisch, prüft beide Kubuntu-Lebenszyklen, finalisiert die sechs `_save_`-Dateien und signiert ausschließlich auf `main` oder einem Versionstag.

## Sicherheitskern

- private XDG-App-Verzeichnisse `0700`, private Dateien `0600`
- eine Primärinstanz über Unix-Domain-Socket und Linux-Peer-UID
- atomarer Projektpapierkorb ohne Copy-delete-Fallback
- append-only Undo-/Redo-Journal mit SHA-256-Hashkette
- unveränderliche Lauf- und Operationspläne, atomare Checkpoints und `flock`
- kontrollierte Abbruchpunkte und idempotenter Wiederanlauf
- rein lesende Diagnose- und Transaktionsansichten
- kein stilles Überschreiben, automatisches Duplikatlöschen, Diagnoseupload oder automatische Reparatur
