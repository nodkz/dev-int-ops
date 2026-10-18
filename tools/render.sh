#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Regenerate the diagrams (SVG for the pages, PNG at 2x for downloads), the social card (1200x630) and the paper's PDF.
# Needs Python 3 and Google Chrome. Override the browser with CHROME=/path/to/chrome.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
PROFILE="$(mktemp -d)"
PRINT="$ROOT/site/v1/.print.html"
trap 'rm -rf "$PROFILE" "$PRINT"' EXIT

shot() {
  local svg="$1" scale="$2" out="$3" w h
  w=$(grep -o '<svg[^>]*' "$svg" | grep -o ' width="[0-9]*"' | head -1 | tr -dc '0-9')
  h=$(grep -o '<svg[^>]*' "$svg" | grep -o ' height="[0-9]*"' | head -1 | tr -dc '0-9')
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --no-first-run --user-data-dir="$PROFILE" \
    --force-device-scale-factor="$scale" --window-size="$w,$h" --screenshot="$out" "file://$svg" >/dev/null 2>&1
  echo "rendered ${out#"$ROOT"/}"
}

python3 "$ROOT/tools/build_diagrams.py"
for svg in "$ROOT"/site/assets/diagrams/*.svg; do
  shot "$svg" 2 "${svg%.svg}.png"
done
shot "$ROOT/site/assets/og-image.svg" 1 "$ROOT/site/assets/og-image.png"

# Print from a copy of the paper with every figure loaded eagerly. The figures are SVG, so the PDF keeps them as vectors.
# The EXIT trap deletes the copy even when Chrome fails, so it never lands in site/.
sed -e 's/ loading="lazy"//g' "$ROOT/site/v1/index.html" > "$PRINT"
"$CHROME" --headless=new --disable-gpu --no-first-run --user-data-dir="$PROFILE" --no-pdf-header-footer \
  --print-to-pdf="$ROOT/site/v1/devintops-v1-draft.pdf" "file://$PRINT" >/dev/null 2>&1
rm -f "$PRINT"
python3 "$ROOT/tools/pdf_meta.py" "$ROOT/site/v1/devintops-v1-draft.pdf"
