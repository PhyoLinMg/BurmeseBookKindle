"""Turn the downloaded OCR text into blocks.json (the book's editable structure).

usage: assemble_blocks.py config.json
config.json:
{
  "text_glob": "text/p*.txt",             # OCR exports (paths relative to this file)
  "scans": "s",                            # NNNN.png page images (for picture pages)
  "first_page": 4, "last_page": 334,        # book pages that hold the story
  "titles": {"4": "အခန်း(၁)", "8": "...", "120": ""},   # page -> chapter title; "" = scene break
  "image_pages": [27, 37],                  # full-page illustrations, kept as pictures
  "skip": [162],                            # blank / duplicated / misprinted pages
  "running_heads": ["ဆားပုလင်း\\S*\\s*နှင်းမောင်နှင့်\\s*မြ\\S*"],   # regexes for the page-header line
  "author_head": "မင်းသိ",                   # short lines containing this are page headers
  "out": "blocks.json"
}
Paragraphs are joined across lines and pages until a line ends a sentence (။ ” ? ! ...).
The result is a first draft; the proofreading pass fixes the rest."""
import re, json, glob, difflib, collections, sys
import os
C = json.load(open(sys.argv[1]))
_D = os.path.dirname(os.path.abspath(sys.argv[1]))   # relative paths are relative to the config file
for _k in ('text_glob', 'scans', 'out'):
    if _k in C and not os.path.isabs(C[_k]): C[_k] = os.path.join(_D, C[_k])
C.setdefault('out', os.path.join(_D, 'blocks.json'))
TEXT = '\n'.join(open(f, encoding='utf-8-sig').read() for f in sorted(glob.glob(C['text_glob'])))
TITLES = C.get('titles', {}); IMG = set(C.get('image_pages', [])); SKIP = set(C.get('skip', []))
HEADS = [re.compile(h) for h in C.get('running_heads', [])]; AUTH = C.get('author_head', 'မင်းသိ')
MY = re.compile('[က-အဣ-ဪဿ၌-၏]')

parts = re.split(r'#?\s*P\s*([0-9Oo]{4})\s*#', TEXT)   # tolerant of OCR misreading the marker
pages = {}
for k in range(1, len(parts) - 1, 2):
    pages[int(parts[k].replace('O', '0').replace('o', '0'))] = parts[k + 1]
want = [n for n in range(C['first_page'], C['last_page'] + 1) if n not in SKIP and n not in IMG]
missing = [n for n in want if n not in pages]
print('pages parsed', len(pages), '| missing markers:', missing or 'none')

def junk(l):
    s = l.strip()
    if not s: return True
    if len(s) < 70 and any(h.search(s) for h in HEADS): return True
    if len(s) < 25 and AUTH in s: return True
    if re.fullmatch(r'[\s၀-၉0-9.:;,\-–—!|iIl/\\()\[\]{}\'"“”‘’*#~^`©]+', s): return True   # page numbers, specks
    if len(MY.findall(s)) < 2 and not re.search('[။၏၍]', s): return True
    return False

def norm(t):
    for h in HEADS:
        if h.match(t): t = h.sub('', t, count=1)
    t = re.sub(r'(?<=[က-႟])[A-Za-z]+|[A-Za-z]+(?=[က-႟])', '', t)   # Latin OCR noise glued to Burmese
    t = re.sub(r'(?:၄|ငှ|င)င်း(?=[၏ကသအတနမ\s၊။]|$)', '၎င်း', t)
    t = re.sub(r'(?<![၀-၉])၀(?![၀-၉])', 'ဝ', t)                                          # zero vs wa
    t = re.sub(r'(^|[\s(])"', r'\1“', t); t = t.replace('"', '”')
    t = re.sub(r"(^|[\s(])'", r'\1‘', t)
    t = re.sub(r'\s+([၊။၏])', r'\1', t)
    return re.sub(r'[ \t]+', ' ', t).strip()

END = re.compile(r'(?:[။?!]|[။၏]\s*[”’]|[”’]|\.\s*\.\s*\.)\s*$')
blocks = []
for n in range(C['first_page'], C['last_page'] + 1):
    if n in SKIP: continue
    if n in IMG:
        blocks.append({'type': 'pic', 'src': f"{C['scans']}/{n:04d}.png"}); continue
    if n not in pages: continue
    lines = [x for x in (norm(l) for l in pages[n].split('\n') if not junk(l)) if x]
    t = TITLES.get(str(n))
    if t is not None:
        if t:
            for j in range(min(3, len(lines))):      # drop the OCR'd copy of the title
                if difflib.SequenceMatcher(None, lines[j].replace(' ', ''), t.replace(' ', '')).ratio() > 0.5 and len(lines[j]) < len(t) + 25:
                    lines.pop(j); break
            blocks.append({'type': 'h', 'text': t})
        else:
            blocks.append({'type': 'break'})
    for l in lines:
        prev = blocks[-1] if blocks else None
        if prev and prev['type'] == 'p' and not END.search(prev['text']) and not l.startswith(('“', '‘', '(')):
            prev['text'] += ' ' + l
        else:
            blocks.append({'type': 'p', 'text': l, 'indent': True})
out = []
for b in blocks:                                    # split run-together dialogue
    if b['type'] != 'p': out.append(b); continue
    out += [{'type': 'p', 'text': p.strip(), 'indent': True} for p in re.split(r'(?<=[။”])\s+(?=“)', b['text']) if p.strip()]
json.dump(out, open(C['out'], 'w'), ensure_ascii=False)
print(dict(collections.Counter(b['type'] for b in out)), 'chars', sum(len(b.get('text', '')) for b in out))
