"""Lay the natural-speed narration onto the film and derive the story-time warp.

Each line keeps a slot in the original (story) frames, where the visuals were authored. The line gets its
natural length in film frames; gaps between lines are the old gaps x1.25 (min ~1.1 s), plus 1.7 s more where
a chapter turns. Optional per-gap extra frames (EXTRA, set after looking at the score) push later lines on.
Writes render/src/vo.js.
"""
import json
import sys
from pathlib import Path

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl

ROOT = Path(__file__).parent.parent
# story-frame slot of each line (old timeline): start, end
SLOTS = [(14, 77), (124, 191), (252, 323), (335, 420), (448, 552), (560, 637), (656, 733), (752, 848), (858, 935),
         (942, 1000), (1012, 1040), (1046, 1133), (1141, 1213), (1221, 1313), (1352, 1441), (1452, 1527), (1538, 1580),
         (1660, 1771), (1782, 1857), (1890, 1944), (2028, 2118), (2120, 2170), (2176, 2200), (2206, 2322), (2338, 2395),
         (2404, 2460), (2490, 2570), (2580, 2660), (2676, 2770), (2786, 2890), (2916, 2990), (3040, 3140),
         (3146, 3186), (3202, 3302), (3328, 3432), (3468, 3560), (3570, 3668), (3680, 3745)]
CHAPTER_STARTS = [240, 432, 744, 1008, 1320, 2016, 2328, 2472, 2904, 3192, 3456, 3768]  # round 4: 07 拆与填 folded into 保护
STORY_END = 3960
EXTRA = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}  # {"gap index": extra frames}
SMOOTH = 5e4  # penalty on the change of story speed; line starts are held tight, line ends loosely


def smooth_warp(rows, end):
    """Story frame for every film frame: a least-squares curve through the line starts (tight) and ends (loose)
    with a penalty on its second difference, so the picture never lurches between slow pauses and fast lines."""
    n = end + 1
    knots = [(0, 0, 1e3), (end, STORY_END, 1e3)]
    for f0, ln, s0, s1 in rows:
        knots += [(f0, s0, 4.0), (f0 + ln, s1, 0.5)]
    A = sp.csr_matrix((np.ones(len(knots)), (np.arange(len(knots)), [k[0] for k in knots])), shape=(len(knots), n))
    W = sp.diags([k[2] for k in knots])
    D = sp.diags([1.0, -2.0, 1.0], [0, 1, 2], shape=(n - 2, n))
    S = spl.spsolve((A.T @ W @ A + SMOOTH * D.T @ D).tocsc(), A.T @ W @ np.array([k[1] for k in knots], float))
    S = np.maximum.accumulate(np.clip(S, 0, STORY_END))
    print(f"story speed {np.diff(S).min():.2f}..{np.diff(S).max():.2f}")
    return S


def main():
    lines = json.loads((ROOT / "vo/v4/lines.json").read_text())["lines"]
    assert len(lines) == len(SLOTS)
    rows, t = [], SLOTS[0][0]
    for i, ((s0, s1), ln) in enumerate(zip(SLOTS, lines)):
        n = round(ln["dur"] * 24)
        rows.append([t, n, s0, s1])
        if i + 1 < len(SLOTS):
            old_gap = SLOTS[i + 1][0] - s1
            gap = max(26, round(old_gap * 1.25))
            if any(s1 <= c < SLOTS[i + 1][0] for c in CHAPTER_STARTS):
                gap += 40
            gap += int(EXTRA.get(str(i), 0))
            t += n + gap
    end = rows[-1][0] + rows[-1][1] + round((STORY_END - SLOTS[-1][1]) * 1.2)
    out = ["// Narration placement (written by vo/plan_v2.py). One row per subtitle line:",
           "// [film start frame, film length (natural speed), story slot start, story slot end].",
           "// The story slots are frames of the authored timeline; the film stretches them to fit the voice.",
           "export const VO = ["]
    out += [f"  [{a}, {b}, {c}, {d}]," for a, b, c, d in rows]
    out += ["];", f"export const FILM_END = {end};", f"export const STORY_END = {STORY_END};",
            "// story frame for each film frame (smoothed warp)",
            "export const WARP = [" + ",".join(f"{v:.1f}" for v in smooth_warp(rows, end)) + "];", ""]
    (ROOT / "render/src/vo.js").write_text("\n".join(out))
    print(f"film {end} frames = {end / 24:.1f} s; speech {sum(r[1] for r in rows) / 24:.1f} s")


main()
