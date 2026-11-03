"""Mix the score under the narration without flattening it.

The score (vo/align.json "music", now music/music_E1.wav) enters at -offset seconds of film time (0 = first frame); the plan_v2.py
gap extras in vo/align.json place its break, climax and coda against the chapters. Under a line only the speech band (250 Hz - 5 kHz) dips, and
only by as much as the music actually competes there: nothing when the score is already quiet, at most MAX_DIP
when it is full. Lows and highs carry on, so a swell under a line keeps its weight.

Usage: mix_v2.py  ->  vo/mix_v2.wav (48 kHz stereo float, before the master limiter in out/encode.sh)
"""
import json
import re
import wave
from pathlib import Path

import numpy as np
from scipy.signal import butter, sosfiltfilt

ROOT = Path(__file__).parent.parent
SR = 48000
BED_DB = -4.0     # score level against the narration track overall
MAX_DIP = 4.5     # most the speech band ever dips under a line (dB)
CLEAR = 9.0       # speech band of the score is left alone when it sits this far below the voice (dB)
VO_GAIN_DB = 2.5
ATT, REL = 0.45, 0.9  # seconds: dip leads the line, recovers after it


def read(fn):
    with wave.open(str(fn)) as w:
        sr, ch, sw, n = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
        x = np.frombuffer(w.readframes(n), {2: np.int16, 4: np.int32}[sw]).astype(np.float64) / (2 ** (8 * sw - 1))
    assert sr == SR, fn
    return x.reshape(-1, ch)


def write(fn, x):
    x = x.astype(np.float32)
    with open(fn, "wb") as f:
        data = x.tobytes()
        f.write(b"RIFF" + (36 + len(data)).to_bytes(4, "little") + b"WAVEfmt ")
        f.write((16).to_bytes(4, "little") + (3).to_bytes(2, "little") + (2).to_bytes(2, "little"))
        f.write(SR.to_bytes(4, "little") + (SR * 8).to_bytes(4, "little") + (8).to_bytes(2, "little"))
        f.write((32).to_bytes(2, "little") + b"data" + len(data).to_bytes(4, "little") + data)


def level_db(x, win):
    """Smoothed RMS level in dB, sample-rate resolution via a running mean of the power."""
    p = np.convolve((x ** 2).mean(1) if x.ndim == 2 else x ** 2, np.ones(win) / win, "same")
    return 10 * np.log10(p + 1e-12)


def main():
    vo_js = (ROOT / "render/src/vo.js").read_text()
    rows = [tuple(map(int, m)) for m in re.findall(r"\[(\d+), (\d+), \d+, \d+\]", vo_js)]
    film_end = int(re.search(r"FILM_END = (\d+)", vo_js).group(1))
    align = json.loads((ROOT / "vo/align.json").read_text())
    offset = -align["offset"]  # score start, film seconds
    n = round(film_end / 24 * SR)

    vo = read(ROOT / "vo/vo_track.wav")[:n] * 10 ** (VO_GAIN_DB / 20)
    vo = np.pad(vo, ((0, n - len(vo)), (0, 0)))  # ffmpeg can end the track a few samples short
    music = np.zeros((n, 2))
    m = read(ROOT / align.get("music", "music/music_C0.wav"))
    k0 = round(offset * SR)
    music[k0:k0 + len(m)] = m[: n - k0]
    music *= 10 ** (BED_DB / 20)
    # tail: the score is already fading; close it over the last 3 s
    fade = round(3 * SR)
    music[-fade:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, fade)))[:, None]

    # complementary three-band split (zero-phase, sums back exactly)
    lo = sosfiltfilt(butter(4, 250, "low", fs=SR, output="sos"), music, axis=0)
    hi = sosfiltfilt(butter(4, 5000, "high", fs=SR, output="sos"), music, axis=0)
    mid = music - lo - hi

    # how much the score competes with the voice in the speech band, line by line
    mid_db = level_db(mid, round(0.4 * SR))
    t = np.arange(n) / SR
    act = np.zeros(n)
    want = np.zeros(n)
    ease = lambda u: 0.5 - 0.5 * np.cos(np.pi * np.clip(u, 0, 1))
    for f0, ln in rows:
        a, b = f0 / 24, (f0 + ln) / 24
        i0, i1 = max(0, int((a - ATT) * SR)), min(n, int((b + REL) * SR))
        seg = t[i0:i1]
        env = np.where(seg < a, ease((seg - (a - ATT)) / ATT), np.where(seg <= b, 1.0, 1 - ease((seg - b) / REL)))
        voice_db = level_db(vo[int(a * SR):int(b * SR)], SR // 10)
        voice_db = np.percentile(voice_db, 75)  # speaking level of this line
        act[i0:i1] = np.maximum(act[i0:i1], env)
        want[i0:i1] = np.maximum(want[i0:i1], env * np.clip(mid_db[i0:i1] - (voice_db - CLEAR), 0, MAX_DIP))
    # the dip itself moves slowly: never pump on single notes
    sm = round(0.35 * SR)
    dip = np.convolve(want, np.ones(sm) / sm, "same")
    g_mid = 10 ** (-dip / 20)
    g_all = 10 ** (-0.2 * dip / 20)  # whole score eases by a fifth of the speech-band dip (max ~0.9 dB)
    score = (lo + hi + mid * g_mid[:, None]) * g_all[:, None]

    mix = score + vo
    write(ROOT / "vo/mix_v2.wav", mix)
    spoken = act > 0.99
    print(f"film {n / SR:.1f} s, score at {offset:.1f} s; speech-band dip under lines: "
          f"mean {dip[spoken].mean():.2f} dB, 90% {np.percentile(dip[spoken], 90):.2f} dB, max {dip.max():.2f} dB; "
          f"lines with no dip {np.mean(dip[spoken] < 0.3) * 100:.0f}% of spoken time")
    np.save(ROOT / "vo/dip_db.npy", dip[:: SR // 100].astype(np.float32))


if __name__ == "__main__":
    main()
