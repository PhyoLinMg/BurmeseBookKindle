"""Book-wide literal replacements in p/note/center/h blocks.
usage: global_replace.py blocks.json fixes.json   (fixes.json: [[old, new], ...]; every occurrence is replaced)
Prints the hit count per pair; a 0 means the pair didn't match (check spacing/characters)."""
import json, sys
b = json.load(open(sys.argv[1])); fx = json.load(open(sys.argv[2])); cnt = []
for old, new in fx:
    n = 0
    for x in b:
        if 'text' in x and old in x['text']:
            n += x['text'].count(old); x['text'] = x['text'].replace(old, new)
    cnt.append(n)
json.dump(b, open(sys.argv[1], 'w'), ensure_ascii=False)
print('hits:', cnt); print('zero:', [fx[i][0] for i, n in enumerate(cnt) if n == 0])
