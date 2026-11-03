"""Find frame-to-frame jumps in a rendered frame directory (cuts, camera lurches, popping layers).

Usage: qa_jumps.py <frames_dir> [--ignore-bottom 0.26]
Flags frames whose change is far above the local norm and groups consecutive ones into runs. Every run should
be a designed cut (two camera keys one frame apart) or a known fast move; anything else is a bug.
The bottom band (subtitles) is ignored because subtitle changes are expected jumps.
"""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("frames")
    ap.add_argument("--ignore-bottom", type=float, default=0.26)
    ap.add_argument("--fps", type=int, default=24)
    a = ap.parse_args()
    fs = sorted(Path(a.frames).glob("f*.png"))
    prev, d = None, []
    for f in fs:
        im = np.asarray(Image.open(f).convert("L").resize((240, 135), Image.BILINEAR), np.float32)
        im[int(135 * (1 - a.ignore_bottom)):, :] = 0
        if prev is not None:
            d.append(np.abs(im - prev).mean())
        prev = im
    d = np.array(d)
    med = np.array([np.median(d[max(0, i - 48):i + 48]) for i in range(len(d))])
    idx = np.where(((d - med) / (med + 0.3) > 2.5) & (d > 2.0))[0] + 1
    runs = []
    for i in idx:
        if runs and i - runs[-1][1] <= 2:
            runs[-1][1] = i
        else:
            runs.append([i, i])
    print(f"{len(fs)} frames, median change {np.median(d):.2f}")
    for s, e in runs:
        print(f"  frame {s}" + (f"-{e}" if e > s else "") + f"  ({s / a.fps:.2f} s)  change {d[s - 1]:.1f} vs local {med[s - 1]:.1f}")


if __name__ == "__main__":
    main()
