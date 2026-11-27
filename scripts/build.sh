#!/usr/bin/env bash
# Build the Kindle PDF + plain-text copy from blocks.json.
# Set BOOK_AUTHOR="<author in Burmese>" to print the author on the title page.
# usage: build.sh blocks.json source.pdf out_dir FileStem "Title line 1" "Title line 2" ["part label"] ["note"]
#   source.pdf: its page 1 becomes the cover.   FileStem e.g. MinTheinKha_MyaingYazaTarTay
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BLOCKS=$1 SRC=$2 OUT=$3 STEM=$4 T1=$5 T2=$6 PART=${7:-} NOTE=${8:-"Retyped Kindle edition · Google OCR, proofread"}
mkdir -p "$OUT"; H="$OUT/$STEM.html"; RAW="$OUT/${STEM}_raw.pdf"
python3 "$HERE/kindle_typeset.py" "$BLOCKS" "$SRC" "$PART" "$H" "$T1" "$T2" "$NOTE"
google-chrome --headless=new --no-sandbox --disable-gpu --no-pdf-header-footer --print-to-pdf="$RAW" "file://$(realpath "$H")" 2>/dev/null
python3 "$HERE/kindle_outline.py" "$RAW" "$H.marks.json" "$OUT/${STEM}_Kindle.pdf"
python3 - "$BLOCKS" "$OUT/${STEM}_text.txt" <<'PY'
import json, sys
b = json.load(open(sys.argv[1])); o = []
for x in b:
    if x['type'] == 'h': o.append('\n## ' + x['text'] + '\n')
    elif x['type'] == 'break': o.append('* * *')
    elif x.get('text'): o.append(x['text'])
open(sys.argv[2], 'w').write('\n\n'.join(o))
PY
python3 "$HERE/check_fontsize.py" "$OUT/${STEM}_Kindle.pdf"
