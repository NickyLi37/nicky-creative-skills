"""Contact sheet of chosen frames, labelled with frame number and time, for a one-glance review.

Usage: contact_sheet.py <frames_dir> <out.jpg> 12,600,2400,3881 [--cols 4] [--fps 24]
Pick frames at every chapter start, every designed cut, the climax and the last second (fades and the end card
are where map edges, missing fonts and stray layers show up).
"""
import argparse

from PIL import Image, ImageDraw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("frames")
    ap.add_argument("out")
    ap.add_argument("list")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--fps", type=int, default=24)
    a = ap.parse_args()
    fr = [int(v) for v in a.list.split(",")]
    W, H = 480, 270
    rows = (len(fr) + a.cols - 1) // a.cols
    sheet = Image.new("RGB", (W * a.cols, H * rows))
    for k, f in enumerate(fr):
        im = Image.open(f"{a.frames}/f{f:05d}.png").convert("RGB").resize((W, H))
        ImageDraw.Draw(im).text((6, 6), f"{f}  {f / a.fps:.1f}s", fill=(255, 80, 80))
        sheet.paste(im, ((k % a.cols) * W, (k // a.cols) * H))
    sheet.save(a.out, quality=85)
    print(a.out)


if __name__ == "__main__":
    main()
