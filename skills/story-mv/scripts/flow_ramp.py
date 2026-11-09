#!/usr/bin/env python3
"""Retime one shot as a step print with its own speed curve. Each output image holds for --hold frames; between
steps the source position advances by the next increment. A position between two source frames is drawn as an
optical-flow in-between (OpenCV DIS), so a speed ramp changes speed gradually.

usage:
  flow_ramp.py IN.mp4 OUT_DIR --start 14 --steps "4*4,3*3,2*28,1.8,1.6,1.4,1.2,1*23" [--hold 2] [--tail 1] [--sheet SHEET.jpg]

OUT_DIR receives 0001.png, 0002.png ... at the input size. The first step shows source frame --start; each
further step moves on by the next increment of --steps ("2*28" means 28 steps of 2). N increments give N + 1
positions; the last one is shown for --tail frames. The example is the HONG KONG shot V3: a slow start skipped
at four frames a step, real speed, a four-step ease and half speed, 125 frames from 14 to 124.
--sheet writes a contact sheet of every in-between with its source position, to check at full size.

Rules from the HONG KONG film (references/repairs.md):
- Ease a speed change over three or four steps (1.8, 1.6, 1.4, 1.2). Swapping whole frames 2, 1, 2, 1 reads
  as a long-short stutter.
- In-betweens are safe when neighbouring frames move little. Fast action, or a clip with duplicated frames
  inside a fast move, gives half-transparent single frames: leave those as they are.
Needs numpy, opencv-python and ffmpeg on PATH.
"""
import argparse
import os
import subprocess
import sys

import numpy as np
import cv2


def parse_steps(text):
    out = []
    for part in text.replace(' ', '').split(','):
        if not part:
            continue
        if '*' in part:
            v, k = part.split('*')
            out += [float(v)] * int(k)
        else:
            out.append(float(part))
    if not out or any(v <= 0 for v in out):
        raise ValueError('steps must be positive numbers')
    return out


def positions(start, steps, hold, tail=None):
    """Source position of every output frame. N increments give N + 1 positions: the first N hold for `hold`
    frames each, the last one for `tail` frames (default `hold`)."""
    pts = [float(start)]
    for v in steps:
        pts.append(pts[-1] + v)
    out = []
    for q in pts[:-1]:
        out += [q] * hold
    return out + [pts[-1]] * (hold if tail is None else tail)


def read_frames(path):
    w, h = map(int, subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                             'stream=width,height', '-of', 'csv=p=0', path]).decode().strip().split(',')[:2])
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-vf',
                          'scale=in_color_matrix=bt709:in_range=tv:out_range=pc,format=bgr24',
                          '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE, check=True).stdout
    n = len(raw) // (w * h * 3)
    return [np.frombuffer(raw, np.uint8, w * h * 3, i * w * h * 3).reshape(h, w, 3) for i in range(n)]


class Inbetween:
    def __init__(self, frames):
        self.A = frames
        h, w = frames[0].shape[:2]
        self.h, self.w = h, w
        self.dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
        self.gx, self.gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
        self.cache = {}

    def half(self, x):
        return cv2.cvtColor(cv2.resize(x, (self.w // 2, self.h // 2), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)

    def up(self, f):
        return cv2.resize(cv2.GaussianBlur(f, (0, 0), 2), (self.w, self.h), interpolation=cv2.INTER_LINEAR) * 2

    def __call__(self, x):
        i = int(np.floor(x + 1e-6))
        t = x - i
        if t < 1e-3 or i + 1 >= len(self.A):
            return self.A[min(i, len(self.A) - 1)]
        if x not in self.cache:
            I0, I1 = self.A[i], self.A[i + 1]
            G0, G1 = self.half(I0), self.half(I1)
            F01, F10 = self.up(self.dis.calc(G0, G1, None)), self.up(self.dis.calc(G1, G0, None))
            a = cv2.remap(I0, self.gx - t * F01[..., 0], self.gy - t * F01[..., 1], cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            b = cv2.remap(I1, self.gx - (1 - t) * F10[..., 0], self.gy - (1 - t) * F10[..., 1], cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            self.cache[x] = np.clip(a.astype(np.float32) * (1 - t) + b.astype(np.float32) * t + .5, 0, 255).astype(np.uint8)
        return self.cache[x]


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('input')
    p.add_argument('out_dir')
    p.add_argument('--start', type=float, default=0, help='source frame of the first step')
    p.add_argument('--steps', required=True)
    p.add_argument('--hold', type=int, default=2, help='output frames per step (2 = 12 fps at 24)')
    p.add_argument('--tail', type=int, help='frames for the last position (default: --hold)')
    p.add_argument('--sheet')
    a = p.parse_args(argv)
    frames = read_frames(a.input)
    pos = positions(a.start, parse_steps(a.steps), a.hold, a.tail)
    if pos[-1] > len(frames) - 1 + 1e-6:
        raise ValueError(f'the plan reaches source frame {pos[-1]:.2f}, the clip has {len(frames)} frames (last index {len(frames) - 1})')
    ib = Inbetween(frames)
    print('source position of each step:', ' '.join(f'{v:.2f}' for v in pos[::a.hold]))
    if a.sheet:
        mids = sorted({v for v in pos if abs(v - round(v)) > 1e-3})
        tiles = []
        for v in mids:
            t = ib(v).copy()
            cv2.putText(t, f'src {v:.2f}', (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
            tiles.append(cv2.resize(t, (640, int(640 * t.shape[0] / t.shape[1])), interpolation=cv2.INTER_AREA))
        if tiles:
            blank = np.zeros_like(tiles[0])
            rows = [np.hstack(tiles[r:r + 3] + [blank] * (3 - len(tiles[r:r + 3]))) for r in range(0, len(tiles), 3)]
            cv2.imwrite(a.sheet, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 90])
            print('sheet', a.sheet, len(tiles), 'in-betweens')
    os.makedirs(a.out_dir, exist_ok=True)
    for k, v in enumerate(pos):
        cv2.imwrite(os.path.join(a.out_dir, f'{k + 1:04d}.png'), ib(v), [cv2.IMWRITE_PNG_COMPRESSION, 1])
    print(f'wrote {len(pos)} frames to {a.out_dir}')
    return pos


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as err:
        print('flow_ramp:', err, file=sys.stderr)
        sys.exit(1)
