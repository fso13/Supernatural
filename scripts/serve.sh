#!/usr/bin/env bash
# Локальный сервер для сайта-бестиария.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/site"
PORT="${1:-8770}"
echo "Бестиарий: http://127.0.0.1:${PORT}/  (Ctrl+C — остановить)"
cd "$DIR"
exec python3 -m http.server "$PORT" --bind 127.0.0.1
