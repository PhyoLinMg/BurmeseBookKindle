import json, re, sys
# usage: apply_edits.py blocks.json edits.json start_block_index
bp, ep, start = sys.argv[1], sys.argv[2], int(sys.argv[3])
b = json.load(open(bp)); edits = json.load(open(ep)); miss = []
for old, new in edits:
    hits = [i for i in range(start, len(b)) if b[i]['type'] in ('p','note','center') and (b[i]['text'].strip()==old.strip() if new=='@DEL@' else old in b[i]['text'])]
    if not hits: miss.append(old[:40]); continue
    i = hits[0]
    if new == '@JOIN@':   # append the next text block to this one
        j = i + 1
        b[i]['text'] = b[i]['text'].rstrip() + ' ' + b[j]['text'].lstrip(); b.pop(j); continue
    if new.startswith('@SET@'): b[i]['text'] = new[5:]; continue   # replace the whole block
    b[i]['text'] = b[i]['text'].replace(old, new, 1)
out = []
for x in b:
    t = x.get('text', '')
    if x['type'] in ('p','note') and t.strip() == '@DEL@': continue
    if x['type'] == 'p' and ('\n\n' in t or t.startswith(('@NOTE@','@BREAK@','@H@','@H2@','@C@','@PIC@'))):
        for piece in t.split('\n\n'):
            piece = piece.strip()
            if not piece: continue
            if piece.startswith('@NOTE@'):
                out.append({'type':'note','text':'မှတ်ချက်။ ။ '+re.sub(r'\s*\(?စာရေးသူ\)?\s*$','',piece[6:].strip()),'sig':'စာရေးသူ'})
            elif piece.startswith('@BREAK@'): out.append({'type':'break'})
            elif piece.startswith('@H2@'): out.append({'type':'h2','text':piece[4:].strip()})
            elif piece.startswith('@C@'): out.append({'type':'center','text':piece[3:].strip()})
            elif piece.startswith('@PIC@'): out.append({'type':'pic','src':piece[5:].strip()})
            elif piece.startswith('@H@'): out.append({'type':'h','text':piece[3:].strip()})
            else: out.append({'type':'p','text':piece,'indent':True})
    else: out.append(x)
json.dump(out, open(bp,'w'), ensure_ascii=False)
print('applied', len(edits)-len(miss), '/', len(edits), 'missing:', miss)
