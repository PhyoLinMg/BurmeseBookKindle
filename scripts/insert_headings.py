"""Insert chapter headings that the OCR left inside paragraphs (headings in the middle or at the foot of a page).
usage: insert_headings.py blocks.json headings.json
headings.json: [["text as it appears in the OCR", "heading as it should read"], ...] in book order.
Each OCR string is searched from the previous heading onward; the paragraph is split around it.
Prints misses — fix the OCR string (copy it from show_ch output) and rerun."""
import json, sys
b = json.load(open(sys.argv[1])); hs = json.load(open(sys.argv[2])); pos = 0; miss = []
for ocr, title in hs:
    for i in range(pos, len(b)):
        x = b[i]
        if x['type'] == 'p' and ocr in x['text']:
            pre, post = x['text'].split(ocr, 1)
            new = []
            if pre.strip(): new.append({'type': 'p', 'text': pre.strip(), 'indent': True})
            new.append({'type': 'h', 'text': title})
            if post.strip(): new.append({'type': 'p', 'text': post.strip(), 'indent': True})
            b[i:i + 1] = new; pos = i + len(new); break
    else: miss.append(ocr)
json.dump(b, open(sys.argv[1], 'w'), ensure_ascii=False)
print('inserted', len(hs) - len(miss), 'missing:', miss)
