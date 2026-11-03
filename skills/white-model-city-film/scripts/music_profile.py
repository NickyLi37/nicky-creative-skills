"""Map a score before placing it: loudness and brightness over time.

Usage: music_profile.py score.wav [score2.wav ...]
Prints, per take:
  - a quarter-second loudness strip, 10 s per row (' .:-=+*#%@' from quiet to full, relative to the take's p95)
  - per-second spectral centroid in kHz (low = dark/warm, high = bright)
Read off the dark passages, the full entries, the brightest stretch and the coda, then place lines on them with
align_extras.py. Comparing two takes this way is faster and steadier than listening for structure.
"""
import sys
import wave

import numpy as np


def load(fn):
    w = wave.open(fn)
    sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
    x = np.frombuffer(w.readframes(w.getnframes()), {2: np.int16, 4: np.int32}[sw]).astype(float) / 2 ** (8 * sw - 1)
    return x.reshape(-1, ch).mean(1), sr


for fn in sys.argv[1:]:
    x, sr = load(fn)
    q = sr // 4
    db = np.array([10 * np.log10(np.mean(x[i:i + q] ** 2) + 1e-12) for i in range(0, len(x) - q, q)])
    db -= np.percentile(db, 95)
    print(f"== {fn}  {len(x) / sr:.1f} s   loudness (1 char = 0.25 s)")
    for t0 in range(0, int(len(x) / sr), 10):
        seg = db[t0 * 4:(t0 + 10) * 4]
        print(f"{t0:4d} " + "".join(" " if v < -30 else ".:-=+*#%@"[min(8, int((v + 30) / 3.4))] for v in seg))
    cen = []
    for i in range(0, len(x) - 2 * sr, sr):
        s = x[i:i + 2 * sr]
        S = np.abs(np.fft.rfft(s * np.hanning(len(s))))
        f = np.fft.rfftfreq(len(s), 1 / sr)
        cen.append((S * f).sum() / (S.sum() + 1e-12) / 1000)
    print("   centroid kHz per second (10 per row)")
    for t0 in range(0, len(cen), 10):
        print(f"{t0:4d} " + " ".join(f"{c:3.1f}" for c in cen[t0:t0 + 10]))
