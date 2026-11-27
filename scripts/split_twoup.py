import sys, glob, os
import numpy as np
from PIL import Image
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gutter import gutter

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)

def deskew(im):
    a = (np.array(im.resize((im.width // 3, im.height // 3))) < 128)
    best, ang = -1, 0
    for d in np.arange(-2.0, 2.01, 0.2):
        r = np.array(Image.fromarray((a * 255).astype(np.uint8)).rotate(d, fillcolor=0)) > 0
        v = r.sum(axis=1).astype(float); s = ((v[1:] - v[:-1]) ** 2).sum()
        if s > best: best, ang = s, d
    return im.rotate(ang, fillcolor=255, resample=Image.BICUBIC), ang

def bbox(a):
    m = a < 128
    rows = np.where(m.mean(axis=1) > 0.003)[0]; cols = np.where(m.mean(axis=0) > 0.004)[0]
    if len(rows) == 0: return None
    return rows[0], rows[-1] + 1, cols[0], cols[-1] + 1

def work(f):
    idx = int(os.path.basename(f).split('-')[1].split('.')[0])
    im = Image.open(f).convert('L')
    a = np.array(im); h, w = a.shape
    g, _ = gutter(im)
    res = []
    for k, part in enumerate((im.crop((0, 0, g, h)), im.crop((g, 0, w, h)))):
        # strip outer page-edge dark borders
        pa = np.array(part)
        part, ang = deskew(part)
        pa = np.array(part)
        # remove dark scanner borders: columns/rows that are mostly black
        colm = (pa < 100).mean(axis=0); rowm = (pa < 100).mean(axis=1)
        pa[:, colm > 0.5] = 255; pa[rowm > 0.5, :] = 255
        b = bbox(pa)
        name = os.path.join(out, f'{idx:03d}_{k}.png')
        if b is None:
            Image.new('L', (10, 10), 255).save(name)
        else:
            r0, r1, c0, c1 = b
            Image.fromarray(pa[max(0, r0 - 10):r1 + 10, max(0, c0 - 10):c1 + 10]).save(name)
        res.append((idx, k, round(ang, 1)))
    return res

if __name__ == '__main__':
    files = sorted(glob.glob(os.path.join(src, 'p-*.png')))
    files = [f for f in files if not f.endswith('-001.png')]
    with Pool(os.cpu_count()) as p:
        r = p.map(work, files)
    print(len(r) * 2, 'pages; sample angles', [x for rr in r[:6] for x in rr])
