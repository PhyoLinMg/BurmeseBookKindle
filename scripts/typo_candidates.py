"""List likely typos: rare words with a frequent near-twin (one syllable-mark edit away), across the whole book.
usage: typo_candidates.py blocks.json [min_twin_count]
Prints: rare_form (count) -> frequent_form (count) | context. Review each by eye; many are real words."""
import json, re, sys, collections
b = json.load(open(sys.argv[1])); K = int(sys.argv[2]) if len(sys.argv) > 2 else 3
T = [x.get('text', '') for x in b]
words = collections.Counter(w for t in T for w in re.findall(r'[က-႟]+', t))
# split into syllable-ish units for cheap edit distance on characters
def edits1(w):
    out = set()
    for i in range(len(w) + 1):
        if i < len(w): out.add(w[:i] + w[i + 1:])                       # delete
        for c in 'ါာိီုူေဲံ့်းျြွှ္':
            out.add(w[:i] + c + w[i:])                                   # insert mark
            if i < len(w): out.add(w[:i] + c + w[i + 1:])               # replace with mark
        if i < len(w) - 1: out.add(w[:i] + w[i + 1] + w[i] + w[i + 2:]) # swap
    return out
res = []
for w, n in words.items():
    if n > 1 or len(w) < 4: continue
    best = max(((words[v], v) for v in edits1(w) if v in words and v != w), default=None)
    if best and best[0] >= K:
        ctx = next(t for t in T if w in t); i = ctx.find(w)
        res.append((w, n, best[1], best[0], ctx[max(0, i - 25):i + len(w) + 25]))
for r in sorted(res, key=lambda r: -r[3]): print(f'{r[0]} ({r[1]}) -> {r[2]} ({r[3]}) | {r[4]}')
print(len(res), 'candidates')
