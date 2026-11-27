"""Which book page holds a phrase? Finds it in the OCR text and reports the last #PNNNN# marker before it.
usage: find_page.py "/abs/work/text/*.txt" "phrase one" ["phrase two" ...]"""
import re, sys, glob
files = sorted(glob.glob(sys.argv[1]))
for ph in sys.argv[2:]:
    hits = []
    for f in files:
        t = open(f, encoding='utf-8-sig').read(); i = t.find(ph)
        while i >= 0:
            m = re.findall(r'#\s*P\s*([0-9Oo]{4})\s*#', t[:i]); hits.append(m[-1] if m else '?'); i = t.find(ph, i + 1)
    print(ph, '->', ', '.join(sorted(set(hits))) or 'not found')
