"""Typed-Word PDF in a WinInnwa-family font -> blocks.json (no OCR needed).

usage: extract_wininnwa.py source.pdf blocks.json [--first-page 1] [--title-lines 1]
The source is a Word document printed to PDF (letter size, 14 pt "WinInnwa", 18 pt title):
left-aligned lines, paragraphs separated by empty lines or by quote/speaker structure,
centred lines for section titles, "xxxxxxxx" / "_____" lines (Verdana) for scene breaks,
English quotations in Times. Rules:
  - centred line, no sentence-ending mark, not a quote  -> 'h' (consecutive ones merge)
  - centred quoted line ( “…” )                          -> 'center'
  - right-aligned short lines at the very end              -> 'center' (closing words, signature)
  - otherwise lines join into a paragraph until an empty line, a line starting with “,
    or a short line ending in ။ / ” / ... (speaker intros like "ဦးကိုကိုကြီးက..." stand alone)
  - a paragraph starting with မှတ်ချက် becomes a 'note' block
The first 18 pt line is the book title and is dropped (it goes on the title page).
Read the printed headings list and compare with the PDF before proofreading."""
import sys, os, re, json, collections, argparse
import fitz
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from win_map import decode, UNKNOWN

ap = argparse.ArgumentParser(); ap.add_argument('pdf'); ap.add_argument('out')
ap.add_argument('--first-page', type=int, default=1)
a = ap.parse_args()
doc = fitz.open(a.pdf)
W = doc[0].rect.width; MID = W / 2

rows = []   # (page, kind, text, x0, x1, y)
for pno in range(a.first_page - 1, len(doc)):
    for b in doc[pno].get_text('dict')['blocks']:
        for l in b.get('lines', []):
            sp = l['spans']; raw = ''.join(s['text'] for s in sp); x0, y0, x1, _ = l['bbox']
            f = sp[0]['font']; size = max(s['size'] for s in sp)
            if not raw.strip():
                rows.append((pno + 1, 'blank', '', x0, x1, y0)); continue
            if re.fullmatch(r'\s*(x{5,}|_{5,})\s*', raw):
                rows.append((pno + 1, 'break', '', x0, x1, y0)); continue
            if 'Win' in f:
                txt = ''.join(decode(s['text']) if 'Win' in s['font'] else s['text'] for s in sp)
                kind = 'title' if size >= 17 else 'text'
            else:
                txt = raw; kind = 'latin'
            rows.append((pno + 1, kind, re.sub(r'\s+', ' ', txt).strip(), x0, x1, y0))

END = re.compile(r'(။|၏|”|’|\.\.+|…)\s*$')
blocks, cur = [], None
def flush():
    global cur
    if cur and cur['text'].strip():
        t = cur['text'].strip()
        if t.startswith('မှတ်ချက်'):
            t = re.sub(r'^မှတ်ချက်\s*။?\s*။?\s*', 'မှတ်ချက်။ ။ ', t)
            blocks.append({'type': 'note', 'text': t, 'sig': ''})
        else:
            blocks.append({'type': 'p', 'text': t, 'indent': True})
    cur = None

title_seen = False; last = len(rows) - 1
for i, (pg, kind, t, x0, x1, y) in enumerate(rows):
    if kind == 'title' and not title_seen:
        title_seen = True; continue
    if kind in ('blank',):
        flush(); continue
    if kind == 'break':
        flush()
        if blocks and blocks[-1]['type'] != 'break': blocks.append({'type': 'break'})
        continue
    centred = x0 > 140 and abs((x0 + x1) / 2 - MID) < 18
    right = x0 > 400 and x1 > W - 100
    if kind == 'text' and (centred or right) and len(t) < 80:
        quoted = t.startswith('“') and t.endswith('”')
        if right or quoted:
            flush(); blocks.append({'type': 'center', 'text': t}); continue
        if not END.search(t) and not t.startswith('“'):
            flush()
            prev = blocks[-1] if blocks else None
            if prev and prev['type'] == 'h' and prev.get('_row') == i - 1:
                prev['text'] += ' ' + t
            else:
                blocks.append({'type': 'h', 'text': t})
            blocks[-1]['_row'] = i
            continue
    starts_quote = t.startswith(('“', '‘'))
    if cur is None:
        cur = {'text': t, 'x1': x1}
    elif starts_quote or (END.search(cur['text']) and cur['x1'] < 440) or kind == 'latin' != cur.get('kind'):
        flush(); cur = {'text': t, 'x1': x1}
    else:
        cur['text'] += ' ' + t; cur['x1'] = x1
    cur['kind'] = kind
flush()
for b in blocks: b.pop('_row', None)
json.dump(blocks, open(a.out, 'w'), ensure_ascii=False)
print(dict(collections.Counter(b['type'] for b in blocks)), 'chars', sum(len(b.get('text', '')) for b in blocks))
print('unknown codes:', UNKNOWN or 'none')
print('headings:'); [print('  ', b['text']) for b in blocks if b['type'] == 'h']
