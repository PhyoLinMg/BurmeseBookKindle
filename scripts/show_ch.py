import json, sys
b = json.load(open(sys.argv[1])); n = int(sys.argv[2])
hs = [i for i,x in enumerate(b) if x['type']=='h']; hs.append(len(b))
a, c = hs[n], hs[n+1]
for i in range(a, c):
    x = b[i]
    print(f"[{i}]{x['type'][0]} {x.get('text','')}")
