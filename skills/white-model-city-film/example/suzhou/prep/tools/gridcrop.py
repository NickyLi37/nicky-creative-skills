"""Crop an image region and overlay a labelled pixel grid (for reading coordinates by eye).
Usage: gridcrop.py <img> <x0> <y0> <x1> <y1> <step> <out> [maxw]"""
import sys
from PIL import Image, ImageDraw, ImageFont
Image.MAX_IMAGE_PIXELS = None
img, x0, y0, x1, y1, step, out = sys.argv[1], *map(int, sys.argv[2:7]), sys.argv[7]
maxw = int(sys.argv[8]) if len(sys.argv) > 8 else 1400
im = Image.open(img).convert("RGB").crop((x0, y0, x1, y1))
s = min(1.0, maxw / im.width)
im = im.resize((int(im.width * s), int(im.height * s)))
d = ImageDraw.Draw(im)
try:
    f = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 14)
except OSError:
    f = ImageFont.load_default()
for gx in range((x0 // step + 1) * step, x1, step):
    X = (gx - x0) * s
    d.line([(X, 0), (X, im.height)], fill=(255, 60, 60), width=1)
    d.text((X + 2, 2), str(gx), fill=(255, 220, 0), font=f)
for gy in range((y0 // step + 1) * step, y1, step):
    Y = (gy - y0) * s
    d.line([(0, Y), (im.width, Y)], fill=(60, 160, 255), width=1)
    d.text((2, Y + 2), str(gy), fill=(0, 255, 255), font=f)
im.save(out, quality=90)
