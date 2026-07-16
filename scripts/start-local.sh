#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
APP_FILE="dashboard-studio-ultimate-pro-v3.1.0.html"
HOST="127.0.0.1"
START_PORT="${MULTIMODULTOOL_PORT:-4173}"
NO_BROWSER="${MULTIMODULTOOL_NO_BROWSER:-0}"
LOG_PREFIX="[MULTIMODULTOOL2026]"
SERVER_PID=""

cleanup() {
  if [ -n "${SERVER_PID:-}" ] && kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" >/dev/null 2>&1 || true
  fi
}

on_signal() {
  cleanup
  trap - EXIT HUP INT TERM
  exit 130
}

trap cleanup EXIT
trap on_signal HUP INT TERM

fail() {
  printf '%s Fehler: %s\n' "$LOG_PREFIX" "$1" >&2
  exit 1
}

check_file() {
  [ -f "$ROOT_DIR/$1" ] || fail "Pflichtdatei fehlt: $1"
}

python_is_supported() {
  "$1" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1
}

find_python() {
  if command -v python3 >/dev/null 2>&1 && python_is_supported python3; then
    printf 'python3'
  elif command -v python >/dev/null 2>&1 && python_is_supported python; then
    printf 'python'
  else
    fail "Python 3.8 oder neuer wurde nicht gefunden. Bitte Python installieren oder einen lokalen Webserver im Projektordner starten. Es wurde nichts verändert."
  fi
}

validate_start_port() {
  case "$START_PORT" in
    ''|*[!0-9]*) fail "MULTIMODULTOOL_PORT muss eine ganze Zahl zwischen 1 und 65535 sein." ;;
  esac
  [ "$START_PORT" -ge 1 ] && [ "$START_PORT" -le 65535 ] || fail "MULTIMODULTOOL_PORT muss zwischen 1 und 65535 liegen."
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
  [ "$end" -le 65535 ] || end=65535
  while [ "$port" -le "$end" ]; do
    if port_is_free "$port"; then
      printf '%s' "$port"
      return 0
    fi
    port=$((port + 1))
  done
  fail "Kein freier lokaler Port zwischen $START_PORT und $end gefunden. Bitte belegte lokale Server schließen und erneut starten."
}

wait_for_server() {
  "$PYTHON_BIN" - "$HOST" "$1" "$APP_FILE" <<'PY'
import sys
import time
import urllib.request

host, port, app_file = sys.argv[1], int(sys.argv[2]), sys.argv[3]
url = f"http://{host}:{port}/{app_file}"
deadline = time.monotonic() + 8.0
last_error = "keine Antwort"

while time.monotonic() < deadline:
    try:
        request = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(request, timeout=0.6) as response:
            if 200 <= response.status < 400:
                raise SystemExit(0)
            last_error = f"HTTP {response.status}"
    except Exception as exc:  # noqa: BLE001 - Ausgabe wird nur für die Startdiagnose verwendet.
        last_error = str(exc)
    time.sleep(0.1)

print(f"Lokaler Server wurde nicht rechtzeitig erreichbar: {last_error}", file=sys.stderr)
raise SystemExit(1)
PY
}

open_browser() {
  url=$1
  case "$(printf '%s' "$NO_BROWSER" | tr '[:upper:]' '[:lower:]')" in
    1|true|yes|ja)
      printf '%s Browseröffnung wurde für Prüfung oder Automatisierung übersprungen.\n' "$LOG_PREFIX"
      return 0
      ;;
  esac

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
check_file "manifests/MULTIMODULTOOL2026_01_ModuleManifest.schema.json"
check_file "manifests/MULTIMODULTOOL2026_02_AppManifest.json"
check_file "modules/provoware-genretool-pro/module.manifest.json"
check_file "modules/provoware-genretool-pro/module.html"
check_file "modules/provoware-genretool-pro/module.css"
check_file "modules/provoware-genretool-pro/module.js"
check_file "modules/provoware-genretool-pro/genres_db.json"

PYTHON_BIN=$(find_python)
validate_start_port
PORT=$(pick_port)
APP_URL="http://$HOST:$PORT/$APP_FILE"

printf '%s Prüfung abgeschlossen: Startdatei, Schema, Manifeste und GenreTool-Dateien sind vorhanden.\n' "$LOG_PREFIX"
if [ "$PORT" != "$START_PORT" ]; then
  printf '%s Hinweis: Port %s ist belegt. Es wird der freie Alternativport %s verwendet. Es wurde nichts überschrieben.\n' "$LOG_PREFIX" "$START_PORT" "$PORT"
fi
printf '%s Lokaler Server wird auf %s gestartet. Beenden mit Strg+C.\n' "$LOG_PREFIX" "$APP_URL"

cd "$ROOT_DIR"
"$PYTHON_BIN" -m http.server "$PORT" --bind "$HOST" &
SERVER_PID=$!

if ! wait_for_server "$PORT"; then
  fail "Der lokale Server ist nicht korrekt gestartet. Bitte vorherige Terminalausgaben prüfen."
fi

printf '%s Server ist erreichbar: %s\n' "$LOG_PREFIX" "$APP_URL"
open_browser "$APP_URL"
wait "$SERVER_PID"
