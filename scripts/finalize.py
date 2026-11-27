"""Book-wide finishing pass, run by pipeline.py after the proofreading edits.

usage: finalize.py work/config.json        (reads the file named by config "finalize")

finalize.json (every key optional; paths relative to the config's folder):
{
  "pictures": [                       # illustrations that share a page with text: crop and place
    {"page": 15, "y0": 0.11, "y1": 0.63, "before": "first words of the paragraph after it"}
  ],
  "full_page_trim": [0.055, 0.97],    # crop full-page pictures (image_pages) to this height band,
                                      #   e.g. to cut off a scanner/website watermark at the top
  "h2": ["sub-heading text", ...],    # blocks with exactly this text become sub-headings
  "center": ["short centred line", ...],
  "replace": [["regex", "replacement"], ...],   # book-wide, after the edits (name spellings etc.)
  "heading_before_picture": true,     # a picture right before a chapter heading moves after it
  "split_new_quotes": true            # split a paragraph where a new “quote opens after ။ or . . .
}
"""
import json, os, re, sys
from collections import Counter
from PIL import Image

cfg_path = os.path.abspath(sys.argv[1]); D = os.path.dirname(cfg_path)
C = json.load(open(cfg_path))
rel = lambda p: p if os.path.isabs(p) else os.path.join(D, p)
B = rel(C.get('out', 'blocks.json')); SCANS = rel(C['scans'])
F = json.load(open(rel(C['finalize'])))
b = json.load(open(B))
PICS = os.path.join(D, 'pics'); os.makedirs(PICS, exist_ok=True)

def find(prefix):
    key = prefix.lstrip('“ ')
    for i, x in enumerate(b):
        if x.get('text', '').lstrip('“ ').startswith(key): return i
    sys.exit('finalize: anchor not found: ' + prefix)

# 1. part-page pictures
for pc in F.get('pictures', []):
    im = Image.open(f"{SCANS}/{pc['page']:04d}.png"); w, h = im.size
    out = f"{PICS}/pic_{pc['page']:04d}.png"
    im.crop((0, int(h * pc['y0']), w, int(h * pc['y1']))).save(out)
    b.insert(find(pc['before']), {'type': 'pic', 'src': out})

# 2. full-page pictures: trim watermark bands
if F.get('full_page_trim'):
    t0, t1 = F['full_page_trim']
    for x in b:
        if x['type'] == 'pic' and os.path.dirname(os.path.abspath(x['src'])) == SCANS:
            im = Image.open(x['src']); w, h = im.size
            out = f"{PICS}/full_{os.path.basename(x['src'])}"
            im.crop((0, int(h * t0), w, int(h * t1))).save(out); x['src'] = out

# 3. block types by exact text
H2, CEN = set(F.get('h2', [])), set(F.get('center', []))
for x in b:
    t = x.get('text', '').strip()
    if x['type'] in ('p', 'center', 'h') and t in H2: x['type'] = 'h2'
    elif x['type'] == 'p' and t in CEN: x['type'] = 'center'

# 4. heading first, then its illustration
if F.get('heading_before_picture', True):
    for i in range(1, len(b)):
        if b[i]['type'] == 'h' and b[i - 1]['type'] == 'pic': b[i - 1], b[i] = b[i], b[i - 1]

# 5. book-wide replacements, whitespace, empty blocks
REP = [tuple(r) for r in F.get('replace', [])]
out = []
for x in b:
    if x.get('text') is not None:
        t = x['text']
        for a, r in REP: t = re.sub(a, r, t)
        t = re.sub(r'[  ]{2,}', ' ', t).strip(); x['text'] = t
        if not t and x['type'] in ('p', 'center'): continue
    out.append(x)
b = out

# 6. a new quotation opening mid-paragraph starts a new paragraph
if F.get('split_new_quotes', True):
    out = []
    for x in b:
        if x['type'] == 'p':
            parts = re.split(r'(?<=။) (?=“)|(?<=\. \. \.) (?=“)', x['text'])
            for pt in parts: y = dict(x); y['text'] = pt; out.append(y)
        else: out.append(x)
    b = out

json.dump(b, open(B, 'w'), ensure_ascii=False)
print('finalized:', dict(Counter(x['type'] for x in b)))
