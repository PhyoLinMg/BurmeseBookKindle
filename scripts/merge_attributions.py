"""Global first proofreading step: re-attach split quote attributions.
OCR often puts `ဟု မေးလေ၏။` / `ဟူ၍ ...` in its own paragraph after the quote it belongs to.
usage: merge_attributions.py blocks.json   (edits in place, prints how many merged)"""
import json, re, sys
p = sys.argv[1]; b = json.load(open(p)); out = []; n = 0
START = re.compile(r'^(ဟု|ဟူ၍|ဟူသော|ဟူ၏|ဟုဆို|ဟူလျှင်)(\s|$)')
for x in b:
    if x['type'] == 'p' and START.match(x['text']) and out and out[-1]['type'] == 'p' and out[-1]['text'].rstrip().endswith(('”', '’')):
        out[-1]['text'] = out[-1]['text'].rstrip() + ' ' + x['text']; n += 1
    else: out.append(x)
json.dump(out, open(p, 'w'), ensure_ascii=False); print('merged', n)
