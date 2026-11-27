"""Render a scanned book PDF to one PNG per book page: NNNN.png (1-based, book order).

usage: prepare_scans.py book.pdf out_dir [--dpi 200] [--twoup]
  --twoup  the scan has two book pages side by side on each PDF page; split them
           (gutter found from the ink profile, each half deskewed and trimmed).
After running, open a few PNGs and check page 1 is the cover and the numbering
matches the printed page numbers (offset is fine, but note it)."""
import sys, os, glob, subprocess, shutil, tempfile, argparse
ap = argparse.ArgumentParser(); ap.add_argument('pdf'); ap.add_argument('out')
ap.add_argument('--dpi', type=int, default=200); ap.add_argument('--twoup', action='store_true')
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
tmp = tempfile.mkdtemp()
subprocess.run(['pdftoppm', '-r', str(a.dpi), '-gray', '-png', a.pdf, os.path.join(tmp, 'p')], check=True)
files = sorted(glob.glob(os.path.join(tmp, 'p-*.png')))
if not a.twoup:
    for i, f in enumerate(files, 1): shutil.move(f, os.path.join(a.out, f'{i:04d}.png'))
else:
    here = os.path.dirname(os.path.abspath(__file__)); halves = os.path.join(tmp, 'h')
    shutil.copy(files[0], os.path.join(a.out, '0001.png'))      # split_twoup.py skips the cover page
    subprocess.run([sys.executable, os.path.join(here, 'split_twoup.py'), tmp, halves], check=True)
    n = 2
    for f in sorted(glob.glob(os.path.join(halves, '*.png'))):
        shutil.move(f, os.path.join(a.out, f'{n:04d}.png')); n += 1
print(len(glob.glob(os.path.join(a.out, '*.png'))), 'pages in', a.out)
