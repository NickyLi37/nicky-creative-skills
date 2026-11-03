// Lay the narration lines on a film-length track at the frames planned by plan_warp.py.
// Usage: node build_vo.mjs --vo render/src/vo.js --lines vo/lines --out vo/vo_track.wav [--fps 24]
// Line i is read from <lines>/NN.wav (two digits). Output: 48 kHz stereo, with a light presence lift and gentle
// levelling so the voice sits on the score without a deep duck.
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) => (v.startsWith('--') ? [...a, [v.slice(2), arr[i + 1]]] : a), []));
if (!args.vo || !args.lines || !args.out) { console.error('usage: build_vo.mjs --vo vo.js --lines <dir> --out vo_track.wav [--fps 24]'); process.exit(1); }
const fps = Number(args.fps || 24);
const { VO, FILM_END } = await import(pathToFileURL(path.resolve(args.vo)).href);
const dur = (FILM_END / fps).toFixed(3);
const ff = ['-y', '-loglevel', 'error'];
const chains = [];
VO.forEach(([f0], i) => {
  ff.push('-i', path.join(args.lines, `${String(i).padStart(2, '0')}.wav`));
  chains.push(`[${i}:a]aresample=48000,adelay=${Math.round((f0 / fps) * 1000)}:all=1[l${i}]`);
});
const mix = VO.map((_, i) => `[l${i}]`).join('') + `amix=inputs=${VO.length}:normalize=0:dropout_transition=0,`
  + 'highpass=f=75,equalizer=f=3200:t=q:w=1.1:g=2,equalizer=f=220:t=q:w=1:g=-1.5,'
  + 'acompressor=threshold=-24dB:ratio=2.5:attack=8:release=180:makeup=2,'
  + `apad=whole_dur=${dur},atrim=0:${dur},pan=stereo|c0=c0|c1=c0[vo]`;
ff.push('-filter_complex', [...chains, mix].join(';'), '-map', '[vo]', '-ar', '48000', args.out);
execFileSync('ffmpeg', ff, { stdio: 'inherit' });
console.log(`${args.out} written (${dur} s, ${VO.length} lines)`);
