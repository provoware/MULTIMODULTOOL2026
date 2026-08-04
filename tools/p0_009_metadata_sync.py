#!/usr/bin/env python3
"""One-shot deterministic metadata synchronization for P0-009."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one occurrence of {old!r}, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_all_required(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"{path}: marker missing: {old!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def update_main() -> None:
    path = ROOT / "src/main.py"
    replace_once(path, "DEVELOPMENT_PROGRESS = 46", "DEVELOPMENT_PROGRESS = 47")
    replace_once(path, "COMPLETED_POINTS = 31", "COMPLETED_POINTS = 32")
    replace_once(path, "OPEN_POINTS = 37", "OPEN_POINTS = 36")
    replace_all_required(path, "Entwicklungsstand: 46 %", "Entwicklungsstand: 47 %")
    replace_all_required(path, "31 erledigt · 37 offen", "32 erledigt · 36 offen")


def update_todo() -> None:
    path = ROOT / "TODO.md"
    replace_once(path, "- Erledigt: **31**", "- Erledigt: **32**")
    replace_once(path, "- Offen: **37**", "- Offen: **36**")
    replace_once(path, "- Rechnerischer Entwicklungsfortschritt: **46 %**", "- Rechnerischer Entwicklungsfortschritt: **47 %**")
    old = "- [ ] **P0-009** – Installierbaren Linux-Releasekandidaten paketieren. Abhängigkeit: `P0-001,P0-004,P0-008` | Abnahme: Installation, Start und Deinstallation auf frischer Kubuntu-VM. | Risiko: **hoch**"
    new = "- [x] **P0-009** – Installierbaren Linux-Releasekandidaten paketieren. Abhängigkeit: `P0-001,P0-004,P0-008` | Abnahme: reproduzierbares amd64-DEB mit Build-ID und Dateimanifest; Offline-Erststart; Installation, Upgrade, Rollback, normale Entfernung und bestätigter vollständiger Purge in frischen containerisierten Kubuntu-22.04-/24.04-Userlands automatisiert geprüft. | Risiko: **hoch**"
    replace_once(path, old, new)


def update_readme() -> None:
    path = ROOT / "README.md"
    replace_once(path, "**Entwicklungsfortschritt: 46 %**", "**Entwicklungsfortschritt: 47 %**")
    replace_once(path, "**Erledigte Punkte: 31**", "**Erledigte Punkte: 32**")
    replace_once(path, "**Offene Punkte: 37**", "**Offene Punkte: 36**")
    replace_once(
        path,
        "**Aktuelle Phase:** transaktionaler Abbruch, Checkpoints und idempotenter Wiederanlauf",
        "**Aktuelle Phase:** installierbarer Linux-Releasekandidat mit Upgrade und Rollback",
    )
    text = path.read_text(encoding="utf-8")
    marker = "## Installierbarer Linux-Releasekandidat"
    if marker not in text:
        section = """

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
"""
        text += section
    doc_link = "- [`docs/LINUX_RELEASEVERTRAG.md`](docs/LINUX_RELEASEVERTRAG.md)"
    if doc_link not in text:
        text += "\n\n" + doc_link + "\n"
    path.write_text(text, encoding="utf-8")


def main() -> None:
    update_main()
    update_todo()
    update_readme()


if __name__ == "__main__":
    main()
