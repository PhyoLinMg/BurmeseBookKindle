"""Measure the body font size actually printed in a PDF (not what the CSS asked for).
usage: check_fontsize.py book.pdf [more.pdf ...]
Chrome silently shrinks the whole book when any line overflows the page, so a 12pt
stylesheet can come out at 8pt. Every book in the series must report 12.0."""
import sys, collections, fitz
for f in sys.argv[1:]:
    d = fitz.open(f); c = collections.Counter()
    for pg in list(d)[5:min(len(d), 60)]:
        for b in pg.get_text('dict')['blocks']:
            for l in b.get('lines', []):
                for s in l['spans']: c[round(s['size'], 1)] += len(s['text'])
    size = c.most_common(1)[0][0] if c else None
    print(f'{f}: body {size}pt, {len(d)} pages, {len(d.get_toc())} bookmarks', '' if size == 12.0 else '  <-- NOT 12pt, see SKILL.md "Shrunken text"')
