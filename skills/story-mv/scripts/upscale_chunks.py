#!/usr/bin/env python3
"""Group the cut's clips into upscale chunks that end on shot boundaries.

usage: upscale_chunks.py LIST.txt [--max 17] [--rate R] [--quote-rate Q] [--write OUT_DIR]

LIST.txt holds the clips in edit order, one path per line or as an ffmpeg concat list (file '...').
Clips are added to a chunk until the next one would take it past --max seconds; a single clip longer than
--max becomes its own chunk and is flagged. --rate and --quote-rate (credits per second, read them off a
live quote) print what each chunk should cost and what will be held while it runs. --write joins each chunk
with ffmpeg stream copy into OUT_DIR/chunk_NN.mp4 and writes OUT_DIR/chunks.json with every clip's first
frame inside its chunk, so upscaled frames map back to shots.

Why chunks: in the HONG KONG film the 4K upscale of the 1080p cut ran as 13 chunks of about 17 s side by side.
Each job held its full quote while it ran and refunded the difference when it settled; all 30 upscale jobs
(chunks, a test and single-shot redos) settled at 19,113 credits against 80,101 quoted, about a quarter.
Shorter chunks hold less at once, and a bad chunk is cheap to redo. Prices change: quote before each batch.
Needs ffprobe on PATH (and ffmpeg for --write). The clips must share codec, size and frame rate.
"""
import argparse
import json
import os
import subprocess
import sys


def read_list(path):
    out = []
    base = os.path.dirname(os.path.abspath(path))
    with open(path, encoding='utf-8') as fh:
        lines = fh.read().splitlines()
    for line in lines:
        s = line.strip()
        if not s or s.startswith('#'):
            continue
        if s.startswith('file '):
            s = s[5:].strip().strip("'\"")
        out.append(s if os.path.isabs(s) else os.path.join(base, s))
    return out


def frames_and_fps(path):
    out = subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_packets', '-show_entries',
                                   'stream=nb_read_packets,r_frame_rate', '-of', 'json', path])
    s = json.loads(out)['streams'][0]
    num, den = map(int, s['r_frame_rate'].split('/'))
    return int(s['nb_read_packets']), num / den


def plan(clips, max_s):
    groups, cur, acc, fps0 = [], [], 0, None
    for c in clips:
        n, fps = frames_and_fps(c)
        if fps0 is None:
            fps0 = fps
        elif abs(fps - fps0) > 1e-3:
            raise ValueError(f'{c} runs at {fps:g} fps, the others at {fps0:g}')
        if cur and (acc + n) / fps > max_s:
            groups.append((cur, acc))
            cur, acc = [], 0
        cur.append((c, n))
        acc += n
    if cur:
        groups.append((cur, acc))
    return groups, fps0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('list')
    p.add_argument('--max', type=float, default=17.0, help='longest chunk in seconds')
    p.add_argument('--rate', type=float, help='credits per second the job settles at')
    p.add_argument('--quote-rate', type=float, help='credits per second the quote holds')
    p.add_argument('--write', metavar='OUT_DIR')
    a = p.parse_args(argv)
    clips = read_list(a.list)
    if not clips:
        raise ValueError('the list is empty')
    groups, fps = plan(clips, a.max)
    rows, total = [], 0
    for i, (g, n) in enumerate(groups):
        sec = n / fps
        total += n
        cost = f'  ~{sec * a.rate:,.0f} credits' if a.rate else ''
        hold = f'  holds {sec * a.quote_rate:,.0f}' if a.quote_rate else ''
        flag = '  LONGER THAN --max' if sec > a.max else ''
        print(f'chunk {i:02d}: {len(g):2d} clips, {n:5d} frames, {sec:6.2f} s{cost}{hold}{flag}')
        first, pos = [], 0
        for c, k in g:
            first.append(dict(clip=os.path.basename(c), first_frame=pos, frames=k))
            pos += k
        rows.append(dict(chunk=i, frames=n, seconds=round(sec, 3), clips=first))
    print(f'{len(groups)} chunks, {total} frames, {total / fps:.2f} s' +
          (f', about {total / fps * a.rate:,.0f} credits' if a.rate else ''))
    if a.write:
        os.makedirs(a.write, exist_ok=True)
        for r, (g, _) in zip(rows, groups):
            lst = os.path.join(a.write, f'chunk_{r["chunk"]:02d}.txt')
            with open(lst, 'w', encoding='utf-8') as f:
                f.writelines("file '{}'\n".format(os.path.abspath(c).replace("'", "'\\''")) for c, _ in g)
            o = os.path.join(a.write, f'chunk_{r["chunk"]:02d}.mp4')
            subprocess.check_call(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst,
                                   '-c', 'copy', '-movflags', '+faststart', o])
            r['file'] = os.path.basename(o)
        with open(os.path.join(a.write, 'chunks.json'), 'w', encoding='utf-8') as fh:
            json.dump(rows, fh, indent=1)
        print('wrote', len(rows), 'chunks to', a.write)
    return rows


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as err:
        print('upscale_chunks:', err, file=sys.stderr)
        sys.exit(1)
