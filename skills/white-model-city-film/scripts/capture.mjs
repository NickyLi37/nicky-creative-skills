// Deterministic frame capture from a page that exposes window.renderFrame(f) and sets window.ready = true.
// Each frame is rendered from its number only; existing PNGs are skipped, so a stopped run resumes where it was.
//
// node capture.mjs --root <project dir> --page render/index.html --out out/frames
//                  [--from 0 --to 6190 | --frames 100,2400] [--scale 0.5|1|2] [--workers 4] [--width 1920 --height 1080]
//
// --scale is the device pixel ratio over the CSS layout: 0.5 = 960x540 preview, 2 = 3840x2160 (4K).
// Frames are dealt round-robin to the workers, so the frames come out roughly in order.
// Needs: npm i playwright-core, plus a local Google Chrome (channel 'chrome').
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright-core';
import { serve } from './server.mjs';

const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) => (v.startsWith('--') ? [...a, [v.slice(2), arr[i + 1]]] : a), []));
const root = path.resolve(args.root || '.');
const page = args.page || 'render/index.html';
const out = path.resolve(args.out || 'frames');
const scale = Number(args.scale || 1), workers = Number(args.workers || 1);
const W = Number(args.width || 1920), H = Number(args.height || 1080);
const name = (f) => path.join(out, `f${String(f).padStart(5, '0')}.png`);

let frames;
if (args.frames) frames = args.frames.split(',').map(Number);
else {
  const a = Number(args.from || 0), b = Number(args.to);
  if (!Number.isFinite(b)) { console.error('--to <exclusive end frame> or --frames is required'); process.exit(1); }
  frames = Array.from({ length: b - a }, (_, i) => a + i);
}
fs.mkdirSync(out, { recursive: true });
const todo = frames.filter((f) => !fs.existsSync(name(f)));

const server = await serve(root, 0);
const url = `http://127.0.0.1:${server.address().port}/${page}`;
const gpu = ['--enable-gpu', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader'];
if (process.platform === 'darwin') gpu.unshift('--use-angle=metal');
const browser = await chromium.launch({ channel: 'chrome', headless: true, args: gpu });

async function worker(list, id) {
  const p = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: scale });
  p.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') console.log(`[w${id}] ${m.type()}: ${m.text()}`); });
  p.on('pageerror', (e) => console.log(`[w${id}] pageerror: ${e.message}`));
  await p.goto(url);
  await p.waitForFunction(() => window.ready === true, null, { timeout: 180000 });
  const t0 = Date.now();
  for (const [i, f] of list.entries()) {
    await p.evaluate((fr) => window.renderFrame(fr), f);
    await p.screenshot({ path: name(f), clip: { x: 0, y: 0, width: W, height: H } });
    if (i % 24 === 0) console.log(`[w${id}] f${f} (${i + 1}/${list.length}) ${((Date.now() - t0) / (i + 1) / 1000).toFixed(2)} s/frame`);
  }
  await p.close();
}

const chunks = Array.from({ length: workers }, (_, w) => todo.filter((_, i) => i % workers === w));
await Promise.all(chunks.map((c, i) => worker(c, i)));
await browser.close();
server.close();
console.log(`done: ${todo.length} frames -> ${out}`);
