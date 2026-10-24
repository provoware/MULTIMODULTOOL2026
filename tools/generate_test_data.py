#!/usr/bin/env python3
"""Reproduzierbare, ausschließlich synthetische Dateibestände für Linux-Tests.

Der Aufruf benötigt einen neuen, noch nicht vorhandenen Zielordner. Vorhandene
Verzeichnisse und Dateien werden niemals überschrieben oder gelöscht.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ID = "MMT-P3-004-v1"
# Feste Bytes statt Zufallszahlen, Zeitstempeln oder personenbezogenen Inhalten.
_DUPLICATE = bytes(range(256)) * 16
FILES: dict[str, bytes] = {
    "archiv/bericht.txt": "Synthetischer Bericht A\n".encode("utf-8"),
    "archiv/bericht-kopie.txt": "Synthetischer Bericht A\n".encode("utf-8"),
    "dubletten/alpha.bin": _DUPLICATE,
    "dubletten/beta.bin": _DUPLICATE,
    "kollision/ordner-a/gleich.txt": b"Version A\n",
    "kollision/ordner-b/gleich.txt": b"Version B\n",
    "leer/leer.txt": b"",
    "sonderzeichen/Grüße mit Leerzeichen.txt": "Nur Testdaten.\n".encode("utf-8"),
    "sortieren/Foto.JPG": b"synthetic-file-not-a-real-image\n",
    "tief/ebene-1/ebene-2/info.md": b"# Synthetische Testdatei\n",
}


class FixtureError(ValueError):
    """Ziel nicht sicher für einen ausschließlich neuen Testdatenbestand."""


def _check_destination(destination: Path) -> None:
    if not destination.is_absolute():
        raise FixtureError("Der Zielpfad muss absolut sein.")
    if os.path.lexists(destination):
        raise FixtureError("Das Ziel existiert bereits; kein Überschreiben erlaubt.")
    parent = destination.parent
    if not parent.is_dir():
        raise FixtureError("Der direkte Elternordner muss bereits existieren.")
    for component in (parent, *parent.parents):
        if component.is_symlink():
            raise FixtureError("Symbolische Verknüpfung im Elternpfad blockiert.")
    resolved = destination.resolve(strict=False)
    if resolved == REPOSITORY_ROOT or REPOSITORY_ROOT in resolved.parents:
        raise FixtureError("Testdaten dürfen nicht im Quellverzeichnis entstehen.")


def _write_new(path: Path, data: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def create_fixture(destination: Path) -> dict[str, object]:
    """Einen neuen synthetischen Bestand erzeugen, ohne bestehende Daten anzufassen.

    Bei einem Schreibfehler bleibt ein erkennbar unvollständiger Testordner
    stehen; es erfolgt ausdrücklich keine automatische Löschung.
    """
    _check_destination(destination)
    try:
        destination.mkdir(mode=0o700, exist_ok=False)
    except FileExistsError as exc:
        raise FixtureError("Ziel wurde zwischen Prüfung und Anlage belegt.") from exc

    records: list[dict[str, object]] = []
    for relative, data in sorted(FILES.items()):
        path = destination / relative
        current = destination
        for component in Path(relative).parts[:-1]:
            current = current / component
            current.mkdir(mode=0o700, exist_ok=True)
        _write_new(path, data)
        records.append({
            "path": relative,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })

    manifest: dict[str, object] = {
        "schemaVersion": 1,
        "fixtureId": FIXTURE_ID,
        "files": records,
        "duplicateGroups": [
            ["archiv/bericht-kopie.txt", "archiv/bericht.txt"],
            ["dubletten/alpha.bin", "dubletten/beta.bin"],
        ],
        "collisionNames": [
            "kollision/ordner-a/gleich.txt",
            "kollision/ordner-b/gleich.txt",
        ],
    }
    payload = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    _write_new(destination / "manifest.json", payload)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="Neuer absoluter Zielordner")
    arguments = parser.parse_args(argv)
    try:
        manifest = create_fixture(arguments.output)
    except (FixtureError, OSError) as exc:
        print(f"ROT: Testdaten nicht vollständig erzeugt: {exc}", file=sys.stderr)
        return 1
    print(f"GRÜN: {len(manifest['files'])} synthetische Testdateien mit Prüfsummen erstellt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
