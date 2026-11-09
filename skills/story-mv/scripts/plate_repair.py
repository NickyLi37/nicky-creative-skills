#!/usr/bin/env python3
"""Repair a defect in a locked-off shot where the subject does not move, and keep the shot's own rain or snow.

  plate IN.mp4 PLATE.png [--from F0] [--to F1]
      Per-pixel median of the frames: a clean still of the shot with the falling rain taken out.
  apply IN.mp4 OUT --plate PLATE.png --edit EDIT.png --mask MASK.png [--box X,Y,W,H] [--streak 13]
        [--min-channel] [--match 90] [--erode 21] [--soften 7] [--sheet SHEET.jpg]
      Lays the repainted plate into every frame inside the mask and adds back only the frame's own long thin
      bright streaks, found as (frame - plate) opened with a 1 x --streak vertical line.

How the HONG KONG shot R7 was fixed (references/repairs.md): the woman crouches still in the rain while her wet
hair hangs to her forearms and reads as long hair. A 42-frame median gave the plate; GPT Image repainted the head
on a crop of the plate with a mask; this script laid it back and kept the rain. Her hands went the same way with
--min-channel, because rain lights all three channels while the old skin edge lights only red.

EDIT and MASK are either full-frame or the size of --box (the crop that went to the image edit). The edit's
brightness is matched to the plate by a smooth ratio measured just outside the mask (--match is the blur sigma
in pixels, 0 turns it off); near-black pixels keep their value. OUT is a folder of PNGs (0001.png ...), or a
.mov (ProRes 422 HQ) or .mp4 (H.264, CRF 14). Needs numpy, opencv-python and ffmpeg on PATH.
"""
import argparse
import os
import subprocess
import sys

import numpy as np
import cv2


def size_of(path):
    w, h = subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                    'stream=width,height', '-of', 'csv=p=0', path]).decode().strip().split(',')[:2]
    return int(w), int(h)


def frames(path, f0=0, f1=None):
    """BGR frames f0..f1-1 (f1 exclusive) of a video, read in order."""
    w, h = size_of(path)
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', path, '-vf',
                          'scale=in_color_matrix=bt709:in_range=tv:out_range=pc,format=bgr24',
                          '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE, bufsize=w * h * 3)
    i = 0
    try:
        while f1 is None or i < f1:
            d = p.stdout.read(w * h * 3)
            if len(d) < w * h * 3:
                break
            if i >= f0:
                yield np.frombuffer(d, np.uint8).reshape(h, w, 3)
            i += 1
    finally:
        p.stdout.close()
        p.kill()
        p.wait()


def cmd_plate(a):
    A = np.stack(list(frames(a.input, a.start, a.end)))
    if len(A) < 3:
        raise ValueError('a median plate needs at least 3 frames')
    h = A.shape[1]
    med = np.empty(A.shape[1:], np.uint8)
    for y in range(0, h, 64):                  # in strips, so a 4K shot fits in memory
        med[y:y + 64] = np.median(A[:, y:y + 64], axis=0).astype(np.uint8)
    cv2.imwrite(a.output, med)
    print(f'plate {a.output} from {len(A)} frames')


def nconv(v, w, s):
    """Blur of v weighted by w: a smooth fill that only listens to where w is 1."""
    return cv2.GaussianBlur(v * w, (0, 0), s) / np.maximum(cv2.GaussianBlur(w, (0, 0), s), 1e-3)


class Writer:
    def __init__(self, out, w, h, fps):
        self.out, self.i, self.p = out, 0, None
        if out.lower().endswith(('.mov', '.mp4')):
            enc = (['-c:v', 'prores_ks', '-profile:v', '3', '-qscale:v', '6', '-pix_fmt', 'yuv422p10le'] if out.lower().endswith('.mov')
                   else ['-c:v', 'libx264', '-crf', '14', '-preset', 'slow', '-pix_fmt', 'yuv420p', '-movflags', '+faststart'])
            self.p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{w}x{h}',
                                       '-r', str(fps), '-i', '-', '-vf', 'scale=in_range=pc:out_color_matrix=bt709:out_range=tv',
                                       *enc, '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', out],
                                      stdin=subprocess.PIPE)
        else:
            os.makedirs(out, exist_ok=True)

    def write(self, img):
        self.i += 1
        if self.p:
            self.p.stdin.write(img.tobytes())
        else:
            cv2.imwrite(os.path.join(self.out, f'{self.i:04d}.png'), img, [cv2.IMWRITE_PNG_COMPRESSION, 1])

    def close(self):
        if self.p:
            self.p.stdin.close()
            self.p.wait()
            if self.p.returncode:
                raise RuntimeError('ffmpeg could not write ' + self.out)


def cmd_apply(a):
    W, H = size_of(a.input)
    plate = cv2.imread(a.plate)
    if plate is None or plate.shape[:2] != (H, W):
        raise ValueError('the plate must be a still of the same shot at the video size')
    x0, y0, bw, bh = map(int, a.box.split(',')) if a.box else (0, 0, W, H)
    if x0 < 0 or y0 < 0 or x0 + bw > W or y0 + bh > H:
        raise ValueError('the box must lie inside the frame')
    edit = cv2.imread(a.edit)
    mask = cv2.imread(a.mask, cv2.IMREAD_GRAYSCALE)
    if edit is None or mask is None:
        raise ValueError('cannot read the edit or the mask')
    if edit.shape[:2] == (H, W) and a.box:
        edit = edit[y0:y0 + bh, x0:x0 + bw]
    if mask.shape[:2] == (H, W) and a.box:
        mask = mask[y0:y0 + bh, x0:x0 + bw]
    edit = cv2.resize(edit, (bw, bh), interpolation=cv2.INTER_AREA).astype(np.float32)
    mask = cv2.resize(mask, (bw, bh), interpolation=cv2.INTER_AREA)
    crop = plate[y0:y0 + bh, x0:x0 + bw].astype(np.float32)
    new = cv2.GaussianBlur(edit, (0, 0), 0.6)
    if a.match > 0:
        ring = (cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))) == 0).astype(np.float32)
        if ring.sum() < 100:
            raise ValueError('no area outside the mask to match brightness: use a larger box, or --match 0')
        ratio = np.clip(np.dstack([nconv(crop[..., c] + 2, ring, a.match) / nconv(edit[..., c] + 2, ring, a.match) for c in range(3)]), 0.6, 1.6)
        lum = new @ np.array([0.0722, 0.7152, 0.2126], np.float32)
        wl = np.clip((lum - 16) / 22, 0, 1)[..., None]           # black hair stays black
        new = new * (1 + (ratio - 1) * wl)
    M = mask
    if a.erode > 0:
        M = cv2.erode(M, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (a.erode, a.erode)))
    M = M.astype(np.float32) / 255
    if a.soften > 0:
        M = cv2.GaussianBlur(M, (0, 0), a.soften)
    M = M[..., None]
    K = cv2.getStructuringElement(cv2.MORPH_RECT, (1, a.streak))
    fps = float(eval_rate(a.input))
    out = Writer(a.output, W, H, fps)
    picks, n = [], 0
    for fr in frames(a.input):
        o = fr.astype(np.float32)
        r = np.maximum(o[y0:y0 + bh, x0:x0 + bw] - crop, 0)
        if a.min_channel:
            r = cv2.morphologyEx(r.min(2), cv2.MORPH_OPEN, K)[..., None]
        else:
            r = cv2.morphologyEx(r, cv2.MORPH_OPEN, K)
        o[y0:y0 + bh, x0:x0 + bw] = o[y0:y0 + bh, x0:x0 + bw] * (1 - M) + (new + r) * M
        img = np.clip(o + 0.5, 0, 255).astype(np.uint8)
        out.write(img)
        if a.sheet and n in (0, 12):
            picks.append(img[y0:y0 + bh, x0:x0 + bw].copy())
        n += 1
    out.close()
    if a.sheet:
        row = picks + [plate[y0:y0 + bh, x0:x0 + bw], edit.astype(np.uint8)]
        hh = 540
        row = [cv2.resize(t, (int(t.shape[1] * hh / t.shape[0]), hh), interpolation=cv2.INTER_AREA) for t in row]
        cv2.imwrite(a.sheet, np.hstack(row), [cv2.IMWRITE_JPEG_QUALITY, 90])
        print('sheet', a.sheet, '(frame 1, frame 13, plate, edit)')
    print(f'wrote {n} frames to {a.output}')


def eval_rate(path):
    r = subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate',
                                 '-of', 'csv=p=0', path]).decode().strip()
    num, den = r.split('/')
    return int(num) / int(den)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)
    q = sub.add_parser('plate')
    q.add_argument('input')
    q.add_argument('output')
    q.add_argument('--from', dest='start', type=int, default=0)
    q.add_argument('--to', dest='end', type=int)
    r = sub.add_parser('apply')
    r.add_argument('input')
    r.add_argument('output')
    r.add_argument('--plate', required=True)
    r.add_argument('--edit', required=True)
    r.add_argument('--mask', required=True)
    r.add_argument('--box', help='X,Y,W,H of the crop that went to the image edit')
    r.add_argument('--streak', type=int, default=13, help='shortest streak kept, in pixels (13 at 4K)')
    r.add_argument('--min-channel', action='store_true', help='keep only streaks bright in all three channels')
    r.add_argument('--match', type=float, default=90)
    r.add_argument('--erode', type=int, default=21, help='pull the mask edge in by about half this many pixels')
    r.add_argument('--soften', type=float, default=7, help='feather of the mask edge, pixels')
    r.add_argument('--sheet')
    a = p.parse_args(argv)
    return {'plate': cmd_plate, 'apply': cmd_apply}[a.cmd](a)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as err:
        print('plate_repair:', err, file=sys.stderr)
        sys.exit(1)
