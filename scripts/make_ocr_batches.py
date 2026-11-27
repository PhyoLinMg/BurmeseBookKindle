"""Stamp each page image with a #PNNNN# marker and pack them into small PDFs for Google OCR.

usage: make_ocr_batches.py scans_dir out_dir [--per 10] [--skip 1,2,3]
Google Docs OCR keeps the stamped text, so after OCR every page's text starts with
#P0042# and assemble_blocks.py can split the OCR text back into book pages.
10 pages per batch keeps each upload small and each OCR export complete
(Google OCR is unreliable on large PDFs).
Writes out_dir/bNN.pdf and out_dir/hashes.txt (sha256 for the Drive upload file reference)."""
import sys, os, glob, hashlib, argparse
from PIL import Image, ImageDraw, ImageFont
ap = argparse.ArgumentParser(); ap.add_argument('scans'); ap.add_argument('out')
ap.add_argument('--per', type=int, default=10); ap.add_argument('--skip', default='')
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
skip = {int(x) for x in a.skip.split(',') if x}
pages = [(int(os.path.basename(f)[:4]), f) for f in sorted(glob.glob(os.path.join(a.scans, '[0-9][0-9][0-9][0-9].png')))]
pages = [(n, f) for n, f in pages if n not in skip]
try: font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 40)
except OSError: font = ImageFont.load_default()
def stamp(n, f):
    im = Image.open(f).convert('L'); band = 80
    out = Image.new('L', (im.width, im.height + band), 255); out.paste(im, (0, band))
    ImageDraw.Draw(out).text((20, 15), f'#P{n:04d}#', fill=0, font=font)
    return out
lines = []
for k in range(0, len(pages), a.per):
    chunk = [stamp(n, f) for n, f in pages[k:k + a.per]]
    name = os.path.join(a.out, f'b{k // a.per + 1:02d}.pdf')
    chunk[0].save(name, save_all=True, append_images=chunk[1:], resolution=200)
    lines.append(f'{os.path.abspath(name)} {hashlib.sha256(open(name, "rb").read()).hexdigest()}')
open(os.path.join(a.out, 'hashes.txt'), 'w').write('\n'.join(lines) + '\n')
print(len(lines), 'batches,', len(pages), 'pages ->', a.out)
