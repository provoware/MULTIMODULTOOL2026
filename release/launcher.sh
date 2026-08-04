#!/usr/bin/env bash
set -euo pipefail
BASE="/opt/multimodultool2026/current"
cd "$BASE/app"
exec "$BASE/venv/bin/python" -m src.main "$@"
