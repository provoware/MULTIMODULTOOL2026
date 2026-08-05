# ANLEITUNG_TOOL

## Unterstützte Systeme

Kubuntu 22.04/24.04, KDE Plasma, X11 oder Wayland, x86-64. Andere Systeme werden vor produktiven Zugriffen kontrolliert blockiert.

## Start

```bash
chmod +x start.sh setup.sh
./start.sh
```

Beim Start werden Linux, Python, PySide6, Manifest, XDG-Pfade, Einstellungen, Ereignisjournal und Single-Instance-Laufzeitpfad geprüft.

Rein lesende Prüfungen:

```bash
python3 -m src.main --validate-only
python3 -m src.main --paths-only
python3 -m src.main --settings-only
python3 -m src.main --show-diagnostics
python3 -m src.main --help
```

## Produktiven Projektordner wählen

1. **Projektordner wählen …** anklicken.
2. Nur den tatsächlichen Arbeitsordner auswählen, nicht `/`, das eigene Home-Verzeichnis oder einen Systemordner.
3. Die grüne Projektprüfung abwarten.
4. Bei Rot nichts manuell umgehen. Ursache und sicheren nächsten Schritt aus Dialog oder Tooltip übernehmen.

Vor der Freigabe prüft das Tool:

- absoluten Linux-Pfad,
- Eigentümer des Projektordners,
- Lese-, Schreib- und Zugriffsrechte,
- Symlink-Komponenten,
- Mount- und Dateisystemgrenze,
- freien Speicher,
- privaten Steuerordner `.multimodultool2026`.

## Dateibestand analysieren

**Bestand analysieren** liest ausschließlich Metadaten. Erfasst werden Dateityp, Größe, Änderungszeit, Endung, Kategorie, Symlinkstatus und Namenshinweise.

- Symlinks werden gemeldet, aber nicht verfolgt.
- Mountgrenzen werden nicht betreten.
- der interne Steuerordner wird nicht analysiert,
- eine kontrolliert abgebrochene Analyse verändert keine Projektdatei.

## Duplikate suchen

1. Nach der Analyse **Duplikate per SHA-256** anklicken.
2. Das Tool bildet zuerst Größenklassen.
3. Nur Größenklassen mit mindestens zwei regulären Dateien werden streamend gehasht.
4. Vor und nach dem Hashen wird der Dateifingerabdruck geprüft.

Die Duplikatsuche ist rein lesend. Sie löscht, verschiebt, verlinkt oder ersetzt keine Datei.

## Dateien organisieren

Unter **Organisieren** steht eine der Regeln zur Auswahl:

- nach Dateityp,
- nach Dateiendung,
- nach Änderungsjahr.

Das Ziel liegt unter `Sortiert/` innerhalb des geprüften Projekts. Zuerst wird eine vollständige Vorher-/Nachher-Vorschau erzeugt. Bereits belegte Ziele, doppelte Ziele, Symlinks, Mehrfach-Hardlinks oder Dateisystemwechsel blockieren den gesamten Plan.

## Massenumbenennung

Unter **Massenumbenennen** können markierte oder alle analysierten Dateien gewählt werden. Kombinierbar sind:

- Präfix,
- Suffix vor der Dateiendung,
- Suchen und Ersetzen,
- Beibehalten, klein oder GROSS,
- fortlaufende Nummer mit Startwert und Stellenzahl.

Dateiendungen bleiben erhalten. Leere, zu lange, unsichere, doppelte, zyklische oder bereits belegte Zielnamen werden vor der Ausführung blockiert.

## Vorschau und Bestätigung

Jeder produktive Plan zeigt:

- eindeutige Operations-ID,
- Typ der Operation,
- Anzahl der Dateien,
- vollständige Vorher-/Nachher-Pfade,
- SHA-256-Planhash,
- Ergebnis der Konfliktprüfung.

Erst **Geprüften Plan ausführen …** und eine zweite Bestätigung starten die Dateiaktion. Es gibt kein stilles Überschreiben.

## Checkpoint, Fortsetzung und Rückgängig

Interner Speicherort:

```text
<Projekt>/.multimodultool2026/operations/<MMTOP-ID>/
├── plan.json
├── checkpoint.json
└── operation.lock
```

- Operationsordner: `0700`
- Plan, Checkpoint und Sperrdatei: `0600`
- exklusive Linux-`flock`-Sperre
- atomare Dateischritte per `os.replace`
- Fingerabdruck aus Geräte-ID, Inode, Modus, Größe, Änderungszeit und Linkanzahl

Nach einer Unterbrechung gleicht das Tool Quelle und Ziel mit dem unveränderlichen Plan ab. Eine Fortsetzung wiederholt keinen bereits bestätigten Dateischritt. Rückgängig arbeitet in umgekehrter Reihenfolge und blockiert, sobald ein Ziel verändert oder ein Originalpfad wieder belegt wurde.

## Berichte

Analyse- und Operationsberichte werden privat gespeichert:

```text
<Projekt>/.multimodultool2026/reports/
```

JSON und Markdown enthalten ausschließlich projekt-relative Pfade. Es gibt keinen automatischen Upload.

## Hilfe und Tooltips

Der Menüpunkt **Hilfe** erklärt Projektwahl, Analyse, Duplikate, Vorschau, Abbruch, Fortsetzung, Rückgängig, Berichte und Signaturprüfung. Tooltips nennen Zweck, Sicherheitsgrenze und Blocker. Weiterhin nicht freigegebene Funktionen bleiben sichtbar und begründen ihre Sperre.

## Fertige `_save_`-Dateien

Erst nach erfolgreichem reproduzierbarem Build und grüner Kubuntu-22.04-/24.04-Matrix:

```text
multimodultool2026_<version>_amd64_save_.deb
multimodultool2026_<version>_amd64_save_.deb.sha256
multimodultool2026-<version>-amd64_save_.tar.gz
release-manager_save_.sh
CANDIDATE_BUILD_RESULT_save_.json
RELEASE_STATUS_save_.json
```

## P3-009: kryptografische Signatur prüfen

Der `main`-Workflow signiert jede der sechs Primärdateien schlüssellos per Sigstore/Cosign. Zusätzlich entstehen ein SHA-256-Releasemanifest und dessen Signaturbundle.

Beispiel:

```bash
cosign verify-blob \
  --bundle 'multimodultool2026_<version>_amd64_save_.deb.sigstore.json' \
  --certificate-identity-regexp '^https://github.com/provoware/MULTIMODULTOOL2026/.github/workflows/release-candidate.yml@refs/(heads/main|tags/v.*)$' \
  --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' \
  'multimodultool2026_<version>_amd64_save_.deb'
```

Gesamtprüfung:

```bash
python3 tools/sign_release_artifacts.py verify \
  --directory dist/release-signed \
  --identity-regexp '^https://github.com/provoware/MULTIMODULTOOL2026/.github/workflows/release-candidate.yml@refs/(heads/main|tags/v.*)$' \
  --issuer 'https://token.actions.githubusercontent.com'
```

Im Repository wird kein privater Signaturschlüssel gespeichert. Das kurzlebige OIDC-Recht gilt nur im isolierten Signaturjob.

## Installation

```bash
./release-manager_save_.sh verify ./multimodultool2026_<version>_amd64_save_.deb
sudo ./release-manager_save_.sh install ./multimodultool2026_<version>_amd64_save_.deb --yes
multimodultool2026 --verify-installation
```

## Entwicklerprüfungen

```bash
python3 tools/validate_repository.py
python3 -m unittest tests.test_productive_workflow -v
python3 -m unittest tests.test_sign_release_artifacts -v
python3 -m unittest tests.test_finalize_release_artifacts -v
python3 -m unittest tests.test_run_control_sigkill -v
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_gui_offscreen -v
bash -n tests/helpers/kubuntu_release_lifecycle.sh
```
