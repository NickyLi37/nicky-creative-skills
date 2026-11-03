"""Lay natural-speed narration onto a film authored in story frames, and derive the story-time warp.

The visuals are authored once, in "story frames". Each narration line owns a slot in story frames. Here every
line gets its natural length in film frames, the gaps between lines are the story gaps scaled up (with a floor),
chapter turns get an extra pause, and optional per-gap extras push later lines on (used to land score sections
on chosen lines). The film frame -> story frame curve is a least-squares fit through the line starts (tight) and
ends (loose) with a penalty on its second difference, so the picture slows into pauses instead of stopping dead.

Usage:
  plan_warp.py --slots slots.json --lines lines.json --out render/src/vo.js [--extra '{"24": 24}']

slots.json  {"fps": 24, "story_end": 3960, "slots": [[s0, s1], ...], "chapter_starts": [240, ...],
             "gap_scale": 1.25, "min_gap": 26, "chapter_pause": 40, "tail_scale": 1.2, "smooth": 5e4}
             (everything but slots / story_end is optional; frames are story frames)
lines.json  {"lines": [{"dur": 3.23}, ...]}   one entry per slot, natural duration in seconds
--extra     {"gap index": extra film frames}; gap i sits between line i and line i+1

Writes an ES module exporting VO (rows [film start, film length, story slot start, story slot end]),
FILM_END, STORY_END and WARP (story frame for every film frame).
"""
import argparse
import json
from pathlib import Path

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl


def smooth_warp(rows, end, story_end, smooth):
    n = end + 1
    knots = [(0, 0, 1e3), (end, story_end, 1e3)]
    for f0, ln, s0, s1 in rows:
        knots += [(f0, s0, 4.0), (f0 + ln, s1, 0.5)]
    A = sp.csr_matrix((np.ones(len(knots)), (np.arange(len(knots)), [k[0] for k in knots])), shape=(len(knots), n))
    W = sp.diags([k[2] for k in knots])
    D = sp.diags([1.0, -2.0, 1.0], [0, 1, 2], shape=(n - 2, n))
    S = spl.spsolve((A.T @ W @ A + smooth * D.T @ D).tocsc(), A.T @ W @ np.array([k[1] for k in knots], float))
    S = np.maximum.accumulate(np.clip(S, 0, story_end))
    print(f"story speed {np.diff(S).min():.2f}..{np.diff(S).max():.2f} story frames per film frame")
    return S


def plan(cfg, lines, extra):
    slots, fps = cfg["slots"], cfg.get("fps", 24)
    chapters = cfg.get("chapter_starts", [])
    assert len(lines) == len(slots), f"{len(lines)} lines for {len(slots)} slots"
    rows, t = [], slots[0][0]
    for i, ((s0, s1), ln) in enumerate(zip(slots, lines)):
        n = round(ln["dur"] * fps)
        rows.append([t, n, s0, s1])
        if i + 1 < len(slots):
            gap = max(cfg.get("min_gap", 26), round((slots[i + 1][0] - s1) * cfg.get("gap_scale", 1.25)))
            if any(s1 <= c < slots[i + 1][0] for c in chapters):
                gap += cfg.get("chapter_pause", 40)
            gap += int(extra.get(str(i), 0))
            t += n + gap
    end = rows[-1][0] + rows[-1][1] + round((cfg["story_end"] - slots[-1][1]) * cfg.get("tail_scale", 1.2))
    return rows, end


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--slots", required=True)
    ap.add_argument("--lines", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--extra", default="{}")
    a = ap.parse_args()
    cfg = json.loads(Path(a.slots).read_text())
    lines = json.loads(Path(a.lines).read_text())["lines"]
    rows, end = plan(cfg, lines, json.loads(a.extra))
    fps = cfg.get("fps", 24)
    out = ["// Narration placement (written by plan_warp.py). One row per subtitle line:",
           "// [film start frame, film length (natural speed), story slot start, story slot end].",
           "// The story slots are frames of the authored timeline; the film stretches them to fit the voice.",
           "export const VO = ["]
    out += [f"  [{a_}, {b}, {c}, {d}]," for a_, b, c, d in rows]
    out += ["];", f"export const FILM_END = {end};", f"export const STORY_END = {cfg['story_end']};",
            "// story frame for each film frame (smoothed warp)",
            "export const WARP = [" + ",".join(f"{v:.1f}" for v in
                                               smooth_warp(rows, end, cfg["story_end"], cfg.get("smooth", 5e4))) + "];", ""]
    Path(a.out).write_text("\n".join(out))
    print(f"film {end} frames = {end / fps:.1f} s; speech {sum(r[1] for r in rows) / fps:.1f} s")


if __name__ == "__main__":
    main()
