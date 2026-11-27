"""Gutter of a two-up sheet = darkest (shadow) column among text-free columns in the middle 38-62%."""
import numpy as np
from PIL import Image
def gutter(im):
    a = np.array(im.convert('L')).astype(int); h, w = a.shape
    band = a[int(h*.12):int(h*.88)]
    dens = np.convolve((np.abs(np.diff(band, axis=0)) > 45).mean(axis=0), np.ones(9)/9, mode='same')
    dark = np.convolve(band.mean(axis=0), np.ones(9)/9, mode='same')
    lo, hi = int(w*.38), int(w*.62)
    cand = [x for x in range(lo, hi) if dens[x] < 0.03]
    if not cand: return w // 2, 999
    g = min(cand, key=lambda x: dark[x]); return g, int(dark[g])
if __name__ == '__main__':
    import sys, glob
    for f in sorted(glob.glob(sys.argv[1]))[1:]:
        im = Image.open(f); g, d = gutter(im); print(f[-7:-4], im.width, g, round(g/im.width, 3), d)
