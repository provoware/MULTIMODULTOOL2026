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
    printf 'ROT: Python 3 wurde nicht gefunden.\n'
    printf 'Lösung unter Kubuntu: sudo apt install python3 python3-venv python3-pip\n'
    exit 10
fi

PYTHON_BIN="python3"
if [[ -x "$PROJECT_DIR/.venv/bin/python" ]]; then
    PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
    printf 'GRÜN: Lokale Python-Umgebung gefunden.\n'
else
    printf 'GELB: Keine lokale .venv gefunden. System-Python wird geprüft.\n'
fi

if ! "$PYTHON_BIN" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
    printf 'ROT: Python 3.10 oder neuer wird benötigt.\n'
    exit 11
fi

printf 'Prüfe Linux- und Layoutvertrag ...\n'
if ! "$PYTHON_BIN" -m src.main --validate-only; then
    printf 'ROT: Start abgebrochen. Plattform- oder Layoutvertrag ist nicht gültig.\n'
    printf 'Es wurden keine Projektdaten verändert.\n'
    exit 12
fi

if ! "$PYTHON_BIN" -c 'import PySide6' >/dev/null 2>&1; then
    printf '\nGELB: PySide6 ist noch nicht installiert.\n'
    printf 'Empfohlene einmalige Einrichtung:\n'
    printf '  python3 -m venv .venv\n'
    printf '  .venv/bin/python -m pip install --upgrade pip\n'
    printf '  .venv/bin/python -m pip install -r requirements.txt\n'
    printf 'Danach erneut ./start.sh ausführen.\n'
    exit 13
fi

printf 'GRÜN: Linux-Vorprüfung erfolgreich. Oberfläche wird gestartet.\n'
exec "$PYTHON_BIN" -m src.main
