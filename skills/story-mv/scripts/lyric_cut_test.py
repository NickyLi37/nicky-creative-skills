#!/usr/bin/env python3
"""Find where a sung word really starts: the cut test.

usage: lyric_cut_test.py AUDIO.wav LINE.txt --word K --near T [--lang en] [--span -1.4 1.0] [--step 0.1]
                         [--end E] [--model mlx-community/whisper-large-v3-mlx]

LINE.txt holds one lyric line. It is read at run time and never printed, so the agent running this never
reads or repeats the lyric. Words are counted from 0; for Chinese each character is one unit.

For each start point s = T + d, the audio from s to --end goes to Whisper with the line's units from K on
forced as the transcript. The mean probability of unit K stays up while s is before the word and collapses for
good once s passes its onset. In the HONG KONG film the collapse sat about 0.03 s after the sung onset; on the
synthetic speech of the test it sits 0.1 to 0.2 s after. So the script prints the collapse and then the
strongest audio onset just before it, which is the time to use. Listen to the result when you can: the user
can hear what the numbers cannot.

Why: word times from Whisper's DTW alignment let the first word after a pause absorb the pause. On HONG KONG
the first words of English lines lit 0.93 s early on average (3.1 s at worst), mid-line words about 0.2 s.
The numbers looked right on a layout sheet; the user saw the fault while watching with the song.
Whisper may not hear some sung Chinese at all (every unit at the probability floor). Time those from the
onsets that repeats of the same hook share, found by audio cross-correlation, and the bar grid, and say so.

Use a vocal stem when you have one; HONG KONG used the centre channel of the mix. Requires Apple silicon with
mlx-whisper (pip install mlx-whisper); the model downloads on first use. numpy and ffmpeg too.
"""
import argparse
import re
import sys
import unicodedata

import numpy as np

CJK = '一-鿿㐀-䶿'


def units(line):
    line = ''.join(c for c in line if unicodedata.category(c)[0] != 'C')
    if re.search(f'[{CJK}]', line):
        return [c for c in line if re.match(f'[{CJK}]', c)], True
    return [re.sub(r"^[^\w']+|[^\w']+$", '', w) for w in line.split() if re.sub(r"[^\w']", '', w)], False


def onsets(x, sr):
    """Onset times (s) from the spectral flux of the audio, strongest local peaks only. Labels are calibrated the
    same way as beat_grid.py: a hit peaks about 0.78 of a window after the start of the frame it enters."""
    hop, win = 80, 512
    n = (len(x) - win) // hop
    if n < 3:
        return np.array([]), np.array([])
    idx = np.arange(win)[None, :] + hop * np.arange(n)[:, None]
    L = np.log1p(np.abs(np.fft.rfft(x[idx] * np.hanning(win), axis=1)) * 40)
    flux = np.maximum(L[1:] - L[:-1], 0).mean(1)
    flux = flux / (flux.std() + 1e-9)
    pk = [i for i in range(1, len(flux) - 1) if flux[i] >= flux[i - 1] and flux[i] > flux[i + 1] and flux[i] > 1.5]
    return ((np.array(pk) + 1) * hop + 0.78 * win) / sr, (flux[pk] if pk else np.array([]))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('audio')
    p.add_argument('line')
    p.add_argument('--word', type=int, required=True, help='index of the word (or character) in the line, from 0')
    p.add_argument('--near', type=float, required=True, help='rough time of the word, seconds (an aligner gives one)')
    p.add_argument('--lang', default='en')
    p.add_argument('--span', type=float, nargs=2, default=(-1.4, 1.0))
    p.add_argument('--step', type=float, default=0.1)
    p.add_argument('--end', type=float, help='end of the audio window (default: 8 s after the word)')
    p.add_argument('--model', default='mlx-community/whisper-large-v3-mlx')
    a = p.parse_args(argv)

    import mlx.core as mx
    from mlx_whisper.load_models import load_model
    from mlx_whisper.tokenizer import get_tokenizer
    from mlx_whisper.audio import load_audio, log_mel_spectrogram, pad_or_trim, N_FRAMES, N_SAMPLES, SAMPLE_RATE

    with open(a.line, encoding='utf-8') as fh:
        U, zh = units(fh.read().strip())
    if not 0 <= a.word < len(U):
        raise ValueError(f'the line has {len(U)} units; --word must be 0..{len(U) - 1}')
    model = load_model(a.model, dtype=mx.float16)
    tok = get_tokenizer(model.is_multilingual, num_languages=model.num_languages, language=a.lang, task='transcribe')
    A = load_audio(a.audio)
    end = a.end if a.end is not None else a.near + 8.0
    G = [tok.encode(w if zh else ' ' + w) for w in U[a.word:a.word + 4]]
    tt = [t for g in G for t in g]
    n0 = len(G[0])

    def prob(s):
        s = max(0.0, s)
        x = A[int(s * SAMPLE_RATE):int(min(end, s + 30) * SAMPLE_RATE)]
        mel = pad_or_trim(log_mel_spectrogram(x, n_mels=model.dims.n_mels, padding=N_SAMPLES), N_FRAMES, axis=-2).astype(mx.float16)
        tokens = mx.array([*tok.sot_sequence, tok.no_timestamps, *tt])
        lg = model.logits(tokens[None], model.embed_audio(mel[None]))[0][len(tok.sot_sequence):-1, :tok.eot].astype(mx.float32)
        lp = np.array(lg - mx.logsumexp(lg, axis=-1, keepdims=True))
        return float(np.exp(np.mean([lp[j, tt[j]] for j in range(n0)])))

    ds = np.round(np.arange(a.span[0], a.span[1] + 1e-9, a.step), 3)
    ps = np.array([prob(a.near + d) for d in ds])
    print('start offset : probability of the word')
    print(' '.join(f'{d:+.1f}:{q:.2f}' for d, q in zip(ds, ps)))
    m = float(ps.max())
    if m < 0.15:
        print('the word is barely heard anywhere in the span (common for sung Chinese): time it another way')
        return None
    keep = [i for i in range(len(ps) - 1) if ps[i] >= 0.5 * m and (ps[i + 1:] < 0.3 * m).all()]
    if not keep:
        print('no lasting collapse in the span: widen --span, or move --near')
        return None
    lo, hi = a.near + ds[keep[-1]], a.near + ds[keep[-1] + 1]      # the word is still heard from lo, gone from hi on
    guess = (lo + hi) / 2 - 0.03
    t_on, s_on = onsets(np.array(A, dtype=np.float32), SAMPLE_RATE)
    w = (t_on > lo - 0.15) & (t_on < hi + 0.02)
    snapped = float(t_on[w][np.argmax(s_on[w])]) if w.any() else None
    print(f'heard from a start at {lo:.2f} s, gone from {hi:.2f} s; onset estimate {guess:.2f} s'
          + (f'; strongest audio onset before the collapse {snapped:.3f} s' if snapped is not None else '; no audio onset nearby'))
    return snapped if snapped is not None else guess


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError) as err:
        print('lyric_cut_test:', err, file=sys.stderr)
        sys.exit(1)
