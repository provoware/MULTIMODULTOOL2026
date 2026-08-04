# Linux-Releasevertrag – MULTIMODULTOOL2026

## Ziel

Der Releasekandidat ist ausschließlich für Linux x86-64 vorgesehen und wird gegen Kubuntu 22.04 LTS sowie Kubuntu 24.04 LTS geprüft. Installation, Upgrade, Rollback und Deinstallation dürfen keine persönlichen XDG-Daten verändern.

## Build-ID

Die Build-ID besteht aus der Releaseversion und den ersten 16 Hexzeichen eines SHA-256-Digests über die reproduzierbare, sortierte Nutzdateiliste:

```text
<VERSION>+<SOURCE-DIGEST-16>
```

Der Digest berücksichtigt Dateipfad, Dateiinhalt und Releaseversion. Zwei Builds mit identischem Quellstand, identischem Wheelhouse und gleichem `SOURCE_DATE_EPOCH` müssen byteidentische Archive erzeugen.

## Paketinhalt

Das Archiv enthält:

- `payload/` mit der Anwendung,
- `wheelhouse/` mit lokal installierbaren Python-Abhängigkeiten,
- `RELEASE-METADATA.json` mit Build-ID, vollständiger Dateiliste, Größe, Modus und SHA-256 je Datei,
- `release_manager.py` für Prüfung und Lebenszyklus,
- `launcher.sh` als installierten Linux-Starter.

Tar-Einträge werden sortiert, auf UID/GID 0 normalisiert und erhalten einen festen Zeitstempel. Symlinks und unbekannte Dateitypen sind im Paket nicht zugelassen.

## Abhängigkeitsprüfung

Vor einer Änderung werden geprüft:

- Linux,
- Python 3.10 oder neuer,
- Python-`venv`,
- `bash`,
- `sha256sum`,
- vollständige Paketdateien und deren SHA-256-Werte.

Die Python-GUI-Abhängigkeiten werden aus dem eingebetteten Wheelhouse mit `pip --no-index` in eine versionsbezogene virtuelle Umgebung installiert.

## Installation

Systemziel:

```text
/opt/multimodultool2026/
├── releases/<BUILD-ID>/
│   ├── app/
│   ├── venv/
│   └── RELEASE-METADATA.json
├── current -> releases/<BUILD-ID>
├── previous -> releases/<VORHERIGE-BUILD-ID>
└── install-state.json
```

Zusätzlich werden angelegt:

- `/usr/local/bin/multimodultool2026`
- `/usr/share/applications/multimodultool2026.desktop`

Ein neuer Release wird zunächst vollständig in einem temporären Slot aufgebaut. Erst nach erfolgreicher Abhängigkeitsinstallation wird der Ordner atomar aktiviert.

## Upgrade und Rollback

Beim Upgrade bleibt der bisher aktive Build unverändert unter `releases/` erhalten. `previous` wird auf den bisherigen Build gesetzt und `current` anschließend atomar auf den neuen Build umgeschaltet.

Rollback vertauscht ausschließlich die beiden geprüften Symlinkziele. Es kopiert oder überschreibt keine Nutzerdaten und führt keine Datenmigration zurück.

## Erster Start

Die Abnahme startet den installierten Python-Interpreter aus dem aktiven Slot und führt aus:

```bash
python -m src.main --validate-only
```

Damit werden Manifest, Linuxvertrag, XDG-Pfadplan und Einstellungen geprüft, ohne produktive Dateiaktionen auszuführen.

## Deinstallation

Die vollständige Programmdeinstallation entfernt:

- alle installierten Release-Slots,
- `current` und `previous`,
- Installationsstatus,
- Kommandozeilenstarter,
- Desktopdatei.

Persönliche Konfigurationen, Journale und Projekte unter XDG- oder Projektpfaden bleiben standardmäßig erhalten. Eine automatische Nutzerdatenlöschung ist nicht Bestandteil des Releasekandidaten.

## Automatische Matrix

`.github/workflows/kubuntu-release-matrix.yml` prüft getrennt:

- Kubuntu-Paketbasis 22.04 mit Python 3.10,
- Kubuntu-Paketbasis 24.04 mit Python 3.12,
- Paketprüfung,
- Neuinstallation,
- ersten Start,
- Upgrade von RC1 auf RC2,
- Rollback auf RC1,
- erneute Aktivierung von RC2,
- vollständige Programmentfernung,
- byteidentischen Doppelbuild.

## Grenzen

- Der Releasekandidat ist noch nicht kryptografisch signiert; das signierte Release-Gate bleibt `P3-009`.
- ARM64 ist nicht freigegeben.
- Persönliche XDG-Daten werden bei Deinstallation bewusst nicht gelöscht.
- Der automatisierte Test verwendet frische GitHub-Ubuntu-Runner mit installierter Kubuntu-/KDE-Paketbasis; eine zusätzliche physische Kubuntu-VM-Abnahme bleibt für `P4-009` offen.
