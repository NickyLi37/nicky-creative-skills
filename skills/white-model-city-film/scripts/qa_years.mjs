// Check that what the narration says matches what the HUD shows: for every subtitle that names a year,
// print the year ticker at the start, middle and end of the line.
// Usage: node qa_years.mjs --timeline render/src/timeline.js [--match 年|year]
// The timeline module must export SUBS ([[f0, f1, cn, en]] in film frames) and stateAt(f) returning { year }.
// After any re-timing of the narration, a line like "four years later" can land before the ticker moves.
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) => (v.startsWith('--') ? [...a, [v.slice(2), arr[i + 1]]] : a), []));
const { SUBS, stateAt, FPS = 24 } = await import(pathToFileURL(path.resolve(args.timeline)).href);
const re = new RegExp(args.match || '\\d{3,4}|年|year', 'i');
for (const [a, b, cn, en] of SUBS) {
  if (!re.test(cn) && !re.test(en)) continue;
  const ys = [a, Math.round((a + b) / 2), b - 1].map((f) => stateAt(f).year);
  console.log(`${(a / FPS).toFixed(1).padStart(6)} s  year ${ys.join(' / ').padEnd(18)} ${cn}`);
}
