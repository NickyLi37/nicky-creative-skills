// Frame capture: node capture.mjs --out <dir> [--from 0 --to 3960 | --frames 1300,1500] [--scale 1.3333] [--workers 2]
// Deterministic: each frame is rendered from its number only; existing PNGs are skipped (resumable).
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright-core';
import { serve } from './server.mjs';

const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) => (v.startsWith('--') ? [...a, [v.slice(2), arr[i + 1]]] : a), []));
const out = path.resolve(args.out || 'frames');
const scale = Number(args.scale || 1);
const workers = Number(args.workers || 1);
let frames;
if (args.frames) frames = args.frames.split(',').map(Number);
else { const a = Number(args.from || 0), b = Number(args.to || 3960); frames = Array.from({ length: b - a }, (_, i) => a + i); }
fs.mkdirSync(out, { recursive: true });
const todo = frames.filter((f) => !fs.existsSync(path.join(out, `f${String(f).padStart(5, '0')}.png`)));

const server = await serve(0);
const url = `http://127.0.0.1:${server.address().port}/render/index.html`;
const browser = await chromium.launch({ channel: 'chrome', headless: true, args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader'] });

async function worker(list, id) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: scale });
  page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') console.log(`[w${id}] ${m.type()}: ${m.text()}`); });
  page.on('pageerror', (e) => console.log(`[w${id}] pageerror: ${e.message}`));
  await page.goto(url);
  await page.waitForFunction(() => window.ready === true, null, { timeout: 180000 });
  const t0 = Date.now();
  for (const [i, f] of list.entries()) {
    await page.evaluate((fr) => window.renderFrame(fr), f);
    await page.screenshot({ path: path.join(out, `f${String(f).padStart(5, '0')}.png`), clip: { x: 0, y: 0, width: 1920, height: 1080 } });
    if (i % 24 === 0) console.log(`[w${id}] f${f} (${i + 1}/${list.length}) ${((Date.now() - t0) / (i + 1) / 1000).toFixed(2)} s/frame`);
  }
  await page.close();
}

const chunks = Array.from({ length: workers }, (_, w) => todo.filter((_, i) => i % workers === w));
await Promise.all(chunks.map((c, i) => worker(c, i)));
await browser.close();
server.close();
console.log(`done: ${todo.length} frames -> ${out}`);
