#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
APP_FILE="dashboard-studio-ultimate-pro-v3.1.0.html"
HOST="127.0.0.1"
START_PORT="${MULTIMODULTOOL_PORT:-4173}"
LOG_PREFIX="[MULTIMODULTOOL2026]"

fail() {
  printf '%s Fehler: %s\n' "$LOG_PREFIX" "$1" >&2
  exit 1
}

check_file() {
  [ -f "$ROOT_DIR/$1" ] || fail "Pflichtdatei fehlt: $1"
}

find_python() {
  if command -v python3 >/dev/null 2>&1; then
    printf 'python3'
  elif command -v python >/dev/null 2>&1; then
    printf 'python'
  else
    fail "Python 3 wurde nicht gefunden. Bitte Python installieren oder einen lokalen Webserver im Projektordner starten. Es wurde nichts verändert."
  fi
}

port_is_free() {
  "$PYTHON_BIN" - "$HOST" "$1" <<'PY'
import socket
import sys

host, port = sys.argv[1], int(sys.argv[2])
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.settimeout(0.2)
    sys.exit(0 if sock.connect_ex((host, port)) != 0 else 1)
PY
}

pick_port() {
  port=$START_PORT
  end=$((START_PORT + 20))
  while [ "$port" -le "$end" ]; do
    if port_is_free "$port"; then
      printf '%s' "$port"
      return 0
    fi
    port=$((port + 1))
  done
  fail "Kein freier lokaler Port zwischen $START_PORT und $end gefunden. Bitte belegte lokale Server schließen und erneut starten."
}

open_browser() {
  url=$1
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$url" >/dev/null 2>&1 &
  elif command -v open >/dev/null 2>&1; then
    open "$url" >/dev/null 2>&1 &
  elif command -v start >/dev/null 2>&1; then
    start "" "$url" >/dev/null 2>&1 &
  else
    printf '%s Browser konnte nicht automatisch geöffnet werden. Bitte diese Adresse öffnen:\n%s\n' "$LOG_PREFIX" "$url"
  fi
}

check_file "$APP_FILE"
check_file "manifests/MULTIMODULTOOL2026_02_AppManifest.json"
check_file "modules/provoware-genretool-pro/module.html"
check_file "modules/provoware-genretool-pro/module.css"
check_file "modules/provoware-genretool-pro/module.js"
check_file "modules/provoware-genretool-pro/genres_db.json"

PYTHON_BIN=$(find_python)
PORT=$(pick_port)
APP_URL="http://$HOST:$PORT/$APP_FILE"

printf '%s Prüfung abgeschlossen: Startdatei, Manifest und GenreTool-Dateien sind vorhanden.\n' "$LOG_PREFIX"
printf '%s Lokaler Server startet auf %s. Beenden mit Strg+C.\n' "$LOG_PREFIX" "$APP_URL"
open_browser "$APP_URL"
cd "$ROOT_DIR"
exec "$PYTHON_BIN" -m http.server "$PORT" --bind "$HOST"
