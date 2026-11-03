// Lay the natural-speed narration lines (vo/v4/lines: round 5: the poem is the plain narration take) on a film-length track at their frames (render/src/vo.js).
// Usage: node vo/build_vo.mjs  ->  vo/vo_track.wav (48 kHz stereo)
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { VO, FILM_END } from '../render/src/vo.js';

const dir = path.dirname(fileURLToPath(import.meta.url));
const dur = (FILM_END / 24).toFixed(3);
const args = ['-y', '-loglevel', 'error'];
const chains = [];
VO.forEach(([f0], i) => {
  args.push('-i', path.join(dir, 'v4', 'lines', `${String(i).padStart(2, '0')}.wav`));
  const ms = Math.round((f0 / 24) * 1000);
  chains.push(`[${i}:a]aresample=48000,adelay=${ms}:all=1[l${i}]`);
});
// light presence lift and gentle levelling so the voice sits on the score without a deep duck
const mix = VO.map((_, i) => `[l${i}]`).join('') + `amix=inputs=${VO.length}:normalize=0:dropout_transition=0,`
  + 'highpass=f=75,equalizer=f=3200:t=q:w=1.1:g=2,equalizer=f=220:t=q:w=1:g=-1.5,'
  + 'acompressor=threshold=-24dB:ratio=2.5:attack=8:release=180:makeup=2,'
  + `apad=whole_dur=${dur},atrim=0:${dur},pan=stereo|c0=c0|c1=c0[vo]`;
args.push('-filter_complex', [...chains, mix].join(';'), '-map', '[vo]', '-ar', '48000', path.join(dir, 'vo_track.wav'));
execFileSync('ffmpeg', args, { stdio: 'inherit' });
console.log(`vo_track.wav written (${dur} s)`);
