#!/usr/bin/env python3
"""ZIP a delivery folder so it opens cleanly anywhere.

usage: share_pack.py FOLDER [OUT.zip]

- Names are stored in NFC with the UTF-8 flag, so Chinese file names read correctly on Windows and macOS.
- Video, images and audio that are already compressed are stored as they are; text is deflated.
- ZIP64 is on, so a 4K master over 4 GB fits. Dot files are left out.
- Every member's CRC is checked after writing.
Build the folder first (copies, or APFS clones with `cp -c` on macOS, which take no extra disk until edited).
Standard library only.
"""
import os
import sys
import unicodedata
import zipfile

STORED = ('.mp4', '.mov', '.m4v', '.mkv', '.webm', '.jpg', '.jpeg', '.png', '.webp', '.gif', '.heic', '.avif',
          '.mp3', '.m4a', '.aac', '.ogg', '.opus', '.flac', '.zip', '.7z', '.skill')


def pack(folder, out=None):
    folder = os.path.abspath(folder.rstrip('/'))
    if not os.path.isdir(folder):
        raise ValueError(f'{folder} is not a folder')
    out = os.path.abspath(out or folder + '.zip')
    if out.startswith(folder + os.sep):
        raise ValueError('write the ZIP outside the folder it packs')
    base = os.path.dirname(folder)
    files = []
    for dp, dn, fn in os.walk(folder):
        dn[:] = sorted(d for d in dn if not d.startswith('.'))
        files += [os.path.join(dp, f) for f in sorted(fn) if not f.startswith('.')]
    if not files:
        raise ValueError('nothing to pack')
    tmp = out + '.part'
    with zipfile.ZipFile(tmp, 'w', allowZip64=True) as z:
        for p in files:
            arc = unicodedata.normalize('NFC', os.path.relpath(p, base))
            comp = zipfile.ZIP_STORED if p.lower().endswith(STORED) else zipfile.ZIP_DEFLATED
            z.write(p, arc, compress_type=comp)
    with zipfile.ZipFile(tmp) as z:
        bad = z.testzip()
        if bad:
            raise RuntimeError(f'CRC check failed on {bad}')
        info = z.infolist()
    os.replace(tmp, out)
    total = sum(os.path.getsize(p) for p in files)
    print(f'{out}: {len(info)} files, {total / 1e6:.1f} MB in, {os.path.getsize(out) / 1e6:.1f} MB out, CRC checked')
    return out, info


def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    if not 1 <= len(a) <= 2 or a[0] in ('-h', '--help'):
        print(__doc__)
        return 2
    pack(*a)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as err:
        print('share_pack:', err, file=sys.stderr)
        sys.exit(1)
