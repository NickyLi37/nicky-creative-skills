// Writes the bilingual subtitles as SRT (Chinese line over English line), from timeline.js.
import fs from 'node:fs';
import { SUBS, FPS } from './src/timeline.js';
const ts = (f) => { const ms = Math.round((f / FPS) * 1000); const p = (n, w = 2) => String(n).padStart(w, '0');
  return `${p(Math.floor(ms / 3600000))}:${p(Math.floor(ms / 60000) % 60)}:${p(Math.floor(ms / 1000) % 60)},${p(ms % 1000, 3)}`; };
const out = SUBS.map(([a, b, cn, en], i) => `${i + 1}\n${ts(a)} --> ${ts(b)}\n${cn}\n${en}\n`).join('\n');
fs.writeFileSync(process.argv[2], out);
console.log(`${SUBS.length} cues -> ${process.argv[2]}`);
