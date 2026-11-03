// Static file server rooted at the project folder (so /render, /data and /brand are reachable).
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = fs.realpathSync(path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..'));
const TYPES = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.json': 'application/json', '.bin': 'application/octet-stream', '.png': 'image/png',
  '.jpg': 'image/jpeg', '.ttf': 'font/ttf', '.otf': 'font/otf', '.woff2': 'font/woff2',
  '.css': 'text/css', '.svg': 'image/svg+xml',
};

export function serve(port = 0) {
  return new Promise((resolve, reject) => {
    const server = http.createServer((req, res) => {
      let file;
      try {
        file = path.join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname));
        if (file.includes('\0')) throw new Error('null byte');
      }
      catch { res.writeHead(400); res.end('bad path'); return; }
      fs.realpath(file, (err, realFile) => {
        if (err) { res.writeHead(404); res.end('not found'); return; }
        const rel = path.relative(ROOT, realFile);
        if (rel === '..' || rel.startsWith('..' + path.sep) || path.isAbsolute(rel)) { res.writeHead(403); res.end(); return; }
        fs.stat(realFile, (err, st) => {
          if (err || !st.isFile()) { res.writeHead(404); res.end('not found'); return; }
          res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-cache' });
          fs.createReadStream(realFile).on('error', () => res.destroy()).pipe(res);
        });
      });
    });
    server.once('error', reject);
    server.listen(port, '127.0.0.1', () => resolve(server));
  });
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const s = await serve(Number(process.argv[2] || 8765));
  console.log(`serving ${ROOT} on http://127.0.0.1:${s.address().port}/render/index.html`);
}
