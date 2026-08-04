#!/usr/bin/env bash
set -Eeuo pipefail

APP_ROOT="/usr/lib/multimodultool2026"
APP_DIR="$APP_ROOT/app"
WHEELHOUSE="$APP_ROOT/wheelhouse"
BUILD_INFO="$APP_ROOT/BUILD_INFO.json"
FILE_MANIFEST="$APP_ROOT/FILE_MANIFEST.sha256"
REQUIREMENTS_LOCK="$APP_ROOT/requirements.lock"

fail() {
    printf 'ROT: %s\n' "$1" >&2
    printf 'Datenstand: System- und Nutzerdaten wurden durch den fehlgeschlagenen Start nicht verändert.\n' >&2
    exit "${2:-20}"
}

[[ "$(uname -s)" == "Linux" ]] || fail "Der Releasekandidat unterstützt ausschließlich Linux." 9
[[ "$(uname -m)" == "x86_64" ]] || fail "Der Releasekandidat unterstützt ausschließlich x86-64." 10
[[ -r "$BUILD_INFO" && -r "$FILE_MANIFEST" && -r "$REQUIREMENTS_LOCK" ]] || fail "Die installierten Release-Metadaten fehlen." 11

if [[ "${1:-}" == "--build-info" ]]; then
    cat "$BUILD_INFO"
    exit 0
fi

command -v python3 >/dev/null 2>&1 || fail "Python 3 wurde nicht gefunden." 12
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' \
    || fail "Python 3.10 oder neuer wird benötigt." 13
command -v sha256sum >/dev/null 2>&1 || fail "sha256sum fehlt." 14
command -v flock >/dev/null 2>&1 || fail "flock fehlt." 15

(
    cd /
    sha256sum --quiet -c "$FILE_MANIFEST"
) || fail "Die installierte reproduzierbare Dateiliste ist beschädigt." 16

if [[ "${1:-}" == "--verify-installation" ]]; then
    printf 'GRÜN: Paketdateien, Build-ID und Systemabhängigkeiten sind gültig.\n'
    cat "$BUILD_INFO"
    exit 0
fi

BUILD_ID="$(python3 - "$BUILD_INFO" <<'PY'
import json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
print(value['buildId'])
PY
)"
[[ "$BUILD_ID" =~ ^MMTBUILD-[A-Za-z0-9._~+-]+-[a-f0-9]{16}$ ]] || fail "Die Build-ID ist ungültig." 17
SAFE_BUILD_ID="${BUILD_ID//[^A-Za-z0-9._-]/_}"

DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
RUNTIME_ROOT="$DATA_HOME/multimodultool2026/runtime"
VENV_DIR="$RUNTIME_ROOT/venv-$SAFE_BUILD_ID"
LOCK_FILE="$RUNTIME_ROOT/runtime.lock"

mkdir -p -- "$RUNTIME_ROOT"
chmod 0700 "$RUNTIME_ROOT"
[[ ! -L "$RUNTIME_ROOT" ]] || fail "Der lokale Runtime-Ordner darf kein Symlink sein." 18

exec 9>"$LOCK_FILE"
chmod 0600 "$LOCK_FILE"
flock -x 9

if [[ ! -x "$VENV_DIR/bin/python" ]] || \
   ! "$VENV_DIR/bin/python" -c 'import PySide6' >/dev/null 2>&1 || \
   [[ ! -r "$VENV_DIR/MMT_BUILD_ID" ]] || \
   [[ "$(cat "$VENV_DIR/MMT_BUILD_ID")" != "$BUILD_ID" ]]; then
    TMP_VENV="$RUNTIME_ROOT/.venv-$SAFE_BUILD_ID-$$.tmp"
    rm -rf -- "$TMP_VENV"
    python3 -m venv "$TMP_VENV" || fail "Die lokale Python-Runtime konnte nicht angelegt werden." 19
    "$TMP_VENV/bin/python" -m pip install \
        --disable-pip-version-check \
        --no-index \
        --find-links "$WHEELHOUSE" \
        --requirement "$REQUIREMENTS_LOCK" \
        || { rm -rf -- "$TMP_VENV"; fail "Die gebündelte Offline-Runtime konnte nicht installiert werden." 20; }
    "$TMP_VENV/bin/python" -c 'import PySide6, sys; print(PySide6.__version__)' >/dev/null \
        || { rm -rf -- "$TMP_VENV"; fail "Die neue Offline-Runtime hat den Importtest nicht bestanden." 21; }
    printf '%s\n' "$BUILD_ID" > "$TMP_VENV/MMT_BUILD_ID"
    chmod 0600 "$TMP_VENV/MMT_BUILD_ID"
    chmod 0700 "$TMP_VENV"
    if [[ -e "$VENV_DIR" ]]; then
        rm -rf -- "$TMP_VENV"
    else
        mv -- "$TMP_VENV" "$VENV_DIR"
    fi
fi

flock -u 9
export PYTHONPATH="$APP_DIR"
export MMT_RELEASE_BUILD_INFO="$BUILD_INFO"
cd "$APP_DIR"
exec "$VENV_DIR/bin/python" -m src.main "$@"
