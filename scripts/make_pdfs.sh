#!/usr/bin/env bash
# Пересобирает все PDF из HTML-версий через headless Chrome.
# Запускать при работающем локальном сервере: bash scripts/serve.sh
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
BASE="${BASE:-http://127.0.0.1:8770}"

if [ ! -x "$CHROME" ]; then
  echo "Не найден Chrome: $CHROME" >&2
  echo "Укажите путь переменной CHROME." >&2
  exit 1
fi

build () {
  local src="$1" out="$2" budget="${3:-40000}"
  local prof="/tmp/pdfbuild_$(echo "$out" | md5 -q | cut -c1-8)"
  rm -rf "$prof"
  "$CHROME" --headless --disable-gpu --no-sandbox --user-data-dir="$prof" \
    --no-first-run --no-pdf-header-footer --virtual-time-budget="$budget" \
    --print-to-pdf="$ROOT/$out" "$BASE/$src" >/dev/null 2>&1 &
  local pid=$!
  for _ in $(seq 1 400); do kill -0 "$pid" 2>/dev/null || break; sleep 1; done
  kill -9 "$pid" 2>/dev/null
  if [ -f "$ROOT/$out" ]; then
    printf '  %-26s %s\n' "$out" "$(du -h "$ROOT/$out" | cut -f1)"
  else
    printf '  %-26s ОШИБКА\n' "$out"
  fi
}

echo "Печатаю PDF из $BASE"
build "site/adventure.html"          "adventure-dnd5e.pdf"
build "site/statblocks.html"         "statblocks-dnd5e.pdf" 60000
build "site-gumshoe/quickstart.html" "quickstart-gumshoe.pdf"
build "site-gumshoe/sheet.html"      "sheet-gumshoe.pdf"
build "site-gumshoe/dossier.html"    "dossier-gumshoe.pdf"
build "site-gumshoe/adventure.html"  "adventure-gumshoe.pdf"
build "site-edge/rules.html"         "rules-edge.pdf"
build "site-edge/adventure.html"     "adventure-edge.pdf"
echo
echo "Книга правил («Охотники») — отдельным скриптом, с обложкой и оглавлением:"
echo "  python3 scripts/build_gumshoe_pdf.py"
echo "  python3 scripts/build_hunters_pdf.py   (бестиарий охотника)"
echo
echo "Книга на 677 страниц собирается отдельно (долго):"
echo "  Chrome --print-to-pdf=bestiary-dnd5e.pdf $BASE/site/book.html"
