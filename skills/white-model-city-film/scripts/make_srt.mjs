// Bilingual SRT (Chinese line over English line) from the timeline's SUBS: [[f0, f1, cn, en], ...] in film frames.
// Usage: node make_srt.mjs --timeline render/src/timeline.js --out out/film.srt
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) => (v.startsWith('--') ? [...a, [v.slice(2), arr[i + 1]]] : a), []));
const { SUBS, FPS = 24 } = await import(pathToFileURL(path.resolve(args.timeline)).href);
const ts = (f) => {
  const ms = Math.round((f / FPS) * 1000), p = (n, w = 2) => String(n).padStart(w, '0');
  return `${p(Math.floor(ms / 3600000))}:${p(Math.floor(ms / 60000) % 60)}:${p(Math.floor(ms / 1000) % 60)},${p(ms % 1000, 3)}`;
};
fs.writeFileSync(args.out, SUBS.map(([a, b, cn, en], i) => `${i + 1}\n${ts(a)} --> ${ts(b)}\n${cn}\n${en}\n`).join('\n'));
console.log(`${SUBS.length} cues -> ${args.out}`);
