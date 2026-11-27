"""Rebuild blocks.json from the OCR text and re-apply every proofreading edit, in one command.

usage: pipeline.py work/config.json [--no-edits] [--no-finalize]

Steps (each one is optional except the first):
  1. assemble_blocks.py        OCR text -> blocks.json (config.json, see its docstring)
  2. merge_attributions.py     re-attach "ဟု …" lines to their quotes
  3. insert_headings.py        if config "headings": "headings.json" exists
  4. cleanup                   built-in OCR fixes + config "cleanup" (strip patterns, regex rules)
  5. edits                     every eNN*.json in config "edits_dir" (default: the config's folder),
                               in sorted order; NN = chapter index (the NN-th `h` block, 0-based)
                               and is the START passed to apply_edits.py
  6. finalize.py               if config "finalize": "finalize.json" exists

Why rebuild instead of editing blocks.json in place: the OCR draft is never touched by hand, every
fix lives in a small edit file, and the whole book can be regenerated after any upstream change
(re-OCR of one page, a new heading, a better cleanup rule) without losing proofreading work.

config.json extra keys (besides the assemble_blocks.py ones):
  "headings": "headings.json",
  "cleanup": {"default_rules": true,
              "strip": ["publisher footer regex", ...],       # deleted wherever they match
              "rules": [["regex", "replacement"], ...]},       # applied after the defaults
  "edits_dir": ".",
  "finalize": "finalize.json"
"""
import json, os, re, subprocess, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
cfg_path = os.path.abspath(sys.argv[1]); D = os.path.dirname(cfg_path)
C = json.load(open(cfg_path))
rel = lambda p: p if os.path.isabs(p) else os.path.join(D, p)
P = rel(C.get('out', 'blocks.json'))
run = lambda *a: subprocess.run([sys.executable, *a], check=True)

run(f'{HERE}/assemble_blocks.py', cfg_path)
run(f'{HERE}/merge_attributions.py', P)
if C.get('headings') and os.path.exists(rel(C['headings'])):
    run(f'{HERE}/insert_headings.py', P, rel(C['headings']))

# Google OCR confusions seen across many Burmese books, plus spacing normalisation.
DEFAULT_RULES = [
    (r'ဘော့', 'တော့'), (r'ကျွန်ဘော', 'ကျွန်တော'), (r'ပေါ့က္ခာ', 'ပေါ့ကွာ'), (r'ပေါ့က္ခ', 'ပေါ့ကွ'),
    (r'သဘည်း', 'သတည်း'), (r'လေ့၏', 'လေ၏'),
    (r' +([့် းါာိီုူဲံ])', r'\1'),          # stray space before a dependent mark
    (r'([။၊])(?=[^\s”’])', r'\1 '),            # space after ။ ၊
    (r' +([။၊])', r'\1'),                      # no space before ။ ၊
    (r'\.\.+', ' . . . '),                     # OCR ellipsis -> the books' spaced dots
    (r'\( ', '('), (r'\s{2,}', ' '),
    (r'(?<![၀-၉])၄င်း', '၎င်း'),             # ၎င်း read as digit 4
]
cl = C.get('cleanup', {})
rules = (DEFAULT_RULES if cl.get('default_rules', True) else []) + [tuple(r) for r in cl.get('rules', [])]
strip = cl.get('strip', [])
b = json.load(open(P))
for x in b:
    t = x.get('text')
    if not t: continue
    for q in strip: t = re.sub(q, '', t)
    for a, r in rules: t = re.sub(a, r, t)
    x['text'] = t.strip()
b = [x for x in b if not (x['type'] == 'p' and not x['text'])]
json.dump(b, open(P, 'w'), ensure_ascii=False)
print('assembled: blocks', len(b), 'chapters', sum(x['type'] == 'h' for x in b))

if '--no-edits' not in sys.argv:
    ed = rel(C.get('edits_dir', '.'))
    for f in sorted(glob.glob(os.path.join(ed, 'e[0-9][0-9]*.json'))):
        n = int(re.search(r'e(\d+)', os.path.basename(f)).group(1))
        hs = [i for i, x in enumerate(json.load(open(P))) if x['type'] == 'h']
        if n >= len(hs): print(os.path.basename(f), 'SKIPPED: no chapter', n); continue
        r = subprocess.run([sys.executable, f'{HERE}/apply_edits.py', P, f, str(hs[n])], capture_output=True, text=True)
        out = r.stdout.strip() or r.stderr.strip()
        flag = '' if out.endswith('missing: []') else '   <-- check'
        print(f'{os.path.basename(f):12s} {out}{flag}')

if '--no-finalize' not in sys.argv and C.get('finalize') and os.path.exists(rel(C['finalize'])):
    run(f'{HERE}/finalize.py', cfg_path)
