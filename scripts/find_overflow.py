"""List elements that overflow the Kindle page width (the cause of Chrome shrinking the whole book).
usage: find_overflow.py book.html"""
import sys
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    br = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
    pg = br.new_page(viewport={'width': 362, 'height': 800}); pg.emulate_media(media='print')
    pg.goto('file://' + __import__('os').path.abspath(sys.argv[1]))
    r = pg.evaluate("""() => { const W = document.body.clientWidth; const o = [];
      for (const e of document.querySelectorAll('p,h2,h3,div,figure')) {
        const r = e.getBoundingClientRect();
        if (e.scrollWidth > e.clientWidth + 1 || r.right > W + 1) o.push([e.tagName, Math.round(r.right), e.scrollWidth, e.clientWidth, e.textContent.slice(0, 80)]); }
      return [W, o.slice(0, 30)]; }""")
    print('body width', r[0]); [print(x) for x in r[1]]
    br.close()
