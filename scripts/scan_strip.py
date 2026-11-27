"""Put several scan pages side by side in one image, to read them when the OCR is garbled.
usage: scan_strip.py scans_dir out.png 311 312 313 [--scale 0.66]
Three or four pages at 0.66 scale stay readable in one image view."""
import sys
from PIL import Image
argv = sys.argv[1:]; sc = 0.66
if '--scale' in argv: k = argv.index('--scale'); sc = float(argv[k + 1]); del argv[k:k + 2]
src, out, nums = argv[0], argv[1], argv[2:]
ims = [Image.open(f'{src}/{int(p):04d}.png').convert('L') for p in nums]
ims = [i.resize((int(i.width * sc), int(i.height * sc))) for i in ims]
c = Image.new('L', (sum(i.width for i in ims), max(i.height for i in ims)), 255); x = 0
for i in ims: c.paste(i, (x, 0)); x += i.width
c.save(out); print(out, c.size)
