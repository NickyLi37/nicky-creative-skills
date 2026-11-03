"""Solve the per-gap pauses that land chosen narration lines on chosen moments of the score.

Usage:
  align_extras.py --slots slots.json --lines lines.json --music-start 0 \
      --targets '[[24, 152.0, [13, 19]], [37, 244.0, [36]]]' [--base '{"24": 24}']

Each target is [line index, score second the line should start at, [gaps that absorb the push]]. Targets are
solved in order; each push is split evenly over its gaps. Pauses can only be added, so a target the base timing
already passes is reported and left alone: pick another take, start the score later in the take, or move the target.
Prints the extras JSON (paste into plan_warp.py --extra) and where every line then falls in film and score time.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from plan_warp import plan  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slots", required=True)
    ap.add_argument("--lines", required=True)
    ap.add_argument("--targets", required=True)
    ap.add_argument("--music-start", type=float, default=0.0)
    ap.add_argument("--base", default="{}")
    a = ap.parse_args()
    cfg = json.loads(Path(a.slots).read_text())
    lines = json.loads(Path(a.lines).read_text())["lines"]
    fps = cfg.get("fps", 24)
    extra = json.loads(a.base)
    for line, sec, gaps in json.loads(a.targets):
        rows, _ = plan(cfg, lines, extra)
        d = round((sec + a.music_start) * fps) - rows[line][0]
        if d < 0:
            print(f"line {line}: already at score {rows[line][0] / fps - a.music_start:.1f} s, "
                  f"{-d / fps:.1f} s past the target {sec} s; left as is")
            continue
        for i, g in enumerate(gaps):
            extra[str(g)] = extra.get(str(g), 0) + d // len(gaps) + (1 if i < d % len(gaps) else 0)
    rows, end = plan(cfg, lines, extra)
    print(json.dumps(extra))
    print(f"film {end / fps:.2f} s; score time at the end {end / fps - a.music_start:.1f} s")
    for k, (f0, n, _, _) in enumerate(rows):
        print(f"  line {k:2d}: film {f0 / fps:6.1f}-{(f0 + n) / fps:6.1f}   score {f0 / fps - a.music_start:6.1f}")


if __name__ == "__main__":
    main()
