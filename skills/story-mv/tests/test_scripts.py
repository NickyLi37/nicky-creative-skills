"""Tests for the story-mv helpers, on synthetic media made at test time and removed afterwards.

python3 skills/story-mv/tests/test_scripts.py
Standard-library helpers always run. Tests that need numpy, OpenCV or Pillow skip when those are missing,
and tests that need ffmpeg skip without it. STORY_MV_ASR=1 also runs the Whisper cut test (Apple silicon with
mlx-whisper and macOS `say`; it loads a large model).
"""
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import unittest
import wave
import zipfile
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / 'scripts'
sys.path.insert(0, str(SCRIPTS))
HAS_FFMPEG = bool(shutil.which('ffmpeg') and shutil.which('ffprobe'))


def has(*mods):
    return all(importlib.util.find_spec(m) for m in mods)


def quiet(fn, *a, **k):
    with redirect_stdout(io.StringIO()) as out:
        r = fn(*a, **k)
    return r, out.getvalue()


def encode_raw(frames, path, fps=24, lossless=False):
    """frames: list of HxWx3 uint8 RGB arrays -> H.264 file."""
    h, w = frames[0].shape[:2]
    q = ['-crf', '0', '-pix_fmt', 'yuv444p'] if lossless else ['-crf', '12', '-pix_fmt', 'yuv420p']
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-r', str(fps), '-i', '-',
                          '-vf', 'scale=out_color_matrix=bt709:out_range=tv', '-c:v', 'libx264', *q,
                          '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', str(path)], stdin=subprocess.PIPE)
    for f in frames:
        p.stdin.write(f.tobytes())
    p.stdin.close()
    assert p.wait() == 0


def decode(path, w, h):
    import numpy as np
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-vf', 'scale=in_color_matrix=bt709:in_range=tv:out_range=pc,format=rgb24',
                          '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)


class Temp(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='story-mv-test-'))
        self.addCleanup(shutil.rmtree, self.tmp, True)


class CardTiming(Temp):
    def test_counting_and_verdicts(self):
        import card_timing as C
        self.assertEqual(C.words('Written by The Weeknd · 陳小霞 · 楊立德')[0], 6)
        self.assertEqual(C.words('youtube.com/watch?v=abc & more')[0], 3)
        self.assertEqual(C.words('S A M P L E')[0], 6)
        cards = self.tmp / 'cards.txt'
        cards.write_text('@hold 6.5\nMUSIC\nHONG KONG\n\n@hold 1.5\none two three four five six seven eight nine ten\n\n'
                         + '\n'.join(f'line {i}' for i in range(7)) + '\n', encoding='utf-8')
        rows, bad = C.check(C.load(str(cards)))
        self.assertEqual([r['verdict'] for r in rows], ['OK', 'SHORT', 'no hold given'])
        self.assertEqual(rows[1]['suggest'], 2.5)
        self.assertIn('7 lines', rows[2]['notes'][0])
        self.assertEqual(bad, 2)
        j = self.tmp / 'cards.json'
        j.write_text(json.dumps([{'hold': 2.2, 'lines': ['one two three four five six seven eight nine ten']}]))
        self.assertEqual(C.check(C.load(str(j)))[0][0]['verdict'], 'TIGHT')


class SharePack(Temp):
    def test_names_flags_and_storage(self):
        import share_pack as S
        root = self.tmp / '交付包'
        (root / '01_成片').mkdir(parents=True)
        nfd = unicodedata.normalize('NFD', 'Café_封面.jpg')
        (root / nfd).write_bytes(b'\xff\xd8' + os.urandom(2000))
        (root / '01_成片' / 'film.mp4').write_bytes(os.urandom(4000))
        (root / '说明.txt').write_text('说明 ' * 200, encoding='utf-8')
        (root / '.DS_Store').write_bytes(b'x')
        out, _ = quiet(S.pack, str(root))
        out = out[0]
        with zipfile.ZipFile(out) as z:
            info = {i.filename: i for i in z.infolist()}
            self.assertIsNone(z.testzip())
        self.assertIn(unicodedata.normalize('NFC', '交付包/Café_封面.jpg'), info)
        self.assertNotIn('交付包/.DS_Store', info)
        for i in info.values():
            self.assertTrue(i.flag_bits & 0x800, i.filename)
        self.assertEqual(info['交付包/01_成片/film.mp4'].compress_type, zipfile.ZIP_STORED)
        self.assertEqual(info['交付包/说明.txt'].compress_type, zipfile.ZIP_DEFLATED)
        with self.assertRaises(ValueError):
            S.pack(str(root), str(root / 'inside.zip'))


class BeatSnap(Temp):
    def test_snap_to_grid(self):
        import beat_grid as B
        board = self.tmp / 'board.json'
        board.write_text(json.dumps({'title': 't', 'shots': [{'id': 'A', 'start': 0, 'end': 1.3}, {'id': 'B', 'start': 1.3, 'end': 1.62},
                                                              {'id': 'C', 'start': 1.62, 'end': 3.04}]}))
        out = self.tmp / 'snapped.json'
        rows, log = quiet(B.main, ['snap', str(board), '--bpm', '120', '--first', '0.25', '--out', str(out)])
        self.assertEqual([(r['start'], r['end']) for r in rows], [(0, 1.25), (1.25, 1.75), (1.75, 3.25)])
        self.assertEqual([r['frames'] for r in rows], [30, 12, 36])
        self.assertEqual(json.loads(out.read_text())['title'], 't')
        rows, log = quiet(B.main, ['snap', str(board), '--bpm', '120', '--first', '0.25', '--min-frames', '20'])
        self.assertIn('SHORT', log)


@unittest.skipUnless(HAS_FFMPEG and has('numpy'), 'needs ffmpeg and numpy')
class BeatAudio(Temp):
    def clicks(self, bpm=120.0, first=0.25, dur=30.0):
        import numpy as np
        sr = 22050
        rng = np.random.default_rng(1)
        x = 0.01 * rng.standard_normal(int(dur * sr)).astype(np.float32)
        for k, tc in enumerate(np.arange(first, dur - 0.1, 60 / bpm)):
            i, n = int(round(tc * sr)), int(0.03 * sr)
            x[i:i + n] += rng.standard_normal(n).astype(np.float32) * np.exp(-np.arange(n) / (0.006 * sr)) * (0.8 if k % 4 == 0 else 0.5)
        path = self.tmp / 'clicks.wav'
        with wave.open(str(path), 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
        return str(path)

    def test_onset_labels_are_calibrated(self):
        import numpy as np
        import beat_grid as B
        song = self.clicks()
        env, t = B.onset_envelope(B.load_audio(song))
        offs = []
        for tc in np.arange(0.25, 29.9, 0.5)[2:-2]:
            m = (t > tc - .12) & (t < tc + .12)
            offs.append(t[m][np.argmax(env[m])] - tc)
        self.assertLess(abs(float(np.mean(offs))), 0.004)

    def test_estimate_and_phase(self):
        import beat_grid as B
        song = self.clicks()
        (bpm, first), _ = quiet(B.main, ['estimate', song, '--min-bpm', '80', '--max-bpm', '180'])
        self.assertAlmostEqual(bpm, 120, delta=1.0)
        self.assertAlmostEqual(first, 0.25, delta=0.012)
        p, log = quiet(B.main, ['phase', song, '--bpm', '120', '--first', '0.30'])
        self.assertAlmostEqual(p, -0.05, delta=0.008)
        self.assertIn('delay the audio by', log)


@unittest.skipUnless(HAS_FFMPEG, 'needs ffmpeg')
class UpscaleChunks(Temp):
    def test_groups_end_on_clip_boundaries(self):
        import upscale_chunks as U
        clips = []
        for i, sec in enumerate([4, 4, 6, 3, 12]):
            c = self.tmp / f'S{i}.mp4'
            subprocess.check_call(['ffmpeg', '-y', '-v', 'error', '-f', 'lavfi', '-i', f'testsrc2=s=160x90:r=24:d={sec}',
                                   '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(c)])
            clips.append(c)
        lst = self.tmp / 'list.txt'
        lst.write_text(''.join(f"file '{c.name}'\n" for c in clips))
        rows, log = quiet(U.main, [str(lst), '--max', '10', '--rate', '57.7', '--write', str(self.tmp / 'up')])
        self.assertEqual([r['frames'] for r in rows], [192, 216, 288])
        self.assertEqual([len(r['clips']) for r in rows], [2, 2, 1])
        self.assertEqual(rows[1]['clips'][1]['first_frame'], 144)
        self.assertIn('LONGER THAN --max', log)
        n = U.frames_and_fps(str(self.tmp / 'up' / 'chunk_01.mp4'))[0]
        self.assertEqual(n, 216)


@unittest.skipUnless(HAS_FFMPEG and has('numpy', 'cv2'), 'needs ffmpeg, numpy and OpenCV')
class FilmLook(Temp):
    def setUp(self):
        super().setUp()
        import numpy as np
        rng = np.random.default_rng(3)
        self.W, self.H = 192, 108
        frames = []
        for i in range(30):
            f = np.full((self.H, self.W, 3), 40, np.uint8)
            f[30:70, 10 + 4 * i:40 + 4 * i] = (200, 60, 50)
            f += rng.integers(0, 12, f.shape, dtype=np.uint8)
            frames.append(f)
        self.src = self.tmp / 'src.mp4'
        encode_raw(frames, self.src, lossless=True)

    def run_look(self, out, *extra):
        import film_look as F
        quiet(F.main, [str(self.src), str(out), *extra])
        return decode(out, self.W, self.H)

    def test_chunks_join_into_the_whole_render(self):
        import numpy as np
        args = ['--grain', '1.2', '--flicker', '.004', '--hand', '3', '--diffuse', '.1', '--edge-soft', '.22', '--step', 'blend']
        whole = self.run_look(self.tmp / 'all.mov', *args)
        a = self.run_look(self.tmp / 'a.mov', '--to', '13', *args)
        b = self.run_look(self.tmp / 'b.mov', '--from', '13', *args)
        self.assertEqual(len(whole), 30)
        self.assertTrue(np.array_equal(np.concatenate([a, b]), whole))

    def test_step_hold_holds_pairs_and_logo_stays_clean(self):
        import numpy as np
        import cv2
        logo = self.tmp / 'logo.png'
        cv2.imwrite(str(logo), np.dstack([np.full((10, 40, 3), 255, np.uint8), np.full((10, 40), 255, np.uint8)]))
        spec = self.tmp / 'spec.json'
        spec.write_text(json.dumps({'fps': 24, 'shots': [{'id': 'A', 'start': 0, 'end': 0.625}, {'id': 'B', 'start': 0.625, 'end': 1.25}],
                                    'step_hold': ['A']}))
        out = self.run_look(self.tmp / 'h.mov', '--spec', str(spec), '--grain', '0', '--logo', str(logo), '--logo-w', '.2')
        diff = lambda i, j: float(np.abs(out[i].astype(int) - out[j].astype(int)).max())
        self.assertEqual(diff(0, 1), 0)
        self.assertEqual(diff(12, 13), 0)
        self.assertGreater(diff(13, 14), 0)   # 15 frames in A: the last one stands alone, never paired with B
        self.assertGreater(diff(16, 17), 0)   # B is not on step print
        lx, ly = int(self.W * .022), int(self.H * .03)
        self.assertGreater(out[5, ly + 2:ly + 8, lx + 2:lx + 30].mean(), 215)


@unittest.skipUnless(HAS_FFMPEG and has('numpy', 'cv2'), 'needs ffmpeg, numpy and OpenCV')
class FlowRamp(Temp):
    def test_positions_and_in_between(self):
        import numpy as np
        import flow_ramp as R
        self.assertEqual(R.parse_steps('4*2, 1.5,1*2'), [4, 4, 1.5, 1, 1])
        p = R.positions(14, R.parse_steps('4*4,3*3,2*28,1.8,1.6,1.4,1.2,1*23'), 2, 1)
        self.assertEqual((len(p), p[0], p[-1]), (125, 14, 124))
        rng = np.random.default_rng(5)
        tex = rng.integers(60, 255, (24, 24, 3), dtype=np.uint8)
        bg = rng.integers(0, 25, (90, 160, 3), dtype=np.uint8)
        frames = []
        for i in range(8):
            f = bg.copy()
            f[30:54, 20 + 10 * i:44 + 10 * i] = tex
            frames.append(f)
        src = self.tmp / 'move.mp4'
        encode_raw(frames, src, lossless=True)
        out = self.tmp / 'ramp'
        pos, _ = quiet(R.main, [str(src), str(out), '--start', '0', '--steps', '0.5*4', '--hold', '1', '--sheet', str(self.tmp / 's.jpg')])
        self.assertEqual(pos, [0, 0.5, 1, 1.5, 2])
        import cv2
        def cx(img):
            m = img.max(2) > 50
            return float(np.nonzero(m)[1].mean())
        mid = cv2.imread(str(out / '0002.png'))
        self.assertAlmostEqual(cx(mid), 20 + 5 + 11.5, delta=2.0)
        self.assertTrue((self.tmp / 's.jpg').exists())


@unittest.skipUnless(HAS_FFMPEG and has('numpy', 'cv2'), 'needs ffmpeg, numpy and OpenCV')
class PlateRepair(Temp):
    def test_defect_goes_and_rain_stays(self):
        import numpy as np
        import cv2
        import plate_repair as P
        W, H = 160, 120
        rng = np.random.default_rng(7)
        bg = np.dstack([np.tile(np.linspace(40, 90, W, dtype=np.float32), (H, 1))] * 3)
        defect = bg.copy()
        defect[40:80, 60:100] = (220, 40, 40)
        frames = []
        for i in range(25):
            f = defect.copy()
            for x in rng.integers(0, W, 6):
                y = int(rng.integers(0, H - 30))
                f[y:y + 30, x] = 230
            frames.append(np.clip(f, 0, 255).astype(np.uint8))
        src = self.tmp / 'rain.mp4'
        encode_raw(frames, src, lossless=True)
        plate = self.tmp / 'plate.png'
        quiet(P.main, ['plate', str(src), str(plate)])
        pl = cv2.imread(str(plate))[..., ::-1].astype(np.float32)
        self.assertGreater(pl[60, 80, 0] - pl[60, 80, 2], 120)          # the defect is static, so it is in the plate
        self.assertLess(np.abs(pl[:, 10:50] - bg[:, 10:50]).max(), 12)  # the rain is not
        edit = np.clip(bg, 0, 255).astype(np.uint8)[..., ::-1]
        cv2.imwrite(str(self.tmp / 'edit.png'), edit)
        mask = np.zeros((H, W), np.uint8)
        mask[30:90, 50:110] = 255
        cv2.imwrite(str(self.tmp / 'mask.png'), mask)
        out = self.tmp / 'fixed'
        quiet(P.main, ['apply', str(src), str(out), '--plate', str(plate), '--edit', str(self.tmp / 'edit.png'),
                       '--mask', str(self.tmp / 'mask.png'), '--match', '0', '--streak', '9', '--erode', '5', '--soften', '2'])
        res = [cv2.imread(str(out / f'{i + 1:04d}.png'))[..., ::-1].astype(np.float32) for i in range(25)]
        self.assertLess(np.median([r[50:70, 70:90, 0] - r[50:70, 70:90, 2] for r in res]), 15)   # red defect gone
        kept = 0
        for f, r in zip(frames, res):
            ys, xs = np.nonzero((f[45:75, 65:95, 1] > 200))
            if len(xs):
                kept += int((r[45:75, 65:95, 1][ys, xs] > 150).mean() > 0.8)
        self.assertGreater(kept, 3)                                       # streaks inside the mask survive


@unittest.skipUnless(has('numpy', 'cv2', 'PIL'), 'needs numpy, OpenCV and Pillow')
class TitleCover(Temp):
    def test_title_behind_subject_and_43_report(self):
        import numpy as np
        import cv2
        import title_cover as T
        font = next((f for f in T.FONTS if os.path.exists(f)), None)
        if not font:
            self.skipTest('no heavy font installed')
        W, H = 640, 360
        still = np.full((H, W, 3), 30, np.uint8)
        cv2.circle(still, (320, 250), 70, (235, 235, 235), -1)
        cv2.imwrite(str(self.tmp / 'still.png'), still)
        mask = np.zeros((H, W), np.uint8)
        cv2.circle(mask, (320, 250), 70, 255, -1)
        cv2.imwrite(str(self.tmp / 'mask.png'), mask)
        out = self.tmp / 'cover.jpg'
        (boxes, ok), log = quiet(T.main, [str(self.tmp / 'still.png'), str(self.tmp / 'mask.png'), str(out), '--title', 'HONG KONG',
                                          '--size', '640x360', '--title-width', '440', '--title-top', '130', '--feather', '60',
                                          '--font', font, '--also', '320x180'])
        img = cv2.imread(str(out))[..., ::-1].astype(np.float32)
        self.assertEqual(img.shape[:2], (H, W))
        tx, ty, tw, th = boxes['title']
        self.assertAlmostEqual(tw, 440, delta=8)
        band = img[ty:ty + th, tx:tx + tw]
        red = (band[..., 0] > 180) & (band[..., 1] < 60) & (band[..., 2] < 60)
        self.assertGreater(red.mean(), 0.2)
        self.assertGreater(img[250, 320].min(), 200)          # the subject stands in front of the title
        self.assertTrue(ok['title'] and ok['subject'])
        self.assertTrue((self.tmp / 'cover_320x180.jpg').exists())


@unittest.skipUnless(os.environ.get('STORY_MV_ASR') == '1' and has('numpy', 'mlx_whisper') and shutil.which('say') and HAS_FFMPEG,
                     'set STORY_MV_ASR=1 on Apple silicon with mlx-whisper and macOS say')
class LyricCutTest(Temp):
    def test_collapse_finds_the_word_onset(self):
        import numpy as np
        import lyric_cut_test as L
        words = ['red', 'taxi', 'corner', 'tonight']
        parts, t, onset = [], 0.0, {}
        for w in words:
            a = self.tmp / f'{w}.aiff'
            subprocess.check_call(['say', '-v', 'Samantha', '-o', str(a), w])
            wv = self.tmp / f'{w}.wav'
            subprocess.check_call(['ffmpeg', '-y', '-v', 'error', '-i', str(a), '-af',
                                   'silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse',
                                   '-ar', '16000', '-ac', '1', str(wv)])
            with wave.open(str(wv)) as r:
                d = r.getnframes() / r.getframerate()
            onset[w] = t + 0.6
            parts.append(wv)
            t += 0.6 + d
        audio = self.tmp / 'line.wav'
        inputs = []
        for p in parts:
            inputs += ['-f', 'lavfi', '-t', '0.6', '-i', 'anullsrc=r=16000:cl=mono', '-i', str(p)]
        n = len(parts) * 2
        subprocess.check_call(['ffmpeg', '-y', '-v', 'error', *inputs, '-filter_complex',
                               ''.join(f'[{i}:a]' for i in range(n)) + f'concat=n={n}:v=0:a=1,apad=pad_dur=2', '-ar', '16000', str(audio)])
        line = self.tmp / 'line.txt'
        line.write_text(' '.join(words))
        got, log = quiet(L.main, [str(audio), str(line), '--word', '2', '--near', f'{onset["corner"] + 0.3:.2f}', '--end', f'{t + 1.5:.2f}'])
        self.assertIsNotNone(got, log)
        self.assertAlmostEqual(got, onset['corner'], delta=0.05, msg=log)
        print(log.strip().splitlines()[-1], f'(true onset {onset["corner"]:.3f} s)')


if __name__ == '__main__':
    unittest.main(verbosity=2)
