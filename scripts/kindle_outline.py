import sys, json, subprocess, re
from pypdf import PdfReader, PdfWriter
pdf, meta, out = sys.argv[1], json.load(open(sys.argv[2])), sys.argv[3]
r = PdfReader(pdf); w = PdfWriter(clone_from=r)
txt = subprocess.run(['pdftotext', pdf, '-'], capture_output=True, text=True).stdout.split('\f')
found = {}
for i, t in enumerate(txt):
    for m in re.findall(r'QQMARK(\d{3})', t): found.setdefault(int(m), i)
w.add_outline_item('မျက်နှာဖုံး', 0)
for k, title in enumerate(meta['marks'], 1):
    if k in found: w.add_outline_item(title, found[k])
w.page_mode = '/UseOutlines'
w.add_metadata({'/Title': meta['title'], '/Author': 'မင်းသိင်္ခ'})
w.write(out)
print('chapters', len(meta['marks']), 'bookmarked', len(found), 'pages', len(r.pages))
