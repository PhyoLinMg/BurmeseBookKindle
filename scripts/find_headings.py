"""Find chapter-heading candidates in page scans: a short, centred text line with a tall gap above it.
usage: find_headings.py scans_dir [first last]  -> prints page, y-fraction, line width fraction
Use it to build the 'titles' map; confirm each hit by looking at the page."""
import sys, glob, os
import numpy as np
from PIL import Image
src = sys.argv[1]; a = int(sys.argv[2]) if len(sys.argv) > 2 else 1; z = int(sys.argv[3]) if len(sys.argv) > 3 else 9999
for f in sorted(glob.glob(os.path.join(src, '[0-9]' * 4 + '.png'))):
    n = int(os.path.basename(f)[:4])
    if n < a or n > z: continue
    im = np.array(Image.open(f).convert('L')); h, w = im.shape
    ink = im < 120
    rows = ink[:, int(w * .05):int(w * .95)].mean(axis=1) > 0.004
    # runs of text rows
    runs = []; y = 0
    while y < h:
        if rows[y]:
            s = y
            while y < h and rows[y]: y += 1
            if y - s > 8: runs.append((s, y))
        y += 1
    if len(runs) < 3: continue
    lh = np.median([e - s for s, e in runs]); gaps = [runs[0][0]] + [runs[i][0] - runs[i - 1][1] for i in range(1, len(runs))]
    mg = np.median(gaps[1:])
    for i, (s, e) in enumerate(runs):
        if i < 2 or s < h * 0.08 or e > h * 0.95: continue
        cols = np.where(ink[s:e].mean(axis=0) > 0.02)[0]
        if len(cols) == 0: continue
        x0, x1 = cols[0] / w, cols[-1] / w
        if gaps[i] > max(2.2 * mg, lh * 1.4) and (x1 - x0) < 0.75 and x0 > 0.15 and abs((x0 + x1) / 2 - 0.5) < 0.12:
            print(n, f'y={s / h:.2f}', f'w={x1 - x0:.2f}')
