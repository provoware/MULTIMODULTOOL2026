#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
APP_FILE="$ROOT_DIR/dashboard-studio-ultimate-pro-v3.1.0.html"

if [ ! -f "$APP_FILE" ]; then
  printf 'Fehler: Startdatei nicht gefunden: %s\n' "$APP_FILE" >&2
  exit 1
fi

if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$APP_FILE" >/dev/null 2>&1 &
elif command -v open >/dev/null 2>&1; then
  open "$APP_FILE" >/dev/null 2>&1 &
elif command -v start >/dev/null 2>&1; then
  start "" "$APP_FILE" >/dev/null 2>&1 &
else
  printf 'Bitte öffnen Sie diese Datei im Browser:\n%s\n' "$APP_FILE"
  exit 0
fi

printf 'Dashboard wird lokal geöffnet:\n%s\n' "$APP_FILE"
