#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

printf '\nMULTIMODULTOOL2026 – sichere Linux-Startroutine\n'
printf 'Projekt: %s\n\n' "$PROJECT_DIR"

if [[ "$(uname -s)" != "Linux" ]]; then
    printf 'ROT: Dieses Projekt wird ausschließlich für Linux-Desktop-Systeme gebaut.\n'
    printf 'Unterstützt: Kubuntu 22.04/24.04 mit KDE Plasma.\n'
    printf 'Es wurden keine Daten verändert.\n'
    exit 9
fi

if ! command -v python3 >/dev/null 2>&1; then
    printf 'GELB: Python 3 wurde nicht gefunden. Der Einrichtungsassistent wird gestartet.\n'
    if ! bash "$PROJECT_DIR/setup.sh"; then
        printf 'ROT: Python-Einrichtung nicht abgeschlossen.\n'
        exit 10
    fi
fi

if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
    printf 'ROT: Python 3.10 oder neuer wird benötigt.\n'
    printf 'Es wurden keine Projektdaten verändert.\n'
    exit 11
fi

if [[ ! -x "$PROJECT_DIR/.venv/bin/python" ]] || \
   ! "$PROJECT_DIR/.venv/bin/python" -c 'import PySide6' >/dev/null 2>&1; then
    printf 'GELB: Die lokale Linux-Umgebung ist noch nicht vollständig eingerichtet.\n'
    if ! bash "$PROJECT_DIR/setup.sh"; then
        printf 'ROT: Einrichtung nicht abgeschlossen. Die Oberfläche wird nicht gestartet.\n'
        exit 13
    fi
fi

PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
if [[ ! -x "$PYTHON_BIN" ]]; then
    printf 'ROT: .venv/bin/python fehlt nach der Einrichtung.\n'
    exit 14
fi

printf 'Prüfe Linux- und Layoutvertrag ...\n'
if ! "$PYTHON_BIN" -m src.main --validate-only; then
    printf 'ROT: Start abgebrochen. Plattform- oder Layoutvertrag ist nicht gültig.\n'
    printf 'Es wurden keine Projektdaten verändert.\n'
    exit 12
fi

printf 'GRÜN: Linux-Vorprüfung erfolgreich. Oberfläche wird gestartet.\n'
exec "$PYTHON_BIN" -m src.main
