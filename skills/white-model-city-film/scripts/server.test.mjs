// Run: node --test scripts/server.test.mjs
import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import test from 'node:test';
import { serve } from './server.mjs';

function request(server, url) {
  return new Promise((resolve, reject) => {
    http.get({ hostname: '127.0.0.1', port: server.address().port, path: url }, (res) => {
      let body = '';
      res.setEncoding('utf8');
      res.on('data', (chunk) => { body += chunk; });
      res.on('end', () => resolve({ status: res.statusCode, body }));
    }).on('error', reject);
  });
}

for (const kind of ['generic', 'suzhou']) {
  test(`${kind} server serves only its root and survives malformed paths`, async () => {
    const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'city-film-server-'));
    let server;
    try {
      const root = path.join(temp, 'public');
      fs.mkdirSync(path.join(root, 'render'), { recursive: true });
      fs.mkdirSync(path.join(temp, 'public-private'));
      fs.writeFileSync(path.join(root, 'hello.txt'), 'hello');
      fs.writeFileSync(path.join(temp, 'public-private', 'secret.txt'), 'private');
      fs.symlinkSync(path.join(temp, 'public-private'), path.join(root, 'outside'));
      if (kind === 'generic') server = await serve(root);
      else {
        const file = path.join(root, 'render', 'server.mjs');
        fs.copyFileSync(new URL('../example/suzhou/render/server.mjs', import.meta.url), file);
        server = await (await import(pathToFileURL(file).href)).serve();
      }
      assert.deepEqual(await request(server, '/hello.txt'), { status: 200, body: 'hello' });
      assert.equal((await request(server, '/%2e%2e%2fpublic-private%2fsecret.txt')).status, 403);
      assert.equal((await request(server, '/outside/secret.txt')).status, 403);
      assert.equal((await request(server, '/%ZZ')).status, 400);
      assert.equal((await request(server, '/%00')).status, 400);
      assert.equal((await request(server, '/missing')).status, 404);
      assert.equal((await request(server, '/hello.txt')).status, 200);
    } finally {
      if (server) await new Promise((resolve) => server.close(resolve));
      fs.rmSync(temp, { recursive: true, force: true });
    }
  });
}
