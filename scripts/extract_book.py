import sys, os, io, json, collections, re, base64
import fitz
import numpy as np
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from ztr_map import decode

src, first_body, out, imgdir = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
os.makedirs(imgdir, exist_ok=True)
LATIN = {'ZTR1B13', 'ZTR1B07', 'ZTR2682', 'ZTR2684', 'ZTR267B'}
ORN = {'ZTR2680', 'ZTR1B0F'}
TOP, BOT = 80, 718

doc = fitz.open(src)

def fontkey(f): return f.split('.')[0]

def line_text(l):
    parts = []
    for s in l['spans']:
        t = ''.join(c['c'] for c in s['chars'])
        fk = fontkey(s['font'])
        if fk in LATIN or fk == 'Arial': parts.append(t)
        elif fk.startswith('ZTR'): parts.append(decode(t))
        else: parts.append(t)
    return ''.join(parts)

def strip_png(pix, name):
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.alpha and pix.n == 1:
        ink = arr[..., 0]                       # pure stencil: alpha = ink
    elif pix.alpha:
        ink = ((255 - arr[..., :-1].mean(axis=2)) * (arr[..., -1] / 255)).astype(np.uint8)
    else:
        ink = (255 - arr[..., :pix.n].mean(axis=2)).astype(np.uint8)
    ink = Image.fromarray(np.ascontiguousarray(ink))
    ink = ink.resize((ink.width * 3, ink.height * 3), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.1))
    ink = ink.point(lambda v: 255 if v > 110 else 0)
    img = Image.fromarray(255 - np.array(ink)).convert('L')
    p = os.path.join(imgdir, name); img.save(p, optimize=True)
    return p

items = []   # dicts: page, y, x, kind, text/size or img
stats_x = collections.Counter()
for pno in range(first_body - 1, len(doc)):
    p = doc[pno]
    rows = []
    for b in p.get_text('rawdict')['blocks']:
        for l in b.get('lines', []):
            y, x = l['bbox'][1], l['bbox'][0]
            fk = fontkey(l['spans'][0]['font'])
            if fk == 'Arial' or y < TOP or y > BOT: continue
            sz = max(s['size'] for s in l['spans'])
            t = line_text(l).strip()
            if not t: continue
            kind = 'orn' if fk in ORN else 'text'
            rows.append(dict(page=pno + 1, y=y, x=x, x1=l['bbox'][2], size=sz, text=t, kind=kind))
    seen = []
    pics = []
    for info in p.get_image_info(xrefs=True):
        r = fitz.Rect(info['bbox'])
        if r.height >= 100 and r.width >= 100 and r.y1 > TOP and r.y0 < BOT:
            for k, q in enumerate(pics):
                if (r + (-6, -6, 6, 6)).intersects(q):
                    pics[k] = q | r; break
            else:
                pics.append(r)
    for k, r in enumerate(pics):
        r = fitz.Rect(r.x0, max(r.y0, 30), r.x1, r.y1)
        pm = p.get_pixmap(dpi=170, clip=r)
        path = os.path.join(imgdir, f'pic{pno + 1:03d}_{k}.jpg')
        Image.open(io.BytesIO(pm.tobytes('png'))).convert('L').save(path, quality=85)
        rows.append(dict(page=pno + 1, y=r.y0, x=r.x0, x1=r.x1, size=24, kind='pic', img=path, w=r.width, h=r.height))
    for info in p.get_image_info(xrefs=True):
        r = fitz.Rect(info['bbox'])
        if r.height >= 100 and r.width >= 100: continue
        if not (r.height < 40 and r.width > 8 and TOP < r.y0 < BOT): continue
        if any(abs(r.x0 - s.x0) < 3 and abs(r.y0 - s.y0) < 3 for s in seen): continue
        seen.append(r)
        pix = fitz.Pixmap(doc, info['xref'])
        path = strip_png(pix, f'p{pno + 1:03d}_{len(seen):02d}.png')
        rows.append(dict(page=pno + 1, y=r.y0, x=r.x0, x1=r.x1, size=24, kind='img', img=path, w=r.width, h=r.height))
    # dedupe fake-bold text duplicates
    rows.sort(key=lambda d: (round(d['y'] / 6), d['x']))
    ded = []
    for d in rows:
        if d['kind'] in ('text', 'orn') and any(e['kind'] in ('text', 'orn') and e['text'] == d['text'] and abs(e['y'] - d['y']) < 3 for e in ded):
            continue
        ded.append(d)
    ded.sort(key=lambda d: (d['y'], d['x']))
    merged = []
    for d in ded:
        m = merged[-1] if merged else None
        if m and m['kind'] == 'img' and d['kind'] == 'img' and abs(m['y'] - d['y']) < 5:
            a, b = Image.open(m['img']), Image.open(d['img'])
            gap = max(0, int((d['x'] - m['x1']) * 3 * (a.height / (m['h'] * 3))))
            W = a.width + gap + b.width; H = max(a.height, b.height)
            c = Image.new('L', (W, H), 255); c.paste(a, (0, 0)); c.paste(b, (a.width + gap, 0)); c.save(m['img'])
            m['x1'] = d['x1']; m['w'] = m['x1'] - m['x']
            continue
        merged.append(d)
    ded = merged
    items.extend(ded)
    for d in ded:
        if d['kind'] == 'text' and 20 < d['size'] < 26: stats_x[round(d['x'])] += 1

L = min(x for x, n in stats_x.most_common(3))
print('left margin', L, stats_x.most_common(5))

# ---- build blocks ----
blocks = []; cur = None; prev = None
def flush():
    global cur
    if cur and cur['text'].strip(): blocks.append(cur)
    cur = None

for d in items:
    if d['kind'] == 'orn':
        flush();
        if not blocks or blocks[-1]['type'] != 'break': blocks.append({'type': 'break'})
        prev = None; continue
    if d['kind'] == 'pic':
        flush(); blocks.append({'type': 'pic', 'src': d['img']}); prev = None; continue
    if d['kind'] == 'img':
        flush()
        blocks.append({'type': 'img', 'src': d['img'], 'indent': max(0, d['x'] - L), 'w': d['w'], 'page': d['page']})
        prev = d; continue
    sz, x, t = d['size'], d['x'], d['text']
    if sz >= 28:
        if blocks and blocks[-1]['type'] == 'h' and prev is not None and prev.get('size', 0) >= 28 and prev['page'] == d['page']:
            if abs(prev['y'] - d['y']) < 4:
                # fake-bold duplicate: keep the longer decoding
                if len(t) > len(blocks[-1]['last']):
                    blocks[-1]['text'] = blocks[-1]['text'][: len(blocks[-1]['text']) - len(blocks[-1]['last'])] + t
                    blocks[-1]['last'] = t
                prev = d; continue
            if d['y'] - prev['y'] < sz * 1.7:
                blocks[-1]['text'] += ' ' + t; blocks[-1]['last'] = t
            else:
                blocks.append({'type': 'h2', 'text': t, 'last': t})
        else:
            flush(); blocks.append({'type': 'h', 'text': t, 'last': t})
        prev = d; continue
    if 25.6 <= sz < 28 and abs((x + d['x1']) / 2 - 306) < 40:
        flush(); blocks.append({'type': 'center', 'text': t}); prev = d; continue
    indented = x > L + 6
    if cur is None:
        cur = {'type': 'p', 'text': t, 'indent': indented, 'x': x}
    elif not indented:
        cur['text'] += ' ' + t
    else:
        same_block = prev is not None and prev['kind'] == 'text' and abs(prev['x'] - x) < 3 and prev['x'] > L + 6 and not t.startswith(('“', '‘'))
        if same_block:
            cur['text'] += ' ' + t
        else:
            flush(); cur = {'type': 'p', 'text': t, 'indent': True, 'x': x}
    prev = d
flush()
for b in blocks:
    if 'text' in b:
        b['text'] = re.sub(r'\s+', ' ', b['text']).strip()
json.dump(blocks, open(out, 'w'), ensure_ascii=False, indent=0)
c = collections.Counter(b['type'] for b in blocks)
print(c)
print([b['text'] for b in blocks if b['type'] == 'h'][:40])
