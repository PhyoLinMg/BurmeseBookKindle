"""Copy Drive OCR exports (saved tool-result blobs) into text_dir as pNNNN.txt, named by the first #PNNNN# marker.
usage: collect_ocr.py text_dir [blob_glob]   (default glob: /tmp/claude-tool-results/*/mcp-Google_Drive-blob-*.txt)
Naming by marker means the download order doesn't matter; text_glob 'text_dir/p*.txt' sorts in book order."""
import sys, glob, re, os
out = sys.argv[1]; g = sys.argv[2] if len(sys.argv) > 2 else '/tmp/claude-tool-results/*/mcp-Google_Drive-blob-*.txt'
os.makedirs(out, exist_ok=True); n = 0
for f in glob.glob(g):
    t = open(f, 'rb').read().decode('utf-8-sig', 'replace')
    m = re.search(r'#\s*P\s*([0-9Oo]{4})\s*#', t)
    if not m: print('no marker:', f); continue
    p = int(m.group(1).replace('O', '0').replace('o', '0'))
    open(os.path.join(out, f'p{p:04d}.txt'), 'w').write(t); n += 1
print(n, 'files ->', out, sorted(os.listdir(out))[:3], '...', len(os.listdir(out)))
