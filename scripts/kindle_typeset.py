import json, sys, html, base64, io, os
import fitz
from PIL import Image

blocks_path, src_pdf, part_label, out_html = sys.argv[1:5]
blocks = json.load(open(blocks_path))
_BD = os.path.dirname(os.path.abspath(blocks_path))   # relative picture paths are relative to blocks.json
for _b in blocks:
    if 'src' in _b and not os.path.isabs(_b['src']): _b['src'] = os.path.join(_BD, _b['src'])
import re as _re
for _b in blocks:
    if 'text' in _b:
        _b['text'] = _re.sub(r'\s+(?=[ါ-ှ၊။၏])', '', _b['text'])
# usage: kindle_typeset.py blocks.json source.pdf "part label" out.html "title line 1" "title line 2" "note"
# author name comes from the BOOK_AUTHOR environment variable
TITLE1 = sys.argv[5] if len(sys.argv) > 5 else ''
TITLE2 = sys.argv[6] if len(sys.argv) > 6 else ''
NOTE = sys.argv[7] if len(sys.argv) > 7 else 'Retyped Kindle edition'
AUTHOR = os.environ.get('BOOK_AUTHOR', '')
SCALE = 0.5   # original 24pt body -> 12pt

def uri(im, fmt='PNG', q=85):
    b = io.BytesIO()
    if fmt == 'JPEG': im.convert('RGB').save(b, 'JPEG', quality=q)
    else: im.save(b, 'PNG', optimize=True)
    return f'data:image/{fmt.lower()};base64,' + base64.b64encode(b.getvalue()).decode()

# cover: render page 1 and crop to the union of its images
doc = fitz.open(src_pdf); p = doc[0]
rects = [fitz.Rect(i['bbox']) for i in p.get_image_info() if fitz.Rect(i['bbox']).width > 100]
if rects:
    r = rects[0]
    for x in rects[1:]: r |= x
    pix = p.get_pixmap(dpi=200, clip=r)
    cover = Image.open(io.BytesIO(pix.tobytes('png')))
    cover_html = f'<section class="cover"><img src="{uri(cover, "JPEG", 88)}"></section>'
else:   # typed (WinInnwa) sources have no cover picture: make a typographic cover
    cover_html = (f'<section class="cover tc"><div><div class="ct1">{TITLE1}</div><div class="ct2">{TITLE2}</div>'
                  + (f'<div class="ct3">{part_label}</div>' if part_label.strip('() ') else '')
                  + f'<div class="cau">{AUTHOR}</div></div></section>')

parts = [cover_html,
         f'<section class="tp"><div class="t1">{TITLE1}</div><div class="t2">{TITLE2}</div>'
         + (f'<div class="pt">{part_label}</div>' if part_label.strip('() ') else '')
         + (f'<div class="au">{AUTHOR}</div>' if AUTHOR else '') + f'<div class="note">{NOTE}</div></section>']
marks = []
for b in blocks:
    t = b.get('type')
    if t == 'h':
        marks.append(b['text'])
        parts.append(f'<h2><span class="mk">QQMARK{len(marks):03d}</span>{html.escape(b["text"])}</h2>')
    elif t == 'h2':
        parts.append(f'<h3>{html.escape(b["text"])}</h3>')
    elif t == 'center':
        parts.append(f'<p class="c">{html.escape(b["text"])}</p>')
    elif t == 'note':
        body = html.escape(b['text'])
        body = body.replace('မှတ်ချက်။ ။', '<b>မှတ်ချက်။</b> ။', 1).replace('စာကြွင်း။ ။', '<b>စာကြွင်း</b><br>', 1)
        parts.append(f'<div class="note-box"><p class="ni">{body}</p>' + (f'<p class="sig">{html.escape(b["sig"])}</p>' if b.get('sig') else '') + '</div>')
    elif t == 'break':
        parts.append('<p class="orn">✻ ✻ ✻</p>')
    elif t == 'pic':
        im = Image.open(b['src'])
        parts.append(f'<figure class="pic"><img src="{uri(im, "JPEG", 82)}"></figure>')
    elif t == 'img':
        im = Image.open(b['src'])
        w = min(b['w'] * SCALE * 1.25, 290); ind = min(b['indent'] * SCALE, 40)
        parts.append(f'<div class="ln" style="padding-left:{ind:.1f}pt"><img src="{uri(im)}" style="width:{w:.1f}pt"></div>')
    elif t == 'p':
        cls = '' if b.get('indent') else ' class="ni"'
        _pieces = _re.split(r"([A-Za-z][A-Za-z.,'\-]*(?: [A-Za-z][A-Za-z.,'\-]*)*)", b["text"])
        body = ''.join((f'<span class="lat">{html.escape(x)}</span>' if k % 2 else html.escape(x)) for k, x in enumerate(_pieces))
        parts.append(f'<p{cls}>{body}</p>')

CSS = """
@page { size: 4.25in 5.667in; margin: 0.28in 0.24in 0.36in 0.24in;
  @bottom-center { content: counter(page); font: 7pt 'Padauk Book', serif; color: #666; } }
@page cover { margin: 0; @bottom-center { content: none; } }
@page plain { @bottom-center { content: none; } }
html { font-family: 'Padauk Book', 'Padauk', serif; font-size: 12pt; color: #000; }
body { margin: 0; }
p { margin: 0; text-indent: 1.4em; line-height: 1.9; text-align: left; orphans: 2; widows: 2; }
p.ni { text-indent: 0; }
p.c { text-align: center; text-indent: 0; margin: 0.08in 0; }
p.orn { text-align: center; text-indent: 0; color: #777; margin: 0.12in 0; font-size: 9pt; }
h2 { break-before: page; font-family: 'Padauk', sans-serif; font-weight: 700; font-size: 15pt; line-height: 1.75;
     text-align: center; margin: 0.45in 0 0.25in; }
h2::after { content: ''; display: block; width: 0.6in; border-top: 1px solid #999; margin: 0.12in auto 0; }
h3 { font-family: 'Padauk', sans-serif; font-weight: 700; font-size: 12.5pt; text-align: center; margin: -0.1in 0 0.2in; line-height: 1.7; }
h2 + p, h3 + p { text-indent: 0; }
.ln { line-height: 0; margin: 0.035in 0; }
.ln img { max-width: 100%; }
.pic { margin: 0.1in 0; text-align: center; break-inside: avoid; }
.pic img { max-width: 100%; max-height: 4.6in; }
.note-box { border: 1.2px solid #000; border-radius: 8pt; padding: 0.08in 0.12in; margin: 0.15in 0; break-inside: avoid; font-style: italic; }
.note-box p.sig { text-align: right; font-weight: 700; font-style: normal; }
.lat { font-family: 'Noto Serif', serif; font-size: 0.92em; }
.mk { font: 1px sans-serif; color: #fff; position: absolute; }
.cover { page: cover; break-after: page; width: 4.25in; height: 5.667in; display: flex; align-items: center; justify-content: center; background: #fff; }
.cover img { max-width: 4.25in; max-height: 5.667in; }
.tc { background: #1d2b3a; color: #f3ead8; text-align: center; }
.tc .ct1 { font-family: 'Padauk', sans-serif; font-weight: 700; font-size: 17pt; line-height: 1.9; }
.tc .ct2 { font-family: 'Padauk', sans-serif; font-weight: 700; font-size: 24pt; line-height: 1.8; margin-top: 0.1in; }
.tc .ct3 { font-size: 13pt; margin-top: 0.1in; }
.tc .cau { font-size: 15pt; margin-top: 0.9in; border-top: 1px solid #c9b78f; padding-top: 0.12in; display: inline-block; }
.tp { page: plain; break-after: page; text-align: center; padding-top: 1.1in; }
.t1 { font-family: 'Padauk', sans-serif; font-weight: 700; font-size: 16pt; line-height: 1.8; }
.t2 { font-family: 'Padauk', sans-serif; font-weight: 700; font-size: 18pt; line-height: 1.8; }
.pt { font-size: 13pt; margin-top: 0.12in; }
.au { font-size: 14pt; margin-top: 0.5in; }
.note { font-family: sans-serif; font-size: 6pt; color: #888; margin-top: 1.2in; }
"""
title = f'{TITLE1} {TITLE2} {part_label} — {AUTHOR}'.replace('  ', ' ').replace(' ()', '')
docu = f'<!DOCTYPE html><html lang="my"><head><meta charset="utf-8"><title>{title}</title><style>{CSS}</style></head><body>{"".join(parts)}</body></html>'
# Chrome sometimes refuses to break Burmese lines at plain spaces, so one line
# overflows and the whole book gets printed shrunk. A zero-width space after each
# space gives it a guaranteed break point.
_h, _b = docu.split('<body>', 1)
docu = _h + '<body>' + ''.join(x if x.startswith('<') else x.replace(' ', ' \u200b') for x in _re.split(r'(<[^>]*>)', _b))
open(out_html, 'w').write(docu)
json.dump({'marks': marks, 'title': title}, open(out_html + '.marks.json', 'w'), ensure_ascii=False)
print('html', len(docu), 'chapters', len(marks))
