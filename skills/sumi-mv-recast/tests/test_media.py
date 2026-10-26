#!/usr/bin/env python3
"""Offline synthetic tests; requires FFmpeg with libx264 and AAC. No project media."""
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'media.py'
spec = importlib.util.spec_from_file_location('media', SCRIPT)
media = importlib.util.module_from_spec(spec)
spec.loader.exec_module(media)


def command(args):
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode:
        raise AssertionError(p.stderr.decode(errors='replace'))
    return p.stdout


def invoke(*args):
    p = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True)
    return p.returncode, json.loads(p.stdout or p.stderr)


class MediaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='mv-recast-test-')
        cls.root = Path(cls.tmp.name)
        cls.source = cls.root / 'source.mp4'
        # Each frame has a different luma, so an off-by-one cut is observable without OCR/image libraries.
        command(['ffmpeg', '-v', 'error', '-nostdin', '-n', '-f', 'lavfi', '-i',
                 "nullsrc=size=160x120:rate=24000/1001,geq=lum='mod(N*31,256)':cb=128:cr=128",
                 '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000:duration=3.003',
                 '-frames:v', '72', '-c:v', 'libx264', '-crf', '0', '-pix_fmt', 'yuv420p',
                 '-video_track_timescale', '24000', '-c:a', 'aac', '-shortest', str(cls.source)])
        cls.source_hash = media.digest(cls.source)
        cls.clip = cls.root / 'cut.mp4'
        code, cls.cut_result = invoke('extract', cls.source, cls.clip, '--fps', '24000/1001',
                                      '--start-frame', '7', '--end-frame', '36')
        if code: raise AssertionError(cls.cut_result)

    @classmethod
    def tearDownClass(cls):
        assert media.digest(cls.source) == cls.source_hash, 'Input changed'
        cls.tmp.cleanup()

    def test_frame_selection_rational_rate_and_silence(self):
        x = self.cut_result
        self.assertEqual((x['frames'], x['fps'], x['audio_streams']), (29, '24000/1001', 0))
        self.assertAlmostEqual(x['duration_seconds'], 29 * 1001 / 24000, places=6)
        self.assertEqual(x['display_aspect_ratio'], '4/3')
        def lumas(path):
            raw = command(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:v:0', '-an',
                           '-fps_mode', 'passthrough', '-pix_fmt', 'yuv420p', '-f', 'rawvideo', '-'])
            stride = 160 * 120 * 3 // 2
            return [raw[i] for i in range(0, len(raw), stride)]
        expected, actual = lumas(self.source)[7:36], lumas(self.clip)
        self.assertEqual(len(actual), 29)
        self.assertTrue(all(abs(a-b) <= 2 for a, b in zip(actual, expected)), (actual, expected))

    def test_no_overwrite_or_bad_range(self):
        before = media.digest(self.clip)
        code, _ = invoke('extract', self.source, self.clip, '--fps', '24000/1001',
                         '--start-frame', 0, '--end-frame', 12)
        self.assertEqual(code, 2)
        self.assertEqual(media.digest(self.clip), before)
        for fps, start, end in [('24', 7, 36), ('24000/1001', -1, 20), ('24000/1001', 0, 73)]:
            output = self.root / 'invalid.mp4'
            code, _ = invoke('extract', self.source, output, '--fps', fps,
                             '--start-frame', start, '--end-frame', end)
            self.assertEqual(code, 2)
            self.assertFalse(output.exists())

    def test_color_reference_keeps_pixels_and_geometry(self):
        source, output = self.root / 'color.mp4', self.root / 'color-cut.mp4'
        command(['ffmpeg', '-v', 'error', '-n', '-f', 'lavfi', '-i',
                 'testsrc2=size=160x90:rate=30:duration=1', '-c:v', 'libx264', str(source)])
        code, result = invoke('extract', source, output, '--fps', 30,
                              '--start-frame', 5, '--end-frame', 20)
        self.assertEqual(code, 0, result)
        self.assertEqual((result['width'], result['height'], result['frames']), (160, 90, 15))
        def frame(path, index):
            return command(['ffmpeg', '-v', 'error', '-i', str(path), '-vf',
                            f'select=eq(n\\,{index}),setpts=PTS-STARTPTS', '-frames:v', '1',
                            '-pix_fmt', 'yuv420p', '-f', 'rawvideo', '-'])
        a, b = frame(source, 5), frame(output, 0)
        self.assertEqual(len(a), len(b))
        self.assertLess(sum(abs(x-y) for x, y in zip(a, b))/len(a), 5)

    def test_inspection_catches_wrong_contract(self):
        code, result = invoke('inspect', self.clip, '--fps', '24', '--frames', '30', '--aspect', '16:9')
        self.assertEqual(code, 1)
        self.assertFalse(result['checks']['expected_fps'])
        self.assertFalse(result['checks']['expected_frames'])
        self.assertFalse(result['checks']['expected_display_aspect'])

    def test_report_cannot_clobber_or_alias_output(self):
        output = self.root / 'report-alias.mp4'
        code, _ = invoke('extract', self.source, output, '--fps', '24000/1001',
                         '--start-frame', 0, '--end-frame', 12, '--report', output)
        self.assertEqual(code, 2)
        self.assertFalse(output.exists())
        report = self.root / 'existing.json'
        report.write_text('preserve me')
        code, _ = invoke('inspect', self.clip, '--report', report)
        self.assertEqual(code, 2)
        self.assertEqual(report.read_text(), 'preserve me')

    def test_exact_aac_copy_passes_but_reencoded_and_shifted_audio_fail(self):
        copied = self.root / 'copied.mp4'
        command(['ffmpeg', '-v', 'error', '-n', '-i', str(self.source), '-c', 'copy', str(copied)])
        code, result = invoke('inspect', copied, '--audio-baseline', self.source)
        self.assertEqual(code, 0, result)
        self.assertTrue(result['audio_comparison']['aac_payloads_equal'])
        changed = self.root / 'changed.mp4'
        command(['ffmpeg', '-v', 'error', '-n', '-i', str(self.source), '-c:v', 'copy',
                 '-af', 'volume=0.5', '-c:a', 'aac', str(changed)])
        code, result = invoke('inspect', changed, '--audio-baseline', self.source)
        self.assertEqual(code, 1)
        self.assertFalse(result['audio_comparison']['aac_payloads_equal'])
        shifted = self.root / 'shifted.mp4'
        command(['ffmpeg', '-v', 'error', '-n', '-i', str(self.source), '-itsoffset', '0.1',
                 '-i', str(self.source), '-map', '0:v:0', '-map', '1:a:0', '-c', 'copy', str(shifted)])
        code, result = invoke('inspect', shifted, '--audio-baseline', self.source)
        self.assertEqual(code, 1)
        self.assertTrue(result['audio_comparison']['aac_payloads_equal'])
        self.assertFalse(result['audio_comparison']['aac_timing_and_skip_metadata_equal'])

    def test_variable_frame_timing_is_not_silently_normalized(self):
        vfr = self.root / 'vfr.mp4'
        command(['ffmpeg', '-v', 'error', '-n', '-i', str(self.source), '-an', '-vf',
                 'select=not(eq(n\\,12))', '-fps_mode', 'vfr', '-c:v', 'libx264', str(vfr)])
        video = media.one_video(media.probe(vfr))
        output = self.root / 'vfr-cut.mp4'
        code, _ = invoke('extract', vfr, output, '--fps', video['avg_frame_rate'],
                         '--start-frame', 0, '--end-frame', 24)
        self.assertEqual(code, 2)
        self.assertFalse(output.exists())
        coarse = self.root / 'coarse-vfr.mp4'
        command(['ffmpeg', '-v', 'error', '-n', '-f', 'lavfi', '-i',
                 'testsrc2=size=160x120:rate=24:duration=2', '-vf',
                 'select=not(eq(n\\,12))', '-fps_mode', 'vfr', '-c:v', 'libx264',
                 '-video_track_timescale', '24', str(coarse)])
        code, result = invoke('inspect', coarse)
        self.assertEqual(code, 1)
        self.assertFalse(result['checks']['constant_frame_timestamps'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
