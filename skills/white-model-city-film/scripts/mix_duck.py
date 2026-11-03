"""Mix a continuous score under the narration without flattening it.

Under a line only the speech band (250 Hz - 5 kHz) of the score dips, and only by as much as the score actually
competes there: nothing when it is already quiet, at most --max-dip dB when it is full. Lows and highs carry on,
so a swell under a line keeps its weight. The whole score also eases by a fifth of that dip (about 0.9 dB at most).
The last 3 s of the score are faded so the film never ends on a cut.

Usage:
  mix_duck.py --vo-js render/src/vo.js --vo vo/vo_track.wav --music music/score.wav --out vo/mix.wav
              [--music-start 0] [--bed -4] [--max-dip 4.5] [--vo-gain 2.5] [--fps 24]

--music-start: film second where the score's first sample plays (0 = from the first frame, which viewers expect).
Inputs: 48 kHz, mono/stereo, 16- or 32-bit integer PCM WAV (convert other formats with ffmpeg first).
Output is 32-bit float stereo, before the master limiter of the encode step.
"""
import argparse
import re
import wave
from pathlib import Path

import numpy as np
from scipy.signal import butter, sosfiltfilt

SR = 48000
CLEAR = 9.0           # the score's speech band is left alone when it sits this far below the voice (dB)
ATT, REL = 0.45, 0.9  # seconds: the dip leads the line and recovers after it


def read(fn):
    with wave.open(str(fn)) as w:
        sr, ch, sw, n = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
        x = np.frombuffer(w.readframes(n), {2: np.int16, 4: np.int32}[sw]).astype(np.float64) / (2 ** (8 * sw - 1))
    assert sr == SR, f"{fn}: {sr} Hz, resample to {SR} first"
    x = x.reshape(-1, ch)
    return np.repeat(x, 2, axis=1) if ch == 1 else x


def write(fn, x):
    data = x.astype(np.float32).tobytes()
    with open(fn, "wb") as f:
        f.write(b"RIFF" + (36 + len(data)).to_bytes(4, "little") + b"WAVEfmt ")
        f.write((16).to_bytes(4, "little") + (3).to_bytes(2, "little") + (2).to_bytes(2, "little"))
        f.write(SR.to_bytes(4, "little") + (SR * 8).to_bytes(4, "little") + (8).to_bytes(2, "little"))
        f.write((32).to_bytes(2, "little") + b"data" + len(data).to_bytes(4, "little") + data)


def level_db(x, win):
    p = np.convolve((x ** 2).mean(1) if x.ndim == 2 else x ** 2, np.ones(win) / win, "same")
    return 10 * np.log10(p + 1e-12)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    for k in ("--vo-js", "--vo", "--music", "--out"):
        ap.add_argument(k, required=True)
    ap.add_argument("--music-start", type=float, default=0.0)
    ap.add_argument("--bed", type=float, default=-4.0, help="score level against the narration overall (dB)")
    ap.add_argument("--max-dip", type=float, default=4.5, help="most the speech band dips under a line (dB)")
    ap.add_argument("--vo-gain", type=float, default=2.5)
    ap.add_argument("--fps", type=int, default=24)
    a = ap.parse_args()

    vo_js = Path(a.vo_js).read_text()
    rows = [tuple(map(int, m)) for m in re.findall(r"\[(\d+), (\d+), \d+, \d+\]", vo_js)]
    film_end = int(re.search(r"FILM_END = (\d+)", vo_js).group(1))
    n = round(film_end / a.fps * SR)

    vo = read(a.vo)[:n] * 10 ** (a.vo_gain / 20)
    vo = np.pad(vo, ((0, n - len(vo)), (0, 0)))  # ffmpeg can end a track a few samples short
    music = np.zeros((n, 2))
    m = read(a.music)
    k0 = round(a.music_start * SR)
    seg = m[: max(0, n - k0)]
    music[k0:k0 + len(seg)] = seg
    music *= 10 ** (a.bed / 20)
    fade = round(3 * SR)
    music[-fade:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, fade)))[:, None]

    # complementary three-band split (zero-phase, sums back exactly)
    lo = sosfiltfilt(butter(4, 250, "low", fs=SR, output="sos"), music, axis=0)
    hi = sosfiltfilt(butter(4, 5000, "high", fs=SR, output="sos"), music, axis=0)
    mid = music - lo - hi

    mid_db = level_db(mid, round(0.4 * SR))
    t = np.arange(n) / SR
    act, want = np.zeros(n), np.zeros(n)
    ease = lambda u: 0.5 - 0.5 * np.cos(np.pi * np.clip(u, 0, 1))
    for f0, ln in rows:
        s, e = f0 / a.fps, (f0 + ln) / a.fps
        i0, i1 = max(0, int((s - ATT) * SR)), min(n, int((e + REL) * SR))
        tt = t[i0:i1]
        env = np.where(tt < s, ease((tt - (s - ATT)) / ATT), np.where(tt <= e, 1.0, 1 - ease((tt - e) / REL)))
        voice_db = np.percentile(level_db(vo[int(s * SR):int(e * SR)], SR // 10), 75)  # speaking level of this line
        act[i0:i1] = np.maximum(act[i0:i1], env)
        want[i0:i1] = np.maximum(want[i0:i1], env * np.clip(mid_db[i0:i1] - (voice_db - CLEAR), 0, a.max_dip))
    sm = round(0.35 * SR)  # the dip itself moves slowly: never pump on single notes
    dip = np.convolve(want, np.ones(sm) / sm, "same")
    score = (lo + hi + mid * (10 ** (-dip / 20))[:, None]) * (10 ** (-0.2 * dip / 20))[:, None]

    write(a.out, score + vo)
    spoken = act > 0.99
    print(f"film {n / SR:.1f} s, score from {a.music_start:.1f} s; speech-band dip under lines: "
          f"mean {dip[spoken].mean():.2f} dB, 90% {np.percentile(dip[spoken], 90):.2f} dB, max {dip.max():.2f} dB; "
          f"no dip for {np.mean(dip[spoken] < 0.3) * 100:.0f}% of spoken time")


if __name__ == "__main__":
    main()
