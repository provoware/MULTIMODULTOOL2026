#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

confirm() {
    local title="$1"
    local message="$2"
    if command -v kdialog >/dev/null 2>&1 && [[ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]]; then
        kdialog --title "$title" --yesno "$message"
        return $?
    fi
    printf '\n%s\n%s\n' "$title" "$message"
    read -r -p 'Fortfahren? [j/N]: ' answer
    [[ "${answer,,}" == "j" || "${answer,,}" == "ja" || "${answer,,}" == "y" || "${answer,,}" == "yes" ]]
}

printf '\nMULTIMODULTOOL2026 – geführte Linux-Einrichtung\n'
printf 'Projekt: %s\n\n' "$PROJECT_DIR"

if [[ "$(uname -s)" != "Linux" ]]; then
    printf 'ROT: Die Einrichtung ist ausschließlich für Linux-Desktop-Systeme vorgesehen.\n'
    printf 'Es wurden keine Daten verändert.\n'
    exit 9
fi

if ! command -v python3 >/dev/null 2>&1; then
    if ! command -v apt-get >/dev/null 2>&1; then
        printf 'ROT: Python 3 fehlt und apt-get ist nicht verfügbar.\n'
        printf 'Installiere Python 3.10+, python3-venv und python3-pip über deine Distribution.\n'
        exit 10
    fi

    message=$'Python 3 fehlt.\n\nAusgeführt werden:\nsudo apt-get update\nsudo apt-get install -y python3 python3-venv python3-pip\n\nEs werden ausschließlich diese Linux-Systempakete installiert.'
    if ! confirm 'Python für MULTIMODULTOOL2026 einrichten' "$message"; then
        printf 'GELB: Einrichtung abgebrochen. Es wurden keine Projektdateien verändert.\n'
        exit 11
    fi

    sudo apt-get update
    sudo apt-get install -y python3 python3-venv python3-pip
fi

exec python3 tools/setup_assistant.py "$@"
