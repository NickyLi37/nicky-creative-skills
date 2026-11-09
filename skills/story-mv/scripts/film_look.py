#!/usr/bin/env python3
"""Film finish for AI clips: grade, bloom and red halation, grain, soft filter, gate flicker, a small handheld
drift, 12 fps step print and a logo. The defaults are the HONG KONG recipe (1990s Hong Kong night film:
low key, green shadows, yellow-green highlights, red halation round the lights).

usage:
  film_look.py IN.mp4 OUT.mov [--spec SPEC.json] [--from F] [--to F] [--grain 1.0] [--diffuse 0]
               [--edge-soft 0] [--flicker 0] [--hand 0] [--step none|blend|hold] [--no-grade]
               [--logo LOGO.png] [--logo-w .09] [--logo-x .022] [--logo-y .03] [--logo-alpha .9] [--crf N]

Output is ProRes 422 HQ in a .mov unless --crf is given (then H.264 yuv420p). BT.709 in and out: convert
untagged or BT.601 clips first (see references/look-and-finish.md).

Every random value is seeded by the frame number, so --from/--to chunks rendered in parallel join into
exactly the film a single run makes. --from/--to are frame indices of IN, --to exclusive.

SPEC.json sets the look per shot. All keys are optional:
  {"fps": 24, "shots": [{"id": "B5", "start": 0.0, "end": 3.48}, ...],   seconds, edit order
   "step": ["B5"],          12 fps step print, each pair of frames blended (crowds, slow drifts)
   "step_hold": ["R5"],     12 fps step print, one frame held for two, no blend (anything that moves fast)
   "grain": {"C1": 1.4}, "grain_all": 1.2, "hand": {"R1": 0}, "hand_default": 3.0,
   "diffuse": {"R8": 0.3}, "diffuse_all": 0.1, "edge_soft": 0.22, "flicker": 0.004}
Command-line values replace the *_all, hand_default, edge_soft and flicker entries.
Needs numpy, opencv-python and ffmpeg/ffprobe on PATH.
"""
import argparse
import json
import math
import subprocess
import sys

import numpy as np
import cv2

LUM = np.array([0.2126, 0.7152, 0.0722], np.float32)


def probe(path):
    """Width, height, fps and frame count. The container's count is used when it has one; otherwise frames are counted."""
    q = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-of', 'json']
    s = json.loads(subprocess.check_output(q + ['-show_entries', 'stream=width,height,r_frame_rate,nb_frames', path]))['streams'][0]
    num, den = map(int, s['r_frame_rate'].split('/'))
    n = s.get('nb_frames')
    if not str(n).isdigit():
        n = json.loads(subprocess.check_output(q + ['-count_frames', '-show_entries', 'stream=nb_read_frames', path]))['streams'][0]['nb_read_frames']
    return int(s['width']), int(s['height']), num / den, int(n)


class Look:
    """Grade, bloom, halation, softness, vignette and grain at any size; sizes scale from a 1920-wide frame."""
    def __init__(self, W, H, grade=True, seed=11):
        self.W, self.H, self.grade = W, H, grade
        self.k = k = W / 1920.0
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 * 0.9 + ((yy - H / 2) / (H / 2)) ** 2 * 0.7)
        self.vig = (1 - 0.16 * np.clip(r - 0.6, 0, 1) ** 1.6)[..., None].astype(np.float32)
        self.edge = (np.clip((r - 0.55) / 0.6, 0, 1) ** 1.5)[..., None].astype(np.float32)
        rng = np.random.default_rng(seed)
        P = 96                                       # plates are a little larger than the frame and cropped at random
        self.pl = np.empty((12, H + P, W + P), np.float16)
        for i in range(12):
            g = cv2.GaussianBlur(rng.standard_normal((H + P, W + P), dtype=np.float32), (0, 0), 0.75 * k)
            self.pl[i] = g / g.std()
        self.pc = np.empty((5, H + P, W + P, 3), np.float16)
        for i in range(5):
            g = cv2.GaussianBlur(rng.standard_normal((H + P, W + P, 3), dtype=np.float32), (0, 0), 1.1 * k)
            self.pc[i] = g / g.std()

    def __call__(self, x, f, gmul=1.0):
        W, H, k = self.W, self.H, self.k
        y = np.clip(x, 0, 1)
        if self.grade:
            y = y * y * (3 - 2 * y) * 0.28 + y * 0.72                       # a gentle S-curve
            l = (y @ LUM)[..., None]
            sh = np.clip(1 - l / 0.42, 0, 1) ** 1.5
            hi = np.clip((l - 0.55) / 0.45, 0, 1)
            y = y * (1 + sh * (np.array([0.96, 1.02, 0.88], np.float32) - 1)    # shadows towards green
                     + hi * (np.array([0.99, 1.005, 0.94], np.float32) - 1))  # highlights towards yellow-green
            l2 = (y @ LUM)[..., None]
            y = l2 + (y - l2) * 1.06
            small = cv2.resize(x, (max(1, W // 4), max(1, H // 4)), interpolation=cv2.INTER_AREA)
            src = np.clip(small - 0.62, 0, 1) / 0.38                       # only the lights bloom
            bloom = cv2.resize(cv2.GaussianBlur(src, (0, 0), 26 * k / 4), (W, H), interpolation=cv2.INTER_LINEAR)
            hal = cv2.resize(cv2.GaussianBlur(src, (0, 0), 11 * k / 4), (W, H), interpolation=cv2.INTER_LINEAR)
            y = 1 - (1 - np.clip(y, 0, 1)) * (1 - 0.20 * bloom)
            y[..., 0] += 0.14 * hal[..., 0] + 0.05 * hal[..., 1]               # red halation round neon and tail-lights
            y[..., 1] += 0.035 * hal[..., 1]
            y = cv2.addWeighted(y, 0.8, cv2.GaussianBlur(y, (0, 0), 0.8 * k), 0.2, 0)
            y = y * self.vig
        rng = np.random.default_rng(f * 7 + 3)
        i, j = rng.integers(0, len(self.pl)), rng.integers(0, len(self.pc))
        ox, oy = rng.integers(0, 96), rng.integers(0, 96)
        g = self.pl[i, oy:oy + H, ox:ox + W].astype(np.float32)[..., None] * 0.8
        g = g + self.pc[j, oy:oy + H, ox:ox + W].astype(np.float32) * 0.25
        lum = (np.clip(y, 0, 1) @ LUM)[..., None]
        amp = (0.008 + 0.011 * (1 - np.abs(lum * 2 - 0.9).clip(0, 1))) * gmul   # most grain in the mid-tones
        return np.clip(y + g * amp, 0, 1)


def hand_path(f, fps, sid, amp):
    """A very small drift, seeded per shot, slow enough to read as someone breathing behind the camera."""
    s = sum(map(ord, str(sid))) * 0.37
    t = f / fps
    dx = amp * (math.sin(t * 2.1 + s) * 0.6 + math.sin(t * 5.3 + s * 1.7) * 0.28 + math.sin(t * 11.0 + s * 2.3) * 0.12)
    dy = amp * (math.sin(t * 1.7 + s * 1.3) * 0.6 + math.sin(t * 4.7 + s * 0.7) * 0.28 + math.sin(t * 9.0 + s * 1.9) * 0.12)
    return dx, dy


def load_logo(path, W, H, w, x, y, alpha):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None:
        raise ValueError(f'cannot read logo {path}')
    if im.shape[2] == 3:
        im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
    lw = int(W * w)
    lh = int(im.shape[0] * lw / im.shape[1])
    im = cv2.resize(im, (lw, lh), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    return np.ascontiguousarray(im[..., 2::-1]), im[..., 3:4] * alpha, int(W * x), int(H * y)


class Shots:
    def __init__(self, spec, fps, n):
        rows = spec.get('shots') or [{'id': 'ALL', 'start': 0, 'end': n / fps}]
        self.rows = [(round(r['start'] * fps), round(r['end'] * fps), r['id']) for r in rows]

    def at(self, f):
        for a, b, sid in self.rows:
            if f < b:                      # the same rounding the cut uses, or a boundary frame lands in the wrong shot
                return a, b, sid
        return self.rows[-1]


def render(a):
    W, H, fps, n = probe(a.input)
    spec = {}
    if a.spec:
        with open(a.spec, encoding='utf-8') as fh:
            spec = json.load(fh)
    fps = spec.get('fps', fps)
    f0, f1 = a.start, min(a.end if a.end is not None else n, n)
    if not 0 <= f0 < f1:
        raise ValueError(f'empty frame range {f0}..{f1} of {n}')
    shots = Shots(spec, fps, n)
    step_blend = set(spec.get('step', []))
    step_hold = set(spec.get('step_hold', []))
    if a.step == 'blend':
        step_blend |= {r[2] for r in shots.rows}
    elif a.step == 'hold':
        step_hold |= {r[2] for r in shots.rows}
    grain = spec.get('grain', {})
    grain_all = a.grain if a.grain is not None else spec.get('grain_all', 1.0)
    hand = spec.get('hand', {})
    hand_default = a.hand if a.hand is not None else spec.get('hand_default', 0.0)
    diffuse = spec.get('diffuse', {})
    diffuse_all = a.diffuse if a.diffuse is not None else spec.get('diffuse_all', 0.0)
    edge_soft = a.edge_soft if a.edge_soft is not None else spec.get('edge_soft', 0.0)
    flicker = a.flicker if a.flicker is not None else spec.get('flicker', 0.0)
    look = Look(W, H, grade=not a.no_grade)
    logo = load_logo(a.logo, W, H, a.logo_w, a.logo_x, a.logo_y, a.logo_alpha) if a.logo else None

    a0 = max(0, f0 - 1)                      # a step pair can start one frame before the range
    rd = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{a0 / fps:.5f}', '-i', a.input,
                           '-vf', 'scale=in_color_matrix=bt709:in_range=tv:out_range=pc,format=rgb24',
                           '-frames:v', str(f1 - a0 + 1), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                          stdout=subprocess.PIPE, bufsize=W * H * 3)
    if a.crf is None:
        enc = ['-vf', 'scale=in_range=pc:out_color_matrix=bt709:out_range=tv,format=yuv422p10le',
               '-c:v', 'prores_ks', '-profile:v', '3', '-qscale:v', '6']
    else:
        enc = ['-vf', 'scale=in_range=pc:out_color_matrix=bt709:out_range=tv,format=yuv420p',
               '-c:v', 'libx264', '-preset', 'slow', '-crf', str(a.crf), '-movflags', '+faststart']
    wr = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                           '-r', str(fps), '-i', '-', *enc, '-color_primaries', 'bt709', '-color_trc', 'bt709',
                           '-colorspace', 'bt709', a.output], stdin=subprocess.PIPE)
    buf, pos = {}, a0

    def get(i):
        nonlocal pos
        while pos <= i:
            d = rd.stdout.read(W * H * 3)
            if len(d) < W * H * 3:
                break
            buf[pos] = np.frombuffer(d, np.uint8).reshape(H, W, 3)
            pos += 1
        for q in [q for q in buf if q < i - 2]:
            del buf[q]
        return buf.get(i, buf[max(buf)] if buf else None)

    for f in range(f0, f1):
        s0, s1, sid = shots.at(f)
        if sid in step_blend or sid in step_hold:
            m = s0 + ((f - s0) // 2) * 2
            last = s1 - 1                    # an odd frame count: the last frame pairs with itself, never with the next shot
            p = get(m)
            if sid in step_hold:
                x = p.astype(np.float32) / 255
            else:
                q = get(min(m + 1, last, n - 1))
                x = (p.astype(np.float32) + q.astype(np.float32)) * (0.5 / 255)
        else:
            x = get(f).astype(np.float32) / 255
        amp = hand.get(sid, hand_default) * W / 3840             # amplitudes are written in pixels at 4K
        if amp > 0:
            dx, dy = hand_path(f, fps, sid, amp)
            z = 1 + 4.4 * amp / W                                # a hair of zoom hides the moving border
            M = np.array([[z, 0, -(z - 1) * W / 2 + dx], [0, z, -(z - 1) * H / 2 + dy]], np.float32)
            x = cv2.warpAffine(x, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        dv = max(diffuse.get(sid, 0), diffuse_all)
        if dv > 0 or edge_soft > 0:
            sm = cv2.resize(x, (max(1, W // 4), max(1, H // 4)), interpolation=cv2.INTER_AREA)
            sm = cv2.resize(cv2.GaussianBlur(sm, (0, 0), 1.6), (W, H), interpolation=cv2.INTER_LINEAR)
            w_ = dv + edge_soft * look.edge                      # old lenses go soft towards the corners
            x = x * (1 - w_) + sm * w_
        if flicker:
            x = x * (1 + flicker * float(np.random.default_rng(f * 13 + 5).standard_normal()))
        y = look(x, f, grain.get(sid, 1.0) * grain_all)
        if logo:                                                  # after the grade, so the logo stays clean
            lrgb, la, lx, ly = logo
            reg = y[ly:ly + la.shape[0], lx:lx + la.shape[1]]
            reg[:] = reg * (1 - la) + lrgb * la
        wr.stdin.write((y * 255 + 0.5).astype(np.uint8).tobytes())
    wr.stdin.close()
    wr.wait()
    rd.stdout.close()
    rd.kill()
    if wr.returncode:
        raise RuntimeError('ffmpeg could not write the output')
    print(f'wrote {a.output}: frames {f0}..{f1 - 1} of {n}, {W}x{H} at {fps:g} fps')


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('input')
    p.add_argument('output')
    p.add_argument('--spec')
    p.add_argument('--from', dest='start', type=int, default=0)
    p.add_argument('--to', dest='end', type=int)
    p.add_argument('--grain', type=float)
    p.add_argument('--diffuse', type=float)
    p.add_argument('--edge-soft', type=float)
    p.add_argument('--flicker', type=float)
    p.add_argument('--hand', type=float, help='handheld amplitude in pixels at 4K (HONG KONG: 3)')
    p.add_argument('--step', choices=['none', 'blend', 'hold'], default='none', help='12 fps step print for the whole input')
    p.add_argument('--no-grade', action='store_true', help='grain, softness and logo only')
    p.add_argument('--logo')
    p.add_argument('--logo-w', type=float, default=0.09, help='logo width as a share of the frame width')
    p.add_argument('--logo-x', type=float, default=0.022)
    p.add_argument('--logo-y', type=float, default=0.03)
    p.add_argument('--logo-alpha', type=float, default=0.9)
    p.add_argument('--crf', type=int, help='write H.264 at this CRF instead of ProRes')
    render(p.parse_args(argv))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as err:
        print('film_look:', err, file=sys.stderr)
        sys.exit(1)
