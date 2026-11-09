#!/usr/bin/env python3
"""Beat grid helpers for an edit that lands on the music.

  estimate SONG.wav [--min-bpm 60] [--max-bpm 180]
      Tempo and first-beat estimate from the onset envelope. Check it against the song: half and double
      tempo are printed too, because an onset envelope cannot always tell them apart.
  phase SONG.wav --bpm 69 --first 0.055 [--window 10]
      Where the song's accents sit against that grid, window by window, and the audio delay that puts
      them on it. On HONG KONG an uncalibrated detector put the accents about 50 ms ahead of the cuts,
      so the whole track was delayed by 48 ms and no cut moved. Calibrated, they sit 10 to 15 ms ahead,
      which leaves that film's audio about 35 ms behind its cuts.
  snap BOARD.json --bpm 69 --first 0.055 [--fps 24] [--div 1] [--min-frames 12] [--out SNAPPED.json]
      Moves every shot boundary to the nearest grid line (div 2 = half beats), rounds it to a frame and
      reports each shot's length in frames. BOARD.json is {"shots": [{"id", "start", "end"}, ...]} in seconds.

estimate and phase need numpy and ffmpeg on PATH; snap uses the standard library only.
"""
import argparse
import json
import subprocess
import sys

SR, HOP, WIN = 22050, 128, 1024
LAG = 0.78                 # share of the window between a frame's start and where a hit inside it peaks


def load_audio(path):
    import numpy as np
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         stdout=subprocess.PIPE, check=True).stdout
    return np.frombuffer(raw, np.float32)


def onset_envelope(x):
    """Log spectral flux, with the slow level taken out. Returns (envelope, time of each value in seconds)."""
    import numpy as np
    n = max(0, (len(x) - WIN) // HOP)
    if n < 2:
        raise ValueError('audio is too short')
    win = np.hanning(WIN).astype(np.float32)
    flux = np.empty(n - 1, np.float32)
    prev = None
    for i0 in range(0, n, 4096):            # in blocks, so a long song stays small in memory
        idx = np.arange(WIN)[None, :] + HOP * np.arange(i0, min(n, i0 + 4096))[:, None]
        L = np.log1p(np.abs(np.fft.rfft(x[idx] * win, axis=1)) * 40).astype(np.float32)
        if prev is not None:
            L = np.vstack([prev[None], L])
        d = np.maximum(L[1:] - L[:-1], 0).mean(1)
        start = i0 - 1 if prev is not None else 0
        flux[start:start + len(d)] = d
        prev = L[-1]
    k = 800                                 # about 4.6 s: removes swells, keeps hits
    flux = flux - np.convolve(flux, np.ones(k, np.float32) / k, 'same')
    flux = np.maximum(flux, 0)
    flux /= flux.std() + 1e-6
    # Each value compares a frame with the one before it, and a hit is strongest as it enters the newer frame.
    # Labelled by the start of that frame, onsets read about 36 ms early (window 1024 at 22.05 kHz); measured on
    # synthetic clicks, 0.78 of the window puts the peak within a few ms of the true onset.
    t = ((np.arange(len(flux)) + 1) * HOP + LAG * WIN) / SR
    return flux, t


def fold(env, t, beats, phases, spread=3):
    """Mean envelope at beats + phase, for every phase; spread widens each probe by a few envelope steps."""
    import numpy as np
    out = []
    for p in phases:
        ii = np.searchsorted(t, beats + p)
        ii = ii[ii < len(env)]
        if not len(ii):
            out.append(0.0)
            continue
        v = sum(env[np.clip(ii + k, 0, len(env) - 1)] for k in range(-spread, spread + 1))
        out.append(float(v.mean()))
    return np.array(out)


def cmd_estimate(a):
    import numpy as np
    env, t = onset_envelope(load_audio(a.song))
    step = HOP / SR
    lags = np.arange(int(60 / a.max_bpm / step), int(60 / a.min_bpm / step) + 1)
    e = env - env.mean()
    ac = np.array([np.dot(e[:-l], e[l:]) / (len(e) - l) for l in lags])
    order = np.argsort(ac)[::-1]
    picks = []
    for i in order:
        bpm = 60 / (lags[i] * step)
        if all(abs(bpm - q) / q > 0.03 for q, _ in picks):
            picks.append((bpm, ac[i]))
        if len(picks) == 3:
            break
    bpm = picks[0][0]
    # refine: the fold sharpness peaks at the true period
    best = (0, bpm, 0.0)
    for b in np.arange(bpm * 0.99, bpm * 1.01, bpm * 0.0005):
        per = 60 / b
        beats = np.arange(0, t[-1], per)
        ph = np.arange(0, per, 0.005)
        f = fold(env, t, beats, ph, 1)
        if f.max() > best[0]:
            best = (f.max(), b, ph[f.argmax()])
    _, bpm, first = best
    print(f'tempo {bpm:.2f} BPM, beat period {60 / bpm:.4f} s, first beat at {first:.3f} s')
    print('other candidates:', ', '.join(f'{b:.2f}' for b, _ in picks[1:]), '(also try half and double tempo)')
    return bpm, first


def grid(bpm, first, end, div=1):
    per = 60.0 / bpm / div
    k0 = -int(first // per) if first > 0 else 0
    out, k = [], k0
    while first + k * per <= end + per:
        out.append(first + k * per)
        k += 1
    return out


def cmd_phase(a):
    import numpy as np
    env, t = onset_envelope(load_audio(a.song))
    per = 60.0 / a.bpm
    beats = np.array(grid(a.bpm, a.first, t[-1]))
    ph = np.arange(-per / 2, per / 2, 0.005)
    print(f'grid period {per:.4f} s, first beat {a.first:.3f} s')
    print('window       accent phase  sharpness')
    for w0 in np.arange(0, t[-1], a.window):
        b = beats[(beats >= w0) & (beats < w0 + a.window)]
        if len(b) < 2:
            continue
        f = fold(env, t, b, ph)
        print(f'{w0:6.1f}-{w0 + a.window:6.1f}  {ph[f.argmax()]:+.3f} s      {f.max() / (f.mean() + 1e-6):.2f}')
    f = fold(env, t, beats, ph)
    p = float(ph[f.argmax()])
    print(f'whole song: accents sit {p:+.3f} s from the grid (sharpness {f.max() / (f.mean() + 1e-6):.2f})')
    if p < 0:
        print(f'they come early: delay the audio by {-p * 1000:.0f} ms (ffmpeg adelay={-p * 1000:.0f}:all=1) and keep the cuts')
    elif p > 0:
        print(f'they come late: move the grid {p * 1000:.0f} ms later, or trim that much from the start of the audio')
    return p


def cmd_snap(a):
    with open(a.board, encoding='utf-8') as fh:
        board = json.load(fh)
    shots = board['shots'] if isinstance(board, dict) else board
    if not shots:
        raise SystemExit('no shots')
    end = max(s['end'] for s in shots)
    lines = grid(a.bpm, a.first, end, a.div)
    def near(x):
        return min(lines, key=lambda g: abs(g - x))
    bounds = [shots[0]['start']] + [s['end'] for s in shots]
    snapped = [bounds[0]] + [near(x) for x in bounds[1:]]
    frames = [round(x * a.fps) for x in snapped]
    out, worst = [], 0.0
    print(f'{"shot":8} {"start":>8} {"end":>8} {"frames":>6}  moved')
    for i, s in enumerate(shots):
        f0, f1 = frames[i], frames[i + 1]
        moved = snapped[i + 1] - bounds[i + 1]
        worst = max(worst, abs(moved))
        flag = ''
        if f1 - f0 < a.min_frames:
            flag = f'  SHORT (< {a.min_frames} frames)'
        if f1 <= f0:
            flag = '  EMPTY: two boundaries snapped to one grid line'
        print(f'{s.get("id", i)!s:8} {f0 / a.fps:8.3f} {f1 / a.fps:8.3f} {f1 - f0:6d}  {moved:+.3f} s{flag}')
        row = dict(s, start=round(f0 / a.fps, 5), end=round(f1 / a.fps, 5), frames=f1 - f0)
        out.append(row)
    print(f'{len(shots)} shots, {frames[-1] - frames[0]} frames, largest move {worst:.3f} s')
    if a.out:
        res = dict(board, shots=out) if isinstance(board, dict) else out
        with open(a.out, 'w', encoding='utf-8') as fh:
            json.dump(res, fh, ensure_ascii=False, indent=1)
        print('wrote', a.out)
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)
    e = sub.add_parser('estimate')
    e.add_argument('song')
    e.add_argument('--min-bpm', type=float, default=60)
    e.add_argument('--max-bpm', type=float, default=180)
    f = sub.add_parser('phase')
    f.add_argument('song')
    f.add_argument('--bpm', type=float, required=True)
    f.add_argument('--first', type=float, required=True, help='time of the first beat, seconds')
    f.add_argument('--window', type=float, default=10)
    s = sub.add_parser('snap')
    s.add_argument('board')
    s.add_argument('--bpm', type=float, required=True)
    s.add_argument('--first', type=float, required=True)
    s.add_argument('--fps', type=float, default=24)
    s.add_argument('--div', type=int, default=1, help='grid lines per beat: 1 beats, 2 half beats')
    s.add_argument('--min-frames', type=int, default=12)
    s.add_argument('--out')
    a = p.parse_args(argv)
    return {'estimate': cmd_estimate, 'phase': cmd_phase, 'snap': cmd_snap}[a.cmd](a)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as err:
        print('beat_grid:', err, file=sys.stderr)
        sys.exit(1)
