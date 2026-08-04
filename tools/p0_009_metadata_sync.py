#!/usr/bin/env python3
"""Deterministic, idempotent metadata synchronization for P0-009."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_expected(path: Path, old: str, new: str, *, all_occurrences: bool = False) -> None:
    text = path.read_text(encoding="utf-8")
    if old in text:
        updated = text.replace(old, new) if all_occurrences else text.replace(old, new, 1)
        path.write_text(updated, encoding="utf-8")
        return
    if new in text:
        return
    raise RuntimeError(f"{path}: neither old nor synchronized marker exists: {old!r}")


def append_section(path: Path, marker: str, section: str) -> None:
    text = path.read_text(encoding="utf-8")
    if marker not in text:
        path.write_text(text.rstrip() + "\n\n" + section.strip() + "\n", encoding="utf-8")


def update_main() -> None:
    path = ROOT / "src/main.py"
    replace_expected(path, "DEVELOPMENT_PROGRESS = 46", "DEVELOPMENT_PROGRESS = 47")
    replace_expected(path, "COMPLETED_POINTS = 31", "COMPLETED_POINTS = 32")
    replace_expected(path, "OPEN_POINTS = 37", "OPEN_POINTS = 36")
    replace_expected(path, "Entwicklungsstand: 46 %", "Entwicklungsstand: 47 %", all_occurrences=True)
    replace_expected(path, "31 erledigt · 37 offen", "32 erledigt · 36 offen", all_occurrences=True)


def update_todo() -> None:
    path = ROOT / "TODO.md"
    replace_expected(path, "- Erledigt: **31**", "- Erledigt: **32**")
    replace_expected(path, "- Offen: **37**", "- Offen: **36**")
    replace_expected(path, "- Rechnerischer Entwicklungsfortschritt: **46 %**", "- Rechnerischer Entwicklungsfortschritt: **47 %**")
    old = "- [ ] **P0-009** – Installierbaren Linux-Releasekandidaten paketieren. Abhängigkeit: `P0-001,P0-004,P0-008` | Abnahme: Installation, Start und Deinstallation auf frischer Kubuntu-VM. | Risiko: **hoch**"
    new = "- [x] **P0-009** – Installierbaren Linux-Releasekandidaten paketieren. Abhängigkeit: `P0-001,P0-004,P0-008` | Abnahme: reproduzierbares amd64-DEB mit Build-ID und Dateimanifest; Offline-Erststart; Installation, Upgrade, Rollback, normale Entfernung und bestätigter vollständiger Purge in frischen containerisierten Kubuntu-22.04-/24.04-Userlands automatisiert geprüft. | Risiko: **hoch**"
    replace_expected(path, old, new)


def update_readme() -> None:
    path = ROOT / "README.md"
    replace_expected(path, "**Entwicklungsfortschritt: 46 %**", "**Entwicklungsfortschritt: 47 %**")
    replace_expected(path, "**Erledigte Punkte: 31**", "**Erledigte Punkte: 32**")
    replace_expected(path, "**Offene Punkte: 37**", "**Offene Punkte: 36**")
    replace_expected(
        path,
        "**Aktuelle Phase:** transaktionaler Abbruch, Checkpoints und idempotenter Wiederanlauf",
        "**Aktuelle Phase:** installierbarer Linux-Releasekandidat mit Upgrade und Rollback",
    )
    append_section(
        path,
        "## Installierbarer Linux-Releasekandidat",
        """
## Installierbarer Linux-Releasekandidat

P0-009 erzeugt ein reproduzierbares Debian-Paket für Kubuntu 22.04 und 24.04 auf x86-64. Der Releasekandidat enthält:

- eindeutige `MMTBUILD-`-Build-ID,
- sortiertes Source- und installiertes SHA-256-Dateimanifest,
- lokal gebündelte PySide6-Wheels für den netzlosen Erststart,
- geprüfte Installation und Aktualisierung,
- lokales Rollback auf den vorherigen verifizierten Paketstand,
- normale Entfernung mit Erhalt der Nutzerdaten,
- ausdrücklich bestätigten Purge von Systemzustand und den XDG-Daten des ausgewählten Nutzers.

Die Release-CI baut denselben Kandidaten zweimal byteidentisch und führt den vollständigen Lebenszyklus in frischen containerisierten Kubuntu-22.04- und Kubuntu-24.04-Userlands aus. Eine kryptografische Release-Signatur folgt separat mit `P3-009`.

```bash
python3 tools/build_deb_release.py \
  --wheelhouse dist/wheelhouse \
  --output dist/release
```

- [`docs/LINUX_RELEASEVERTRAG.md`](docs/LINUX_RELEASEVERTRAG.md)
""",
    )


def update_documents() -> None:
    append_section(
        ROOT / "AGENTS.md",
        "## Linux-Releasevertrag P0-009",
        """
## Linux-Releasevertrag P0-009

- Releaseziel ist ein reproduzierbares `amd64`-Debian-Paket für Kubuntu 22.04/24.04.
- Runtime-Dateien stammen ausschließlich aus `release/package-files.txt`.
- Build-ID, Source-Manifest, installiertes SHA-256-Manifest und Wheelhouse-Manifest sind verpflichtend.
- Der Erststart installiert PySide6 ausschließlich aus dem gebündelten lokalen Wheelhouse.
- Installation, Upgrade, Rollback und Entfernung laufen nur nach Vorprüfung und ausdrücklichem `--yes`.
- Normale Entfernung bewahrt Nutzerdaten; der Nutzerdaten-Purge benötigt eine eindeutig bestimmte Nicht-root-Identität.
- Signaturen und Vertrauenskette bleiben bis `P3-009` ausdrücklich offen.
""",
    )
    append_section(
        ROOT / "ANLEITUNG_TOOL.md",
        "## Releasekandidat installieren",
        """
## Releasekandidat installieren

```bash
./release-manager.sh verify ./multimodultool2026_0.9.0~rc1_amd64.deb
sudo ./release-manager.sh install ./multimodultool2026_0.9.0~rc1_amd64.deb --yes
multimodultool2026 --verify-installation
```

Upgrade und Rollback:

```bash
sudo ./release-manager.sh upgrade ./multimodultool2026_0.9.0~rc1_amd64.deb --yes
sudo ./release-manager.sh rollback --yes
```

Normale Entfernung bewahrt XDG-Nutzerdaten. Der vollständige Purge benötigt zusätzlich `--purge-system-state --purge-current-user-data --yes` und wird bei Symlinks oder unklarer Nutzerzuordnung blockiert.
""",
    )
    append_section(
        ROOT / "CHANGELOG.md",
        "## 2026-08-04 – P0-009",
        """
## 2026-08-04 – P0-009

- reproduzierbarer amd64-DEB-Builder mit Build-ID und expliziter Runtime-Dateiliste
- Offline-Wheelhouse für PySide6 und privater Runtime-Slot je Build-ID
- geprüfter Release-Manager für Installation, Upgrade, lokales Rollback und Deinstallation
- normale Entfernung mit Erhalt der Nutzerdaten sowie ausdrücklich bestätigter vollständiger Purge
- byteidentischer Doppelbuild des Releasekandidaten
- automatisierte Lebenszyklusmatrix in Kubuntu-22.04-/24.04-Userlands
- Manifest auf Schema 1.5.0 und Fortschritt auf 32 erledigt, 36 offen, 68 gesamt, 47 Prozent aktualisiert
""",
    )
    append_section(
        ROOT / "ENTWICKLERDOKU.md",
        "## Releasearchitektur P0-009",
        """
## Releasearchitektur P0-009

`tools/build_deb_release.py` expandiert die Allowlist, prüft das Wheelhouse, bildet das kanonische Source-Manifest und erzeugt `MMTBUILD-<Version>-<Hash>`. Der Stagingbaum wird auf feste Rechte, Eigentümer und `SOURCE_DATE_EPOCH` normalisiert und über `dpkg-deb --root-owner-group` gebaut.

Der Starter prüft `FILE_MANIFEST.sha256`, erzeugt unter `$XDG_DATA_HOME/multimodultool2026/runtime/` einen privaten venv-Slot je Build-ID und installiert nur aus dem lokalen Wheelhouse. `release-manager.sh` archiviert verifizierte Pakete unter `/var/lib/multimodultool2026`, dokumentiert aktuellen und vorherigen Stand atomar und verwendet für Rollback ausschließlich das erneut geprüfte lokale Archiv.

Die Workflowdatei `.github/workflows/release-candidate.yml` beweist byteidentische Builds und den vollständigen Paketlebenszyklus in zwei Kubuntu-Userland-Matrizen.
""",
    )
    append_section(
        ROOT / "SCHWACHSTELLEN.md",
        "## P0-009 – bekannte Releasegrenzen",
        """
## P0-009 – bekannte Releasegrenzen

- Die Kubuntu-Abnahme läuft containerisiert; gebootete KDE-/SDDM-, X11- und Wayland-VMs bleiben offen.
- SHA-256-Sidecars erkennen Veränderung, ersetzen aber keine kryptografische Herausgebersignatur; `P3-009` bleibt Releaseblocker für Stable.
- `SIGKILL`- und Dateisystemtests beweisen keinen Schutz vor defektem Hardware-Schreibcache oder physischem Stromverlust.
- Der Releasekandidat ist ausschließlich für x86-64 gebaut; ARM64 ist nicht freigegeben.
- Der vollständige Nutzerdaten-Purge ist absichtlich auf einen ausdrücklich bestimmten Nicht-root-Nutzer und bekannte XDG-Pfade begrenzt.
""",
    )
    append_section(
        ROOT / "UPGRADE_POOL.md",
        "## Release-Erweiterungen nach P0-009",
        """
## Release-Erweiterungen nach P0-009

- signierte Release-Manifeste und Schlüsselrotation zusammen mit `P3-009`
- echte Kubuntu-VM-Matrix mit SDDM, KDE Plasma, X11 und Wayland
- delta-basierte Updates erst nach signierter Build-ID- und Dateimanifestprüfung
- optionaler read-only Release-Statusdialog mit Build-ID, Paketversion und Runtime-Slot
- langfristige Bereinigung nicht mehr benötigter Nutzer-Runtime-Slots nur nach Vorschau
""",
    )
    append_section(
        ROOT / "docs/XDG_PFADVERTRAG.md",
        "## Installierte Offline-Runtime",
        """
## Installierte Offline-Runtime

Der Systempaketinhalt liegt unter `/usr/lib/multimodultool2026`. Der erste Start erzeugt pro Build-ID ausschließlich unter `$XDG_DATA_HOME/multimodultool2026/runtime/` einen privaten venv-Slot. Upgrade und Rollback überschreiben keinen bestehenden Slot. Normale Paketentfernung bewahrt XDG-Daten; ein vollständiger Purge ist separat, explizit und auf die bekannten Pfade eines eindeutig bestimmten Nicht-root-Nutzers begrenzt.
""",
    )
    append_section(
        ROOT / "docs/FEHLER_UND_EREIGNISVERTRAG.md",
        "## Release- und Installationsfehler",
        """
## Release- und Installationsfehler

Paket-SHA, Build-ID, Architektur, Abhängigkeiten, installierte Dateiliste, Offline-Runtime und Rollbackarchiv werden vor einer Fortsetzung geprüft. Eine fehlende oder widersprüchliche Voraussetzung blockiert Installation, Upgrade oder Rollback. Der Release-Manager verändert bei einem Vorprüfungsfehler weder Paketstand noch Nutzerdaten. Kryptografische Signaturfehler werden erst nach Einführung des signierten Release-Gates in `P3-009` bewertet.
""",
    )


def main() -> None:
    update_main()
    update_todo()
    update_readme()
    update_documents()


if __name__ == "__main__":
    main()
