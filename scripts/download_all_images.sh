#!/usr/bin/env bash
# Качает оставшиеся изображения батчами: на каждый батч — свежая сессия Chrome
# (иначе Cloudflare блокирует профиль после ~150 запросов подряд).
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BATCH="${1:-60}"
ROUNDS="${2:-8}"

for r in $(seq 1 "$ROUNDS"); do
  PORT=$((9400 + r))
  PROFILE="/tmp/chrome-bestiary-$r"
  rm -rf "$PROFILE"
  "$CHROME" --headless --disable-gpu --no-sandbox --user-data-dir="$PROFILE" \
      --no-first-run --disable-dev-shm-usage --remote-debugging-port="$PORT" \
      about:blank >/dev/null 2>&1 &
  CPID=$!
  sleep 5
  echo "=== раунд $r (порт $PORT) ==="
  node "$ROOT/scripts/download_images.js" "$PORT" 0 "$BATCH" || true
  kill -9 "$CPID" 2>/dev/null
  pkill -f "chrome-bestiary-$r" 2>/dev/null
  sleep 3
  LEFT=$(python3 - "$ROOT" <<'PY'
import json,os,sys
root=sys.argv[1]
tasks=json.load(open(os.path.join(root,'data/raw/image_tasks.json')))
exts=('.jpg','.png','.webp','.gif','.avif')
have=0
for t in tasks:
    if any(os.path.exists(os.path.join(root,'site/img',t['slug']+e)) for e in exts):
        have+=1
print(len(tasks)-have)
PY
)
  echo "осталось скачать: $LEFT"
  [ "$LEFT" -le 0 ] && break
done
echo "готово"
