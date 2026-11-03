"""Per-line speech recognition check: does each narration line survive the mix?

Usage: qa_asr.py --script script.txt --vo-js render/src/vo.js dry.wav mix.wav
script.txt: one narration line per line (the exact text sent to TTS). The wavs are cut per line at the frames in
vo.js and transcribed with Whisper; the character error rate is printed for both, and lines where the mix is
clearly worse than the dry voice are marked "<<" (the score is masking them: lower the bed or raise the dip there).
Convert inputs first: ffmpeg -i mix.wav -ac 1 -ar 16000 mix16.wav (mlx_whisper wants 16 kHz mono).
Needs (Apple silicon): pip install mlx-whisper soundfile opencc-python-reimplemented cn2an
Homophones (e.g. 枕河 heard as 整合) are recognition limits, not TTS errors: check those by ear and by pitch.
"""
import argparse
import re

import numpy as np
import soundfile as sf


def norm_zh(s):
    try:
        import opencc
        s = opencc.OpenCC("t2s").convert(s)
    except ImportError:
        pass
    try:
        import cn2an
        s = cn2an.transform(s, "an2cn")
    except Exception:
        pass
    return re.sub(r"[^一-鿿]", "", s)


def cer(a, b):
    d = np.arange(len(b) + 1)
    for i, ca in enumerate(a, 1):
        nd = d.copy()
        nd[0] = i
        for j, cb in enumerate(b, 1):
            nd[j] = min(d[j] + 1, nd[j - 1] + 1, d[j - 1] + (ca != cb))
        d = nd
    return d[-1] / max(1, len(a))


def main():
    import mlx_whisper
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True)
    ap.add_argument("--vo-js", required=True)
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--model", default="mlx-community/whisper-large-v3-turbo")
    ap.add_argument("--language", default="zh")
    ap.add_argument("wavs", nargs=2, help="dry voice track, final mix")
    a = ap.parse_args()
    script = [norm_zh(l) for l in open(a.script).read().split("\n") if l.strip()]
    rows = [tuple(map(int, m)) for m in re.findall(r"\[(\d+), (\d+), \d+, \d+\]", open(a.vo_js).read())]
    res, txt = {}, {}
    for fn in a.wavs:
        x, sr = sf.read(fn)
        res[fn], txt[fn] = [], []
        for k, (f0, n) in enumerate(rows):
            clip = x[int((f0 / a.fps - 0.15) * sr):int(((f0 + n) / a.fps + 0.25) * sr)].astype(np.float32)
            t = mlx_whisper.transcribe(clip, path_or_hf_repo=a.model, language=a.language,
                                       condition_on_previous_text=False)["text"]
            res[fn].append(cer(script[k], norm_zh(t)))
            txt[fn].append(t)
    dry, mix = a.wavs
    for k in range(len(rows)):
        flag = " <<" if res[mix][k] - res[dry][k] > 0.06 else ""
        print(f"{k:2d} {res[dry][k]:5.2f} {res[mix][k]:5.2f}{flag}  {txt[dry][k][:30]}" + (f" | {txt[mix][k][:30]}" if flag else ""))
    print(f"mean CER  dry {np.mean(res[dry]):.3f}  mix {np.mean(res[mix]):.3f}")


if __name__ == "__main__":
    main()
