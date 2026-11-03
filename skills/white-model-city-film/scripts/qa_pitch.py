"""Median pitch, pitch spread and a coarse contour of voice takes, to compare a re-voiced line with the rest.

Usage: qa_pitch.py line_a.wav [line_b.wav ...]
A line that should sound like the rest of the narration belongs inside the narration's p10-p90 median range.
In the Suzhou film the narration sat at 94-108 Hz; a "poetic" take at 114 Hz read as declamatory and a
pitched-down take at 87 Hz read as eerie.
"""
import sys
import wave

import numpy as np


def load(fn):
    w = wave.open(fn)
    sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
    x = np.frombuffer(w.readframes(w.getnframes()), {2: np.int16, 4: np.int32}[sw]).astype(float) / 2 ** (8 * sw - 1)
    return x.reshape(-1, ch).mean(1), sr


def f0_track(x, sr, fmin=70, fmax=300):
    hop, win = int(0.01 * sr), int(0.04 * sr)
    out = []
    for i in range(0, len(x) - win, hop):
        s = x[i:i + win] * np.hanning(win)
        if np.sqrt(np.mean(s ** 2)) < 0.01:
            out.append(np.nan)
            continue
        ac = np.correlate(s, s, "full")[win - 1:]
        lo, hi = int(sr / fmax), int(sr / fmin)
        k = lo + np.argmax(ac[lo:hi])
        out.append(sr / k if ac[k] > 0.35 * ac[0] else np.nan)
    return np.array(out)


meds = []
for fn in sys.argv[1:]:
    x, sr = load(fn)
    f0 = f0_track(x, sr)
    v = f0[~np.isnan(f0)]
    st = 12 * np.log2(v / np.median(v))
    meds.append(np.median(v))
    bins = [np.nanmedian(f0[i:i + 25]) if np.any(~np.isnan(f0[i:i + 25])) else np.nan for i in range(0, len(f0), 25)]
    print(f"{fn.split('/')[-1]:20s} {len(x) / sr:5.2f} s  median {np.median(v):4.0f} Hz  "
          f"spread {np.percentile(st, 90) - np.percentile(st, 10):4.1f} st  voiced {len(v) / 100:.2f} s")
    print("    " + " ".join("  - " if np.isnan(b) else f"{b:4.0f}" for b in bins))
if len(meds) > 3:
    print(f"medians: p10 {np.percentile(meds, 10):.0f}  median {np.median(meds):.0f}  p90 {np.percentile(meds, 90):.0f} Hz")
