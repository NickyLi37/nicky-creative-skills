#!/usr/bin/env python3
"""Silent frame cuts and read-only delivery checks. Python 3.10+, FFmpeg/ffprobe."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from fractions import Fraction
from pathlib import Path


def run(args):
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode:
        raise ValueError(p.stderr.strip()[-4000:] or f'{args[0]} exited {p.returncode}')
    return p.stdout


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def ratio(value):
    try:
        return Fraction(str(value).replace(':', '/'))
    except (ValueError, ZeroDivisionError) as error:
        raise ValueError(f'Invalid ratio: {value}') from error


def probe(path):
    if not path.is_file():
        raise ValueError(f'Input is not a file: {path}')
    return json.loads(run(['ffprobe', '-v', 'error', '-show_streams', '-show_format',
                           '-of', 'json', str(path)]))


def one_video(info):
    videos = [s for s in info['streams'] if s['codec_type'] == 'video']
    if len(videos) != 1:
        raise ValueError('Exactly one video stream is required; select the intended stream first.')
    return videos[0]


def packets(path, selector, hashes=False):
    return json.loads(run(['ffprobe', '-v', 'error', '-select_streams', selector,
        '-show_packets', *(['-show_data_hash', 'sha256'] if hashes else []),
        '-show_entries', 'packet=pts,dts,duration,data_hash,side_data_list',
        '-of', 'json', str(path)]))['packets']


def timeline(path, video):
    fps, tb = ratio(video['avg_frame_rate']), ratio(video['time_base'])
    if fps <= 0 or tb <= 0:
        raise ValueError('A positive frame rate and time base are required.')
    ps = packets(path, 'v:0')
    if not ps or any('pts' not in p for p in ps):
        raise ValueError('Every video packet must have a presentation timestamp.')
    pts = sorted(Fraction(int(p['pts'])) * tb for p in ps)
    if any(b <= a for a, b in zip(pts, pts[1:])):
        raise ValueError('Video frame presentation timestamps must be strictly increasing.')
    error = max(abs(t - pts[0] - Fraction(i, 1) / fps) for i, t in enumerate(pts))
    # A coarse container tick must not hide a frame-length timing change.
    tolerance = min(tb, Fraction(1, 4) / fps)
    return fps, pts, tb, error, tolerance


def audio_compare(path, info, baseline):
    other = probe(baseline)
    streams = [[s for s in x['streams'] if s['codec_type'] == 'audio'] for x in [info, other]]
    if any(len(s) != 1 or s[0]['codec_name'] != 'aac' for s in streams):
        raise ValueError('AAC equality requires exactly one AAC stream in each file.')
    current, original = [s[0] for s in streams]
    a, b = packets(path, 'a:0', True), packets(baseline, 'a:0', True)
    def normalized(items, stream):
        tb = ratio(stream['time_base'])
        return [{**{k: str(Fraction(int(p[k])) * tb) if k in p else None
                    for k in ['pts', 'dts', 'duration']},
                 'side_data_list': p.get('side_data_list', [])} for p in items]
    fields = ['codec_name', 'profile', 'sample_rate', 'channels', 'channel_layout']
    checks = {
        'aac_payloads_equal': bool(a) and [p['data_hash'] for p in a] == [p['data_hash'] for p in b],
        'aac_timing_and_skip_metadata_equal': normalized(a, current) == normalized(b, original),
        'aac_codec_parameters_equal': all(current.get(k) == original.get(k) for k in fields),
    }
    return checks, {'baseline_sha256': digest(baseline), 'packet_count': len(a),
                    'baseline_packet_count': len(b), **checks}


def inspect(path, expected_fps=None, expected_frames=None, aspect=None, baseline=None):
    info = probe(path); v = one_video(info)
    fps, pts, tb, error, tolerance = timeline(path, v)
    # Decode once with passthrough timing: FFmpeg's final frame counter is independent of container counts.
    progress = run(['ffmpeg', '-v', 'error', '-xerror', '-nostdin', '-i', str(path),
        '-map', '0:v:0', '-map', '0:a?', '-fps_mode', 'passthrough', '-progress', 'pipe:1',
        '-nostats', '-f', 'null', '-'])
    decoded = int([line.split('=', 1)[1] for line in progress.splitlines() if line.startswith('frame=')][-1])
    sar = v.get('sample_aspect_ratio')
    display_aspect = Fraction(v['width'], v['height']) * ratio(sar) if sar and sar != 'N/A' else None
    duration = ratio(v['duration']) if v.get('duration') not in [None, 'N/A'] else None
    checks = {'full_decode': True, 'decoded_frame_and_packet_counts_equal': decoded == len(pts),
              'constant_frame_timestamps': error <= tolerance, 'video_starts_at_zero': abs(pts[0]) <= tolerance,
              'duration_matches_frame_count': duration is not None and abs(duration - Fraction(decoded, 1) / fps) <= max(tb, Fraction(1, 1000000))}
    if expected_fps is not None: checks['expected_fps'] = fps == expected_fps
    if expected_frames is not None: checks['expected_frames'] = decoded == expected_frames
    if aspect is not None: checks['expected_display_aspect'] = display_aspect == aspect
    audio = None
    if baseline:
        audio_checks, audio = audio_compare(path, info, baseline); checks.update(audio_checks)
    return {'status': 'passed' if all(checks.values()) else 'failed', 'sha256': digest(path),
            'width': v['width'], 'height': v['height'], 'sample_aspect_ratio': sar,
            'display_aspect_ratio': str(display_aspect) if display_aspect else None,
            'fps': str(fps), 'frames': decoded, 'duration_seconds': float(duration) if duration else None,
            'max_frame_timestamp_error_seconds': float(error),
            'frame_timestamp_tolerance_seconds': float(tolerance),
            'audio_streams': sum(s['codec_type'] == 'audio' for s in info['streams']),
            'checks': checks, 'audio_comparison': audio,
            'limits': 'Technical checks do not prove identity, choreography, visual quality, or browser playback.'}


def extract(source, output, fps, start, end):
    if start < 0 or end <= start or fps <= 0:
        raise ValueError('Use positive fps and 0 <= start-frame < end-frame (exclusive).')
    if output.exists() or output.is_symlink():
        raise ValueError(f'Will not overwrite: {output}')
    if output.suffix.lower() != '.mp4':
        raise ValueError('Reference output must end in .mp4.')
    v = one_video(probe(source)); actual_fps, pts, tb, error, tolerance = timeline(source, v)
    if actual_fps != fps or error > tolerance:
        raise ValueError('Source is not CFR at the requested fps. Align/normalize it explicitly; no implicit retiming.')
    if end > len(pts):
        raise ValueError(f'End frame {end} exceeds source frame count {len(pts)}.')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.mv-recast-', dir=output.parent) as tmp:
        clip = Path(tmp) / 'cut.mp4'
        run(['ffmpeg', '-v', 'error', '-nostdin', '-n', '-i', str(source), '-map', '0:v:0', '-an',
             '-vf', f'trim=start_frame={start}:end_frame={end},setpts=PTS-STARTPTS',
             '-frames:v', str(end-start), '-fps_mode', 'passthrough', '-c:v', 'libx264',
             '-preset', 'fast', '-crf', '16', '-pix_fmt', 'yuv420p',
             '-video_track_timescale', str(fps.numerator), '-movflags', '+faststart', str(clip)])
        result = inspect(clip, fps, end-start)
        if result['status'] != 'passed' or result['audio_streams'] != 0:
            raise ValueError(f'Extracted reference failed validation: {result}')
        # Atomic no-clobber installation, including a competing writer between the initial check and completion.
        os.link(clip, output)
    result.update(source_sha256=digest(source), start_frame=start, end_frame_exclusive=end,
                  source_start_seconds=str(Fraction(start, 1)/fps),
                  output_file=str(output), audio_policy='silent reference; original master untouched')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    cut = sub.add_parser('extract', help='Extract a silent CFR reference; frame indices are zero-based and end-exclusive.')
    cut.add_argument('input', type=Path); cut.add_argument('output', type=Path)
    cut.add_argument('--fps', type=ratio, required=True, help='Exact source rate, for example 24 or 24000/1001.')
    cut.add_argument('--start-frame', type=int, required=True); cut.add_argument('--end-frame', type=int, required=True)
    check = sub.add_parser('inspect', help='Fully decode and check a final export without changing it.')
    check.add_argument('input', type=Path); check.add_argument('--fps', type=ratio)
    check.add_argument('--frames', type=int); check.add_argument('--aspect', type=ratio, help='Display ratio, for example 4:3.')
    check.add_argument('--audio-baseline', type=Path, help='Compare one AAC stream: payloads, timing, codec, and skip metadata.')
    for p in [cut, check]: p.add_argument('--report', type=Path, help='New JSON file; never overwrites an existing file.')
    args = parser.parse_args()
    try:
        if args.report and (args.report.exists() or args.report.is_symlink()):
            raise ValueError(f'Will not overwrite report: {args.report}')
        if args.report and args.command == 'extract' and args.report.resolve() == args.output.resolve():
            raise ValueError('The report and video output must be different files.')
        if args.command == 'extract':
            result = extract(args.input, args.output, args.fps, args.start_frame, args.end_frame)
        else:
            result = inspect(args.input, args.fps, args.frames, args.aspect, args.audio_baseline)
        text = json.dumps(result, indent=2, ensure_ascii=False) + '\n'
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            with args.report.open('x', encoding='utf-8') as f: f.write(text)
        print(text, end='')
        return 0 if result['status'] == 'passed' else 1
    except (ValueError, OSError, KeyError, IndexError, ZeroDivisionError) as error:
        print(json.dumps({'status': 'error', 'error': str(error)}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
