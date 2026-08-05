# MULTIMODULTOOL2026

> **Entwicklungsfortschritt: 62 %**  
> **Erledigte Punkte: 42**  
> **Offene Punkte: 26**  
> **Gesamtpunkte: 68**  
> **Aktuelle Phase:** P1-001 und P1-003 bis P1-009 sowie P3-009 abgenommen; P1-002 bleibt offen  
> **Letzte Fortschrittsprüfung:** 2026-08-05

> **Plattformvertrag:** ausschließlich Linux-Desktop; primär Kubuntu 22.04 LTS und Kubuntu 24.04 LTS unter KDE Plasma, X11 oder Wayland auf x86-64.

MULTIMODULTOOL2026 ist ein lokal arbeitendes Linux-Desktop-Werkzeug für sichere Dateiorganisation. Der Schutzkern für XDG-Pfade, Einstellungen, Fehlerereignisse, Single-Instance, Projektpapierkorb, Undo/Redo, Abbruch, Wiederanlauf und reproduzierbare Debian-Pakete bleibt erhalten. Der produktive Dateiworkflow wird jetzt durch einen vollständig vorvalidierten Startassistenten mit getrenntem projektinternem Ziel und drei Sicherheitsmodi freigegeben; das schlüssellose Sigstore-Release-Gate ist kryptografisch nachgewiesen.

Die formale Fortschrittszahl enthält P1-001 nach grüner Unit-, Qt-Offscreen-, reproduzierbarer Build- und Kubuntu-22.04-/24.04-Abnahme. P1-002 bleibt bis zur getrennten Navigationserprobung mit eindeutigem Aktivzustand und Zurück-Pfad offen.

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

## Geführter und produktiver Arbeitsablauf

1. **Startassistent öffnen:** Projektordner und davon getrennten Zielordner ausschließlich über Dialoge wählen.
2. **Sicherheitsmodus wählen:** `Nur prüfen`, `Vorschau und Bericht` oder `Produktiv mit Bestätigung`.
3. **Vollständig vorvalidieren:** Eigentümer, Rechte, Symlink-Komponenten, Mountgrenzen, Dateisystem, freier Speicher sowie Geräte-ID und Inode des Zielordners werden geprüft.
4. **Zusammenfassung bestätigen:** Ohne verständliche Freigabeübersicht bleiben Analyse, Bericht und Dateiänderung gesperrt.
5. **Bestand analysieren:** Typ, Größe, Änderungszeit, Dateiendung, Kategorie und Namenshinweise werden rein lesend erfasst.
6. **Duplikate suchen:** Nur reguläre größenidentische Dateien werden streamend per SHA-256 verglichen. Es erfolgt keine automatische Löschung.
7. **Vorschau erzeugen:** Organisation nutzt ausschließlich den bestätigten Zielordner; Massenumbenennung zeigt jeden Vorher-/Nachher-Pfad und bindet ihn an einen Planhash.
8. **Ausdrücklich bestätigen:** Doppelte, belegte, unsichere oder zyklische Ziele blockieren den gesamten Plan. Produktive Ausführung benötigt eine zweite Bestätigung.
9. **Ausführen und nachprüfen:** Jeder Schritt nutzt `os.replace`, einen privaten Checkpoint und einen gebundenen Dateifingerabdruck.
10. **Fortsetzen oder rückgängig:** Nach einer Unterbrechung werden Quelle und Ziel abgeglichen. Undo arbeitet rückwärts und nur bei unveränderten Dateien.
11. **Bericht speichern:** JSON und Markdown enthalten ausschließlich projekt-relative Pfade; im Modus `Nur prüfen` bleibt auch dieser Schreibzugriff gesperrt.

### Sicherheitsmodi

| Modus | Analyse und Vorschau | Bericht | Dateiänderung |
|---|---:|---:|---:|
| `Nur prüfen` | erlaubt | gesperrt | gesperrt |
| `Vorschau und Bericht` | erlaubt | erlaubt | gesperrt |
| `Produktiv mit Bestätigung` | erlaubt | erlaubt | erst nach vollständiger Vorschau und zweiter Bestätigung |

### Harte Dateigrenzen

- Projekt- und Zielordner müssen getrennt sein
- Ziel bleibt innerhalb der geprüften Projektgrenze und auf demselben Dateisystem
- kein stilles Überschreiben
- keine Symlinkverfolgung
- keine produktive Verarbeitung von Mehrfach-Hardlinks
- kein Wechsel über Dateisystem- oder Mountgrenzen
- keine produktive Verarbeitung des internen Steuerordners
- private Operationsordner `0700`, private Plan-/Checkpointdateien `0600`
- Fingerabdruck aus Geräte-ID, Inode, Modus, Größe, Änderungszeit und Linkanzahl
- Zielordner wird vor jeder kritischen Freigabe erneut gegen Geräte-ID, Inode und Eigentümer geprüft

`P1-002` bleibt offen: Die kachelbasierte Navigation benötigt noch einen durchgehend geprüften aktiven Zustand, eine eindeutige Escape-/Zurück-Hierarchie und die sichere Rückkehr zum tatsächlichen Auslöser.

## Release-Dateistatus

Die Kennzeichnung `_save_` wird ausschließlich auf geprüfte Releaseausgaben angewendet. **Quelldateien werden nicht umbenannt**, weil zusätzliche Namensanhänge Python-Imports, Startpfade, Desktopdateien, Paketmanifeste und Wartungsskripte beschädigen würden.

| Fertige Dateien nach grüner Kubuntu-Matrix | Unfertig oder nicht freigegeben |
|---|---|
| `multimodultool2026_<version>_amd64_save_.deb` | P1-002: aktiver Kachelzustand, Zurück-Pfad und Fokus-Rückkehr |
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
- Hauptzweignachweis: Run `30970761299`, Signaturjob `92196203330`, Artefakt `8916623377`, Archiv-SHA-256 `fad8a42f2132722cf89ae659d75887b8bd12c33557387d2d13b47778f31eedf3`

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
python3 -m unittest tests.test_start_assistant -v
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
