"""print blocks a..b of chapter N limited to ~LIMIT chars. usage: chunk.py blocks.json N from_block [limit]"""
import json,sys
b=json.load(open(sys.argv[1])); n=int(sys.argv[2]); a=int(sys.argv[3]); L=int(sys.argv[4]) if len(sys.argv)>4 else 9000
hs=[i for i,x in enumerate(b) if x['type']=='h']+[len(b)]; end=hs[n+1]; tot=0
i=max(a,hs[n])
while i<end and tot<L:
    t=b[i].get('text',b[i].get('src','')); print(f"[{i}]{b[i]['type'][0]} {t}"); tot+=len(t); i+=1
print('NEXT', i if i<end else 'END', 'chapter_end', end)
