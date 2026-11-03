// Geometry helpers. Local metres (x east, y north) map to three as X = x, Z = -y, Y = up.
import * as THREE from 'three';

export const toXZ = (x, y) => [x, -y];

// Mitred ribbon offsets for a 2D polyline; returns [left, right] point arrays.
function ribbonSides(pts, half) {
  const n = pts.length, L = [], R = [];
  for (let i = 0; i < n; i++) {
    const p = pts[i], a = pts[Math.max(0, i - 1)], b = pts[Math.min(n - 1, i + 1)];
    let dx = b[0] - a[0], dy = b[1] - a[1];
    const len = Math.hypot(dx, dy) || 1;
    dx /= len; dy /= len;
    let nx = -dy, ny = dx;
    let scale = 1;
    if (i > 0 && i < n - 1) {
      // mitre against the incoming segment, capped
      let ix = p[0] - a[0], iy = p[1] - a[1];
      const il = Math.hypot(ix, iy) || 1; ix /= il; iy /= il;
      const dot = nx * -iy + ny * ix;
      scale = Math.min(3, 1 / Math.max(0.33, Math.abs(dot)));
    }
    L.push([p[0] + nx * half * scale, p[1] + ny * half * scale]);
    R.push([p[0] - nx * half * scale, p[1] - ny * half * scale]);
  }
  return [L, R];
}

// Build one merged ribbon geometry from many polylines.
// lines: [{pts:[[x,y]...], width, attrs:{name: number}}], y = height above ground.
// Optional ptsB per line -> second position set in attribute 'posB' (for morphing).
export function ribbons(lines, y = 0.5, extraAttrNames = []) {
  let nv = 0, ni = 0;
  for (const l of lines) { if (l.pts.length >= 2) { nv += l.pts.length * 2; ni += (l.pts.length - 1) * 6; } }
  const pos = new Float32Array(nv * 3), posB = new Float32Array(nv * 3), u = new Float32Array(nv), side = new Float32Array(nv);
  const extras = Object.fromEntries(extraAttrNames.map((k) => [k, new Float32Array(nv)]));
  const idx = new Uint32Array(ni);
  let v = 0, k = 0;
  for (const l of lines) {
    const n = l.pts.length;
    if (n < 2) continue;
    const [La, Ra] = ribbonSides(l.pts, l.width / 2);
    const [Lb, Rb] = ribbonSides(l.ptsB || l.pts, l.width / 2);
    // arc length for u
    const acc = [0];
    for (let i = 1; i < n; i++) acc.push(acc[i - 1] + Math.hypot(l.pts[i][0] - l.pts[i - 1][0], l.pts[i][1] - l.pts[i - 1][1]));
    const total = acc[n - 1] || 1;
    const base = v;
    for (let i = 0; i < n; i++) {
      for (const [s, A, B] of [[0, La[i], Lb[i]], [1, Ra[i], Rb[i]]]) {
        pos.set([A[0], y, -A[1]], v * 3);
        posB.set([B[0], y, -B[1]], v * 3);
        u[v] = acc[i] / total;
        side[v] = s;
        for (const name of extraAttrNames) extras[name][v] = l.attrs?.[name] ?? 0;
        v++;
      }
    }
    for (let i = 0; i < n - 1; i++) {
      const a = base + i * 2, b = a + 1, c = a + 2, d = a + 3;
      idx.set([a, c, b, b, c, d], k); k += 6;
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('posB', new THREE.BufferAttribute(posB, 3));
  g.setAttribute('aU', new THREE.BufferAttribute(u, 1));
  g.setAttribute('aSide', new THREE.BufferAttribute(side, 1));
  for (const name of extraAttrNames) g.setAttribute(name, new THREE.BufferAttribute(extras[name], 1));
  g.setIndex(new THREE.BufferAttribute(idx, 1));
  g.computeBoundingSphere();
  g.boundingSphere.radius *= 2; // morph targets may move outside the base sphere
  return g;
}

// Polygons with holes -> one merged flat geometry at height y.
export function polygons(polys, y = 0) {
  const geoms = [];
  for (const rings of polys) {
    const outer = rings[0];
    if (!outer || outer.length < 4) continue;
    const shape = new THREE.Shape(outer.map(([x, yy]) => new THREE.Vector2(x, yy)));
    for (const h of rings.slice(1)) if (h.length >= 4) shape.holes.push(new THREE.Path(h.map(([x, yy]) => new THREE.Vector2(x, yy))));
    const g = new THREE.ShapeGeometry(shape);
    g.rotateX(-Math.PI / 2); // (x, y) -> (x, 0, -y)
    g.translate(0, y, 0);
    geoms.push(g);
  }
  return merge(geoms);
}

export function merge(geoms) {
  let nv = 0, ni = 0;
  for (const g of geoms) { nv += g.attributes.position.count; ni += g.index ? g.index.count : g.attributes.position.count; }
  const pos = new Float32Array(nv * 3), idx = new Uint32Array(ni);
  let v = 0, k = 0;
  for (const g of geoms) {
    pos.set(g.attributes.position.array, v * 3);
    if (g.index) { for (let i = 0; i < g.index.count; i++) idx[k++] = g.index.array[i] + v; }
    else { for (let i = 0; i < g.attributes.position.count; i++) idx[k++] = v + i; }
    v += g.attributes.position.count;
    g.dispose();
  }
  const out = new THREE.BufferGeometry();
  out.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  out.setIndex(new THREE.BufferAttribute(idx, 1));
  out.computeVertexNormals();
  out.computeBoundingSphere();
  return out;
}
