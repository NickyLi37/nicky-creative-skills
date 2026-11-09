#!/usr/bin/env python3
"""A cover with one giant title standing behind the subject: the HONG KONG layout.

usage:
  title_cover.py STILL.png MASK OUT.jpg --title "HONG KONG" [--size 3840x2160] [--scale 1.0] [--offset 0,624]
                 [--title-width 3620] [--title-top 270] [--font FONT.ttf] [--hratio .285] [--track .033] [--space .19]
                 [--color 253,1,1] [--glow 230,1,5] [--feather 500] [--cut "x,y x,y ..."]
                 [--logo LOGO.png] [--logo-width 260] [--logo-pos 80,60] [--also 1920x1080 ...] [--quality 92]

STILL is a clean frame of the film (no lyrics, no logo). MASK is the subject mask at the still's size: a PNG,
or the raw float32 file written by subject_mask.swift (macOS Vision). The picture is scaled by --scale and its
top-left corner placed at --offset on a canvas of --size. The title zone goes almost black, the title is set in a
heavy face squeezed per glyph (the H is --hratio as wide as it is tall; letter gap and word space are shares of
the cap height), then the subject is laid back on top with the title's light wrapping its edges.

Measured on the user's reference for HONG KONG: Impact squeezed to H = 0.285, gap 0.033, space 0.19, pure red
(253, 1, 1) letters with a dark red glow outside them, title about 94% of the frame width. --cut drops the mask
above a polyline (the cover's orange cat had a tail tip showing above its head that read as a hair bun).
The report says whether the title, the subject and the logo sit inside the centred 4:3 area, which is what a
platform that crops to 4:3 keeps. Needs numpy, opencv-python and Pillow.
"""
import argparse
import os
import sys

import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

FONTS = ['/System/Library/Fonts/Supplemental/Impact.ttf', 'C:/Windows/Fonts/impact.ttf',
         '/usr/share/fonts/truetype/msttcorefonts/Impact.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']


def blur(a, s):
    return cv2.GaussianBlur(a, (0, 0), max(s, 0.1))


def rgb(text):
    v = [float(x) / 255 for x in text.split(',')]
    if len(v) != 3:
        raise ValueError('colours are r,g,b in 0..255')
    return np.array(v, np.float32)


class Title:
    def __init__(self, text, font, hratio, track, space):
        self.text, self.font, self.hratio, self.track, self.space = text, font, hratio, track, space
        self._per_cap = None

    def mask(self, cap):
        """The title as a float mask cropped to its ink, and the row of the cap top inside it."""
        f = ImageFont.truetype(self.font, 1000)
        f = ImageFont.truetype(self.font, max(4, int(round(1000 * cap / -f.getbbox('H', anchor='ls')[1]))))
        cap_h = -f.getbbox('H', anchor='ls')[1]
        pad, base, rows = int(cap * .2), int(cap * 1.2), int(cap * 1.4)

        def glyph(c):
            l, t, r, b = f.getbbox(c, anchor='ls')
            im = Image.new('L', (r - l + 2 * pad, rows), 0)
            ImageDraw.Draw(im).text((pad - l, base), c, font=f, fill=255, anchor='ls')
            a = np.asarray(im)
            xs = np.nonzero(a.max(0))[0]
            return a[:, xs.min():xs.max() + 1] if len(xs) else np.zeros((rows, 1), np.uint8)
        sq = self.hratio * cap / glyph('H').shape[1]
        parts = []
        for c in self.text:
            if c == ' ':
                parts.append(np.zeros((rows, int(round(cap * self.space))), np.uint8))
                continue
            g = glyph(c)
            parts += [cv2.resize(g, (max(1, int(round(g.shape[1] * sq))), rows), interpolation=cv2.INTER_AREA),
                      np.zeros((rows, int(round(cap * self.track))), np.uint8)]
        a = np.hstack(parts[:-1]).astype(np.float32) / 255
        ys = np.nonzero(a.max(1))[0]
        return a[ys.min():ys.max() + 1], base - cap_h - ys.min()

    def cap_for(self, width):
        if self._per_cap is None:
            self._per_cap = self.mask(1000)[0].shape[1] / 1000
        return int(width / self._per_cap)


def place(img, s, x0, y0, W, H):
    """img scaled by s with its top-left corner at (x0, y0) on a W x H canvas, and where it covers the canvas."""
    sw, sh = int(round(img.shape[1] * s)), int(round(img.shape[0] * s))
    sc = cv2.resize(img, (sw, sh), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    out = np.zeros((H, W) + img.shape[2:], np.float32)
    cov = np.zeros((H, W), np.float32)
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + sw), min(H, y0 + sh)
    if xb > xa and yb > ya:
        out[ya:yb, xa:xb] = sc[ya - y0:yb - y0, xa - x0:xb - x0]
        cov[ya:yb, xa:xb] = 1
    return out, cov


def load(still, mask, cut=None):
    src = cv2.imread(still)
    if src is None:
        raise ValueError(f'cannot read {still}')
    src = src[..., ::-1].astype(np.float32) / 255
    h, w = src.shape[:2]
    if mask.lower().endswith('.f32'):
        m = np.fromfile(mask, np.float32)
        if m.size != h * w:
            raise ValueError('the raw mask is not the size of the still')
        m = m.reshape(h, w).copy()
    else:
        m = cv2.imread(mask, cv2.IMREAD_GRAYSCALE)
        if m is None:
            raise ValueError(f'cannot read {mask}')
        m = cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    if cut:
        pts = np.array([[float(v) for v in p.split(',')] for p in cut.split()], np.float32)
        xs, ys = pts[:, 0], pts[:, 1]
        x = np.arange(int(xs.min()), int(xs.max()) + 1)
        top = np.interp(x, xs, ys)
        y = np.arange(h, dtype=np.float32)[:, None]
        m[:, x] *= np.clip((y - top[None, :]) / 5 + .5, 0, 1)
    # the mask edge carries a thin line of the background; pull it in 2 px and soften it
    m = blur(cv2.erode(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))), 1.0)
    return src, m


def compose(src, subj, a, title, logo=None):
    W, H = a.W, a.H
    pic, cov = place(src, a.scale, a.x0, a.y0, W, H)
    sub = place(subj, a.scale, a.x0, a.y0, W, H)[0]
    yy = np.arange(H, dtype=np.float32)
    if a.y0 > 0:                                   # the picture's top edge fades into the dark; the subject stays solid
        cov *= (np.clip((yy - a.y0) / a.feather, 0, 1) ** 1.5)[:, None]
    if a.x0 > 0:
        cov *= (np.clip((np.arange(W, dtype=np.float32) - a.x0) / (.7 * a.feather), 0, 1) ** 1.5)[None, :]
    cap = title.cap_for(a.title_width)
    m, ctop = title.mask(cap)
    T = np.zeros((H, W), np.float32)
    tx, ty = (W - m.shape[1]) // 2, a.title_top - ctop
    ys0, xs0 = max(0, ty), max(0, tx)
    ys1, xs1 = min(H, ty + m.shape[0]), min(W, tx + m.shape[1])
    T[ys0:ys1, xs0:xs1] = m[ys0 - ty:ys1 - ty, xs0 - tx:xs1 - tx]
    foot = a.title_top + cap
    keep = .2 + .6 * np.clip((yy - (foot - .2 * cap)) / (.6 * cap), 0, 1) ** 1.3    # dark behind the title, then the street
    comp = pic * cov[..., None] * keep[:, None, None]
    fill = a.color * (1 - .12 * np.clip((yy - a.title_top) / cap, 0, 1))[:, None, None]
    halo = ((blur(T, .008 * cap) * .5 + blur(T, .045 * cap) * .4 + blur(T, .16 * cap) * .3) * (1 - T))[..., None] * a.glow
    comp = 1 - (1 - comp) * (1 - np.clip(halo, 0, 1))
    comp = comp * (1 - T[..., None]) + fill * T[..., None]
    out = pic * sub[..., None] + comp * (1 - sub[..., None])
    light = blur(fill * T[..., None] + halo, .025 * cap)
    edge = (sub * (1 - blur(sub, .012 * cap)))[..., None]
    out = 1 - (1 - out) * (1 - np.clip(light * edge * .9, 0, 1))
    rng = np.random.default_rng(828)
    out = out + (rng.normal(0, .011, (H, W)).astype(np.float32) * (.4 + .6 * T))[..., None]
    out = np.clip(out, 0, 1)
    boxes = {'title': (tx, ty, m.shape[1], m.shape[0])}
    ys, xs = np.nonzero(sub > .5)
    if len(xs):
        boxes['subject'] = (int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1))
    if logo is not None:
        lg = cv2.imread(logo, cv2.IMREAD_UNCHANGED)
        if lg is None:
            raise ValueError(f'cannot read {logo}')
        if lg.shape[2] == 3:
            lg = np.dstack([lg, np.full(lg.shape[:2], 255, np.uint8)])
        lw = a.logo_width
        lh = int(lg.shape[0] * lw / lg.shape[1])
        lg = cv2.resize(lg, (lw, lh), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
        lx, ly = a.logo_x, a.logo_y
        al = lg[..., 3:4] * .9
        out[ly:ly + lh, lx:lx + lw] = out[ly:ly + lh, lx:lx + lw] * (1 - al) + lg[..., 2::-1] * al
        boxes['logo'] = (lx, ly, lw, lh)
    return out, cap, boxes


def inside_43(boxes, W, H):
    w43 = H * 4 / 3
    x0, x1 = (W - w43) / 2, (W + w43) / 2
    return {k: (b[0] >= x0 - 1 and b[0] + b[2] <= x1 + 1) for k, b in boxes.items()}, (round(x0), round(x1))


def save(img, path, size, q):
    im = cv2.resize(np.clip(img, 0, 1)[..., ::-1] * 255, size, interpolation=cv2.INTER_AREA)
    cv2.imwrite(path, im.astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, q, cv2.IMWRITE_JPEG_OPTIMIZE, 1,
                                            cv2.IMWRITE_JPEG_SAMPLING_FACTOR, cv2.IMWRITE_JPEG_SAMPLING_FACTOR_444])
    print(f'{path} {size[0]}x{size[1]} {os.path.getsize(path) / 1e6:.2f} MB')   # 4:4:4 keeps red edges clean


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('still')
    p.add_argument('mask')
    p.add_argument('out')
    p.add_argument('--title', required=True)
    p.add_argument('--size', default='3840x2160')
    p.add_argument('--scale', type=float, default=1.0)
    p.add_argument('--offset', default='0,0', help='top-left corner of the scaled picture on the canvas')
    p.add_argument('--title-width', type=int, help='default: 94%% of the canvas width')
    p.add_argument('--title-top', type=int, help='row of the cap top; default: 1/8 of the canvas height')
    p.add_argument('--font', help='a heavy face; default: Impact where installed')
    p.add_argument('--hratio', type=float, default=.285)
    p.add_argument('--track', type=float, default=.033)
    p.add_argument('--space', type=float, default=.19)
    p.add_argument('--color', default='253,1,1')
    p.add_argument('--glow', default='230,1,5')
    p.add_argument('--feather', type=float, default=500)
    p.add_argument('--cut')
    p.add_argument('--logo')
    p.add_argument('--logo-width', type=int, default=260)
    p.add_argument('--logo-pos', default='80,60')
    p.add_argument('--also', nargs='*', default=[], help='more sizes, written next to OUT')
    p.add_argument('--quality', type=int, default=92)
    a = p.parse_args(argv)
    a.W, a.H = map(int, a.size.lower().split('x'))
    a.x0, a.y0 = map(int, a.offset.split(','))
    a.logo_x, a.logo_y = map(int, a.logo_pos.split(','))
    a.title_width = a.title_width or int(a.W * .94)
    a.title_top = a.title_top if a.title_top is not None else a.H // 8
    a.color, a.glow = rgb(a.color), rgb(a.glow)
    font = a.font or next((f for f in FONTS if os.path.exists(f)), None)
    if not font:
        raise ValueError('no heavy font found; pass --font')
    src, subj = load(a.still, a.mask, a.cut)
    img, cap, boxes = compose(src, subj, a, Title(a.title, font, a.hratio, a.track, a.space), a.logo)
    print('font', os.path.basename(font), 'cap height', cap, 'boxes', boxes)
    ok, span = inside_43(boxes, a.W, a.H)
    print(f'centred 4:3 area x {span[0]}..{span[1]}:', ', '.join(f'{k} {"inside" if v else "OUTSIDE"}' for k, v in ok.items()))
    save(img, a.out, (a.W, a.H), a.quality)
    stem, ext = os.path.splitext(a.out)
    for s in a.also:
        w, h = map(int, s.lower().split('x'))
        save(img, f'{stem}_{w}x{h}{ext}', (w, h), a.quality)
    return boxes, ok


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError) as err:
        print('title_cover:', err, file=sys.stderr)
        sys.exit(1)
