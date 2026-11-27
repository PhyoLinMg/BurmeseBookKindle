"""Replace a run of blocks with retyped text (for pages whose OCR is beyond word-level fixing).
usage: replace_range.py blocks.json "first block starts with" "last block starts with" new.json [--from N]
  - Both ends are INCLUSIVE: the block starting with the last prefix is replaced too,
    so new.json must re-include its text if you only meant to replace up to it.
  - new.json: list of strings; "@H@title" = heading, "@BREAK@" = scene break, else a paragraph.
It prints the removed blocks: read them and confirm nothing outside the garbled stretch was lost."""
import json, sys
p, a, z, nf = sys.argv[1:5]; start = int(sys.argv[sys.argv.index('--from') + 1]) if '--from' in sys.argv else 0
b = json.load(open(p)); new = json.load(open(nf))
i = next(k for k in range(start, len(b)) if b[k].get('text', '').startswith(a))
j = next(k for k in range(i, len(b)) if b[k].get('text', '').startswith(z))
print(f'replacing blocks {i}..{j}:')
for k in range(i, j + 1): print('  -', b[k].get('text', b[k]['type'])[:70])
blk = [{'type': 'break'} if t == '@BREAK@' else {'type': 'h', 'text': t[3:]} if t.startswith('@H@') else {'type': 'p', 'text': t, 'indent': True} for t in new]
b[i:j + 1] = blk; json.dump(b, open(p, 'w'), ensure_ascii=False); print('inserted', len(blk))
