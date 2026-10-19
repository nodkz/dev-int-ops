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
# Relative links become absolute against the canonical address, so the PDF's links work for every reader; images
# and styles stay relative, so the copy prints with the local files. In-page links stay internal.
# The EXIT trap deletes the copy even when Chrome fails, so it never lands in site/.
python3 - "$ROOT/site/v1/index.html" "$PRINT" <<'PY'
import re, sys
from urllib.parse import urljoin
src = open(sys.argv[1], encoding="utf-8").read().replace(' loading="lazy"', "")
def absolute(m):
    href = m.group(2)
    if href.startswith(("#", "//")) or re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", href):
        return m.group(0)
    return m.group(1) + urljoin("https://devintops.org/v1/", href) + m.group(3)
open(sys.argv[2], "w", encoding="utf-8").write(re.sub(r'(<a\b[^>]*?\shref=")([^"]*)(")', absolute, src))
PY
"$CHROME" --headless=new --disable-gpu --no-first-run --user-data-dir="$PROFILE" --no-pdf-header-footer \
  --print-to-pdf="$ROOT/site/v1/devintops-v1-draft.pdf" "file://$PRINT" >/dev/null 2>&1
rm -f "$PRINT"
python3 "$ROOT/tools/pdf_meta.py" "$ROOT/site/v1/devintops-v1-draft.pdf"
