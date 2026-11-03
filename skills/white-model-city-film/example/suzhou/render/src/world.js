// Scene content: board, water, roads, buildings, landmarks, thematic layers. apply(state) drives it per frame.
import * as THREE from 'three';
import { ribbons, polygons } from './geo.js';
import { revealFrame, RISE } from './timeline.js';

const C = (hex) => new THREE.Color(hex);
const PAL = {
  ground: C('#6E6F72'), groundStone: C('#141518'),
  bld: C('#E9E7E2'), bldStone: C('#1C1D21'),
  water: C('#3E5560'), waterStone: C('#22252A'),
  road: C('#808185'), roadStone: C('#18191C'),
  line: C('#F2EEE4'), canal: C('#6FD6E6'), street: C('#E8C36A'), match: C('#BFF7FF'),
  flow: C('#5AC8D8'), bronze: C('#C9A15A'), cinnabar: C('#D8483E'), lamp: C('#FFB867'),
  jade: C('#4FA387'), ember: C('#E9672B'), char: C('#2A2624'), gray: C('#8A8B8E'),
  wallWhite: C('#F4F1EA'), roof: C('#4A5058'), indigo: C('#3B5B8C'), gold: C('#E8D9B0'),
  rice: C('#E0C46A'), riceGreen: C('#7FA36B'), lost: C('#E9E2D2'),
};
const mixC = (a, b, t) => a.clone().lerp(b, t);

// Board extent in local metres (matches prep/common.py BBOX).
export const EXTENT = { x0: -12200, x1: 20200, y0: -8420, y1: 12660 };

async function getJSON(url) { const r = await fetch(url); if (!r.ok) throw new Error(url + ' ' + r.status); return r.json(); }

// Shared raster field: R wave distance, G moat distance, B Shantang corridor, A water mask.
const FIELD_GLSL = `
  uniform sampler2D uField; uniform vec4 uFieldBox;
  vec4 fieldAt(vec2 xy) { return texture2D(uField, (xy - uFieldBox.xy) / uFieldBox.zw); }`;

export async function buildWorld(scene, renderer) {
  const W = {};
  scene.background = new THREE.Color('#050506');
  const film = await getJSON('/data/layers/film.json');
  W.film = film;

  // ---- field texture
  const fm = film.field;
  const fbuf = await (await fetch('/data/layers/field.bin')).arrayBuffer();
  const ftex = new THREE.DataTexture(new Float32Array(fbuf), fm.nx, fm.ny, THREE.RGBAFormat, THREE.FloatType);
  const linear = renderer.extensions.has('OES_texture_float_linear');
  ftex.minFilter = ftex.magFilter = linear ? THREE.LinearFilter : THREE.NearestFilter;
  ftex.needsUpdate = true;
  W.fieldU = { uField: { value: ftex }, uFieldBox: { value: new THREE.Vector4(fm.x0, fm.y0, fm.nx * fm.cell, fm.ny * fm.cell) } };

  // ---- lights
  const hemi = new THREE.HemisphereLight('#e4e9f0', '#3a3b3e', 1.15);
  scene.add(hemi);
  const sun = new THREE.DirectionalLight('#fff4e6', 2.4);
  sun.castShadow = true;
  sun.shadow.mapSize.set(4096, 4096);
  sun.shadow.bias = -0.0004;
  sun.shadow.normalBias = 0.6;
  scene.add(sun, sun.target);
  W.sun = sun; W.hemi = hemi;

  // ---- board slab
  const bw = EXTENT.x1 - EXTENT.x0, bd = EXTENT.y1 - EXTENT.y0;
  const boardMat = new THREE.MeshStandardMaterial({ color: PAL.ground, roughness: 0.92, metalness: 0 });
  const board = new THREE.Mesh(new THREE.BoxGeometry(bw, 360, bd), boardMat);
  board.position.set((EXTENT.x0 + EXTENT.x1) / 2, -180, -(EXTENT.y0 + EXTENT.y1) / 2);
  board.receiveShadow = true;
  scene.add(board);
  W.boardMat = boardMat;

  // ---- water (wave / moat / glow driven by the field)
  const water = await getJSON('/data/layers/water.json');
  W.waterU = { uWave: { value: 0 }, uWaveOn: { value: 0 }, uMoat: { value: 0 }, uGlow: { value: 0 },
    cFlow: { value: PAL.flow }, cGlow: { value: PAL.canal } };
  const waterMat = new THREE.MeshStandardMaterial({ color: PAL.water, roughness: 0.32, metalness: 0.0, side: THREE.DoubleSide,
    polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
  waterMat.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, W.fieldU, W.waterU);
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec2 vXY;')
      .replace('#include <project_vertex>', '#include <project_vertex>\n vec4 wp_ = modelMatrix * vec4(transformed, 1.0); vXY = vec2(wp_.x, -wp_.z);');
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', `#include <common>
        varying vec2 vXY; ${FIELD_GLSL}
        uniform float uWave, uWaveOn, uMoat, uGlow; uniform vec3 cFlow, cGlow;`)
      .replace('#include <color_fragment>', `#include <color_fragment>
        vec4 fd_ = fieldAt(vXY);
        float lit_ = uWaveOn * smoothstep(uWave + 60.0, uWave - 500.0, fd_.r);
        float band_ = uWaveOn * exp(-abs(fd_.r - uWave) / 160.0) * step(fd_.r, uWave + 80.0);
        diffuseColor.rgb *= 1.0 - 0.55 * uWaveOn * (1.0 - lit_);`)
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
        totalEmissiveRadiance += cFlow * (lit_ * 0.5 + band_ * 2.6)
          + cFlow * uMoat * smoothstep(120.0, 45.0, fd_.g) * 1.5 + cGlow * uGlow;`);
  };
  const wArea = new THREE.Mesh(polygons(water.areas.map((a) => a.rings), 0.6), waterMat);
  wArea.receiveShadow = true;
  const widthOf = (k) => ({ river: 22, canal: 14, stream: 7, drain: 5, ditch: 4 }[k] || 6);
  const wLines = new THREE.Mesh(ribbons(water.lines.map((l) => ({ pts: l.pts, width: widthOf(l.kind) })), 0.7), waterMat);
  wLines.receiveShadow = true;
  scene.add(wArea, wLines);
  W.waterMat = waterMat;

  // ---- roads + old-city streets
  const roads = await getJSON('/data/layers/roads.json');
  const roadMat = new THREE.MeshStandardMaterial({ color: PAL.road, roughness: 0.95, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1 });
  const rw = [5, 8, 11, 14, 18, 22];
  const roadMesh = new THREE.Mesh(ribbons([
    ...roads.roads.map((r) => ({ pts: r.pts, width: rw[r.rank] || 6 })),
    ...roads.streets.map((s) => ({ pts: s.pts, width: s.hw === 'footway' || s.hw === 'path' ? 2.5 : 4.5 })),
  ], 0.35), roadMat);
  roadMesh.receiveShadow = true;
  scene.add(roadMesh);
  W.roadMat = roadMat; W.roadMesh = roadMesh;

  // ---- buildings (CMAB)
  W.bldU = {
    uGrow: { value: 1 }, uYear: { value: 2030 }, uZoneGrow: { value: new THREE.Vector4(1, 1, 1, 1) }, uCorrGrow: { value: 0 },
    uStory: { value: 0 }, uRevealAll: { value: 1 },
    uOldTint: { value: 0 }, uRoof: { value: 0 }, uGray: { value: 0 }, uNewTint: { value: 0 }, uFresh: { value: 0 },
    uRamp: { value: 0 }, uDim: { value: 0 }, uFire: { value: 0 }, uFireOn: { value: 0 },
    cOld: { value: PAL.wallWhite }, cRoof: { value: PAL.roof }, cGray: { value: PAL.gray }, cNew: { value: PAL.indigo },
    cEmber: { value: PAL.ember }, cChar: { value: PAL.char },
  };
  const man = await getJSON('/data/layers/buildings.json');
  const buf = await (await fetch('/data/layers/buildings.bin')).arrayBuffer();
  const fieldB = (x, y) => {
    const i = Math.floor((x - fm.x0) / fm.cell), j = Math.floor((y - fm.y0) / fm.cell);
    return i < 0 || j < 0 || i >= fm.nx || j >= fm.ny ? -1 : ftex.image.data[(j * fm.nx + i) * 4 + 2];
  };
  W.buildings = makeBuildings(man, buf, { ...W.bldU, ...W.fieldU }, fieldB);
  scene.add(W.buildings);

  // ---- landmarks
  W.pagodas = makePagodas();
  scene.add(W.pagodas);
  W.towerU = { uRise: { value: 1 }, uRamp: { value: 0 } };
  W.towers = makeTowers(film.towers, W.towerU);
  scene.add(W.towers);

  // ---- thematic layers
  W.moatLine = lineLayer([{ pts: film.moat, width: 34 }], 2.2, PAL.bronze);
  W.shantang = lineLayer([{ pts: film.shantang, width: 12 }], 2.6, PAL.cinnabar);
  W.shantang.U.uGlow.value = 1.15;
  W.route = lineLayer([{ pts: film.route, width: 14 }], 3.0, PAL.lamp, { dashes: true, length: lineLength(film.route) });
  const ring = [...film.wall.pts, film.wall.pts[0]];
  W.frame = lineLayer([{ pts: ring, width: 34 }], 1.8, PAL.gold);
  W.wall = makeWall(film.wall);
  W.wallLine = makeWallLine(film.wall);
  W.gates = makeGates(film.gates);
  W.bridges = makeBridges(film.bridges);
  W.gardens = makeGardens(film.gardens);
  W.cao = makeCaoxieshan(film.caoxieshan);
  W.frame.U.uColor.value.copy(PAL.street); W.frame.U.uGlow.value = 2.1;
  for (const k of ['moatLine', 'shantang', 'route', 'frame', 'wall', 'wallLine', 'gates', 'bridges', 'gardens', 'cao']) scene.add(W[k].obj);

  // ---- Pingjiang lines
  const pj = await getJSON('/data/layers/pingjiang.json');
  W.pj = makePingjiang(pj);
  scene.add(W.pj.mesh);

  // ---- the stele itself (old photo, morphs with the lines) and a Sentinel-2 underlay
  const loader = new THREE.TextureLoader();
  const maxAniso = renderer.capabilities.getMaxAnisotropy();
  const loadTex = async (url) => {
    const tex = await loader.loadAsync(url);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = maxAniso;
    tex.minFilter = THREE.LinearMipmapLinearFilter;
    return tex;
  };
  W.photo = makeStelePhoto(await getJSON('/data/layers/pj_photo.json'), await loadTex('/data/layers/pj_photo.jpg'));
  W.sat = makeSatellite(await getJSON('/data/layers/sat.json'), await loadTex('/data/layers/sat.jpg'));
  scene.add(W.photo.mesh, W.sat.mesh);

  W.apply = (s) => applyState(W, s);
  return W;
}

const lineLength = (pts) => pts.slice(1).reduce((a, p, i) => a + Math.hypot(p[0] - pts[i][0], p[1] - pts[i][1]), 0);

function makeBuildings(man, buf, uniforms, fieldB) {
  const nv = man.nv, ni = man.ni;
  let o = 0;
  const take = (Type, n, comps = 1) => { const a = new Type(buf, o, n * comps); o += n * comps * Type.BYTES_PER_ELEMENT; return a; };
  const pos = take(Float32Array, nv, 3), height = take(Float32Array, nv), meta = take(Float32Array, nv, 2);
  const idx = take(Uint32Array, ni);
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('aHeight', new THREE.BufferAttribute(height, 1));
  g.setAttribute('aMeta', new THREE.BufferAttribute(meta, 2)); // (ageYear, zone*1000 + rand*999)
  // story frame each building starts to rise; vertices of one building are contiguous and share aMeta
  const reveal = new Float32Array(nv);
  for (let a = 0; a < nv;) {
    let b = a + 1;
    while (b < nv && meta[2 * b] === meta[2 * a] && meta[2 * b + 1] === meta[2 * a + 1]) b++;
    let cx = 0, cy = 0;
    for (let k = a; k < b; k++) { cx += pos[3 * k]; cy -= pos[3 * k + 2]; }
    cx /= b - a; cy /= b - a;
    const zone = Math.floor(meta[2 * a + 1] / 1000 + 0.0005), rnd = (meta[2 * a + 1] / 1000) % 1;
    reveal.fill(revealFrame(zone, rnd, meta[2 * a], cx, cy, fieldB(cx, cy)), a, b);
    a = b;
  }
  g.setAttribute('aReveal', new THREE.BufferAttribute(reveal, 1));
  g.setIndex(new THREE.BufferAttribute(idx, 1));
  g.boundingSphere = new THREE.Sphere(new THREE.Vector3(4000, 100, -2100), 30000);
  const HEAD = `
    attribute float aHeight; attribute vec2 aMeta; attribute float aReveal;
    uniform float uGrow, uYear, uCorrGrow, uStory, uRevealAll; uniform vec4 uZoneGrow;
    ${FIELD_GLSL}`;
  const BODY = `
    float rnd = fract(aMeta.y / 1000.0);
    float zone = floor(aMeta.y / 1000.0 + 0.0005);
    float zg = zone < 0.5 ? uZoneGrow.x : (zone < 1.5 ? uZoneGrow.y : (zone < 2.5 ? uZoneGrow.z : uZoneGrow.w));
    float corr = fieldAt(vec2(position.x, -position.z)).b;
    zg = max(zg, uCorrGrow * step(0.0, corr));
    float vis = max(uRevealAll, smoothstep(aReveal, aReveal + ${RISE.toFixed(1)}, uStory));
    float h = max(aHeight, 3.0) * clamp(uGrow * zg * (1.0 + rnd * 0.15), 0.0, 1.0) * vis;
    // a building hidden by zone or year drops under the board instead of leaving its roof on the ground
    float hidden = step(zg * vis, 0.02);
    vec3 transformed = vec3(position.x, mix(position.y * h + 0.05, -4.0, hidden), position.z);`;
  const mat = new THREE.MeshStandardMaterial({ color: PAL.bld, roughness: 0.86, metalness: 0, flatShading: true });
  mat.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, uniforms);
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', `#include <common>
        ${HEAD}
        varying float vTop, vH, vYr, vZone, vCorr, vRnd;`)
      .replace('#include <begin_vertex>', `${BODY}
        vTop = position.y; vH = aHeight; vYr = aMeta.x; vZone = zone; vCorr = corr; vRnd = rnd;`);
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', `#include <common>
        varying float vTop, vH, vYr, vZone, vCorr, vRnd;
        uniform float uYear, uOldTint, uRoof, uGray, uNewTint, uFresh, uRamp, uDim, uFire, uFireOn;
        uniform vec3 cOld, cRoof, cGray, cNew, cEmber, cChar;
        vec3 ramp(float h) {
          vec3 a = vec3(0.231, 0.357, 0.549), b = vec3(0.643, 0.545, 0.776), c = vec3(0.965, 0.906, 0.855);
          return h < 60.0 ? mix(a, b, h / 60.0) : mix(b, c, clamp((h - 60.0) / 200.0, 0.0, 1.0));
        }`)
      .replace('#include <color_fragment>', `#include <color_fragment>
        vec3 bc = diffuseColor.rgb;
        bool oldc = vZone < 0.5;
        float roof = step(0.999, vTop);
        if (oldc || vCorr >= 0.0) { bc = mix(bc, cOld, uOldTint); bc = mix(bc, cRoof, uRoof * roof); }
        bc = mix(bc, cGray, uGray);
        float isNew = step(1985.5, vYr);
        bc = mix(bc, cNew * (0.8 + 0.4 * vRnd), uNewTint * isNew);
        bc = mix(bc, ramp(vH), uRamp);
        float fd = uFire - vCorr;
        float burning = vCorr >= 0.0 ? smoothstep(0.0, 0.015, fd) * (1.0 - smoothstep(0.05, 0.13, fd)) * uFireOn : 0.0;
        float charred = vCorr >= 0.0 ? smoothstep(0.05, 0.13, fd) * uFireOn : 0.0;
        bc = mix(bc, cChar, charred);
        bc *= mix(0.62, 1.0, smoothstep(0.0, 0.35, vTop));
        bc *= 1.0 - 0.72 * uDim;
        diffuseColor.rgb = bc;
        float fresh = uFresh * isNew * exp(-max(uYear - vYr, 0.0) / 1.4) * step(vYr, uYear + 0.5);
        vec3 bEmis = cEmber * (burning * 3.2 + charred * 0.05) + cNew * fresh * 1.6;`)
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
        totalEmissiveRadiance += bEmis;`);
  };
  const depth = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking });
  depth.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, uniforms);
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', `#include <common>\n${HEAD}`)
      .replace('#include <begin_vertex>', BODY);
  };
  const mesh = new THREE.Mesh(g, mat);
  mesh.customDepthMaterial = depth;
  mesh.castShadow = true; mesh.receiveShadow = true;
  mesh.frustumCulled = false;
  mesh.userData.mat = mat;
  return mesh;
}

// name, local x, y, height m, tiers, base radius m, lean deg, toward deg, year it stands from
export const PAGODAS = [
  ['北寺塔', -718, 1344, 76, 9, 9.5, 0, 0, 1150],
  ['瑞光塔', -816, -2181, 43, 7, 6.5, 0, 0, 1030],
  ['双塔东', 645, -239, 33, 7, 4.2, 0, 0, 982],
  ['双塔西', 625, -242, 33, 7, 4.2, 0, 0, 982],
  ['虎丘塔', -4439, 2993, 48, 7, 7.5, 2.8, 30, 961],
];

function pagodaGeometry(h, tiers, r0) {
  const parts = [];
  const body = h * 0.86, tierH = body / tiers;
  for (let i = 0; i < tiers; i++) {
    const r = r0 * (1 - 0.42 * (i / tiers));
    const shaft = new THREE.CylinderGeometry(r * 0.94, r, tierH * 0.78, 8);
    shaft.translate(0, i * tierH + tierH * 0.39, 0);
    const eave = new THREE.CylinderGeometry(r * 1.38, r * 1.12, tierH * 0.14, 8);
    eave.translate(0, i * tierH + tierH * 0.85, 0);
    parts.push(shaft, eave);
  }
  const spire = new THREE.ConeGeometry(r0 * 0.32, h - body, 8);
  spire.translate(0, body + (h - body) / 2, 0);
  parts.push(spire);
  const g = mergeIndexed(parts);
  g.computeVertexNormals();
  return g;
}

function mergeIndexed(geoms) {
  let nv = 0, ni = 0;
  for (const g of geoms) { nv += g.attributes.position.count; ni += g.index ? g.index.count : g.attributes.position.count; }
  const pos = new Float32Array(nv * 3), idx = new Uint32Array(ni);
  let v = 0, k = 0;
  for (const g of geoms) {
    pos.set(g.attributes.position.array, v * 3);
    const n = g.attributes.position.count;
    if (g.index) for (let i = 0; i < g.index.count; i++) idx[k++] = g.index.array[i] + v;
    else for (let i = 0; i < n; i++) idx[k++] = v + i;
    v += n;
  }
  const out = new THREE.BufferGeometry();
  out.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  out.setIndex(new THREE.BufferAttribute(idx, 1));
  return out;
}

function makePagodas() {
  const grp = new THREE.Group();
  const mat = new THREE.MeshStandardMaterial({ color: PAL.bld, roughness: 0.8, flatShading: true });
  for (const [name, x, y, h, tiers, r0, lean, toward, year] of PAGODAS) {
    const m = new THREE.Mesh(pagodaGeometry(h, tiers, r0), mat);
    m.position.set(x, 0, -y);
    if (lean) {
      const a = THREE.MathUtils.degToRad(toward);
      const axis = new THREE.Vector3(Math.cos(a), 0, Math.sin(a));
      m.quaternion.setFromAxisAngle(axis, -THREE.MathUtils.degToRad(lean));
    }
    m.castShadow = true; m.receiveShadow = true;
    m.name = name; m.userData.year = year;
    grp.add(m);
  }
  grp.userData.mat = mat;
  return grp;
}

// Supertall overrides: CMAB compresses heights, so OSM-tagged towers are extruded at their stated height.
function makeTowers(towers, U) {
  const grp = new THREE.Group();
  const geoms = [];
  for (const t of towers) {
    let g;
    const c = t.pts.reduce((a, p) => [a[0] + p[0] / t.pts.length, a[1] + p[1] / t.pts.length], [0, 0]);
    if (t.lattice) {
      g = new THREE.CylinderGeometry(1.6, 9, t.h, 4, 1);
      g.rotateY(Math.PI / 4);
      g.translate(c[0], t.h / 2, -c[1]);
    } else if (t.arch) {
      g = archGeometry(t.pts, t.h);
    } else {
      const ring = t.pts[0][0] === t.pts.at(-1)[0] && t.pts[0][1] === t.pts.at(-1)[1] ? t.pts.slice(0, -1) : t.pts;
      const shape = new THREE.Shape(ring.map(([x, y]) => new THREE.Vector2(x, y)));
      g = new THREE.ExtrudeGeometry(shape, { depth: t.h, bevelEnabled: false });
      g.rotateX(-Math.PI / 2);
    }
    g = g.index ? g.toNonIndexed() : g;
    const n = g.attributes.position.count;
    g.setAttribute('aH', new THREE.BufferAttribute(new Float32Array(n).fill(t.h), 1));
    g.deleteAttribute('uv');
    g.deleteAttribute('normal');
    geoms.push(g);
  }
  let nv = 0;
  for (const g of geoms) nv += g.attributes.position.count;
  const pos = new Float32Array(nv * 3), ah = new Float32Array(nv);
  let v = 0;
  for (const g of geoms) { pos.set(g.attributes.position.array, v * 3); ah.set(g.attributes.aH.array, v); v += g.attributes.position.count; }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  geo.setAttribute('aH', new THREE.BufferAttribute(ah, 1));
  geo.computeVertexNormals();
  const mat = new THREE.MeshStandardMaterial({ color: PAL.bld, roughness: 0.6, metalness: 0.05, flatShading: true });
  const VH = `attribute float aH; uniform float uRise; varying float vHt; varying float vRel;`;
  const VB = `vec3 transformed = vec3(position.x, position.y * uRise, position.z);`;
  mat.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, U);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', `#include <common>\n${VH}`)
      .replace('#include <begin_vertex>', `${VB}\n vHt = aH; vRel = position.y / max(aH, 1.0);`);
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>
        uniform float uRamp; varying float vHt; varying float vRel;`)
      .replace('#include <color_fragment>', `#include <color_fragment>
        vec3 ra = vec3(0.231, 0.357, 0.549), rb = vec3(0.643, 0.545, 0.776), rc = vec3(0.965, 0.906, 0.855);
        float hh = vHt * vRel;
        vec3 rmp = hh < 60.0 ? mix(ra, rb, hh / 60.0) : mix(rb, rc, clamp((hh - 60.0) / 200.0, 0.0, 1.0));
        diffuseColor.rgb = mix(diffuseColor.rgb, rmp, uRamp);
        diffuseColor.rgb *= mix(0.7, 1.0, smoothstep(0.0, 0.25, vRel));`);
  };
  const depth = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking });
  depth.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, U);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', `#include <common>\nattribute float aH; uniform float uRise;`)
      .replace('#include <begin_vertex>', VB);
  };
  const mesh = new THREE.Mesh(geo, mat);
  mesh.customDepthMaterial = depth;
  mesh.castShadow = true; mesh.receiveShadow = true;
  mesh.frustumCulled = false;
  grp.add(mesh);
  grp.userData.mat = mat;
  return grp;
}

// Gate of the Orient as an arch: an inverted-U profile across the footprint's long axis, extruded through its short axis.
function archGeometry(pts, H) {
  const P = pts.slice(0, -1);
  const c = P.reduce((a, p) => [a[0] + p[0] / P.length, a[1] + p[1] / P.length], [0, 0]);
  let best = null;
  for (let i = 0; i < P.length; i++) {
    const a = P[i], b = P[(i + 1) % P.length];
    const L = Math.hypot(b[0] - a[0], b[1] - a[1]);
    if (!best || L > best.L) best = { L, d: [(b[0] - a[0]) / L, (b[1] - a[1]) / L] };
  }
  const u = best.d, w = [-u[1], u[0]];
  const proj = (d) => P.map((p) => (p[0] - c[0]) * d[0] + (p[1] - c[1]) * d[1]);
  const Wd = (Math.max(...proj(u)) - Math.min(...proj(u))) * 0.9;
  const D = (Math.max(...proj(w)) - Math.min(...proj(w))) * 0.42;
  const s = new THREE.Shape();
  const hw = Wd / 2, leg = Wd * 0.27, top = Wd * 0.3, apex = H * 0.8;
  s.moveTo(-hw, 0);
  s.bezierCurveTo(-hw, H * 0.5, -top * 1.2, H * 0.85, -top, H);
  s.lineTo(top, H);
  s.bezierCurveTo(top * 1.2, H * 0.85, hw, H * 0.5, hw, 0);
  s.lineTo(hw - leg, 0);
  s.bezierCurveTo(hw - leg, apex * 0.62, leg * 0.55, apex, 0, apex);
  s.bezierCurveTo(-leg * 0.55, apex, -hw + leg, apex * 0.62, -hw + leg, 0);
  s.lineTo(-hw, 0);
  const g = new THREE.ExtrudeGeometry(s, { depth: D, bevelEnabled: false, curveSegments: 18 });
  g.translate(0, 0, -D / 2);
  // local (x along u, y up, z along w) -> world (X, Y, Z=-y)
  const m = new THREE.Matrix4().set(
    u[0], 0, w[0], c[0],
    0, 1, 0, 0,
    -u[1], 0, -w[1], -c[1],
    0, 0, 0, 1);
  g.applyMatrix4(m);
  return g;
}

// A ribbon layer with draw progress, glow head and optional travelling dashes.
function lineLayer(lines, y, color, opt = {}) {
  const g = ribbons(lines, y);
  const U = { uProg: { value: 0 }, uOpacity: { value: 0 }, uColor: { value: color.clone() }, uT: { value: 0 },
    uLen: { value: opt.length || 1 }, uDash: { value: opt.dashes ? 1 : 0 }, uGlow: { value: 1.6 } };
  const mat = new THREE.ShaderMaterial({
    uniforms: U, transparent: true, depthWrite: false, side: THREE.DoubleSide,
    polygonOffset: true, polygonOffsetFactor: -6, polygonOffsetUnits: -6,
    vertexShader: `attribute float aU; attribute float aSide; varying float vU; varying float vS;
      void main() { vU = aU; vS = aSide; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    fragmentShader: `uniform float uProg, uOpacity, uT, uLen, uDash, uGlow; uniform vec3 uColor; varying float vU; varying float vS;
      void main() {
        if (vU > uProg) discard;
        float head = smoothstep(0.03, 0.0, uProg - vU) * step(uProg, 0.999);
        float a = uOpacity;
        float k = 1.0;
        if (uDash > 0.5) { float s = vU * uLen / 70.0 - uT * 0.9; k = 0.25 + 0.75 * smoothstep(0.55, 0.15, abs(fract(s) - 0.5) * 2.0); }
        float edge = 1.0 - 0.35 * abs(vS - 0.5) * 2.0;
        gl_FragColor = vec4(uColor * (uGlow * k * edge) + head * vec3(2.6, 2.3, 1.9), a);
      }`,
  });
  const mesh = new THREE.Mesh(g, mat);
  mesh.frustumCulled = false; mesh.renderOrder = 12;
  return { obj: mesh, U };
}

// City wall: an extruded band just inside the moat. Surviving stretches (OSM) are flagged aKeep.
function makeWall(wall) {
  const P = [...wall.pts, wall.pts[0]], K = [...wall.keep, wall.keep[0]];
  const n = P.length, half = 9;
  const pos = [], aU = [], aK = [], idx = [];
  for (let i = 0; i < n; i++) {
    const a = P[Math.max(0, i - 1)], b = P[Math.min(n - 1, i + 1)];
    let dx = b[0] - a[0], dy = b[1] - a[1]; const L = Math.hypot(dx, dy) || 1; dx /= L; dy /= L;
    const nx = -dy, ny = dx;
    const l = [P[i][0] + nx * half, P[i][1] + ny * half], r = [P[i][0] - nx * half, P[i][1] - ny * half];
    for (const [q, t] of [[l, 0], [l, 1], [r, 1], [r, 0]]) { pos.push(q[0], t, -q[1]); aU.push(i / (n - 1)); aK.push(K[i]); }
  }
  for (let i = 0; i < n - 1; i++) {
    const o = i * 4, p = o + 4;
    for (const [s0, s1] of [[0, 1], [1, 2], [2, 3]]) idx.push(o + s0, p + s0, p + s1, o + s0, p + s1, o + s1);
  }
  let g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('aU', new THREE.Float32BufferAttribute(aU, 1));
  g.setAttribute('aKeep', new THREE.Float32BufferAttribute(aK, 1));
  g.setIndex(idx);
  g = g.toNonIndexed();
  g.computeVertexNormals();
  const U = { uFull: { value: 0 }, uKeep: { value: 0 }, uGone: { value: 0 }, uKeepGlow: { value: 0 }, uH: { value: 16 } };
  const mat = new THREE.MeshStandardMaterial({ color: PAL.bld, roughness: 0.85, flatShading: true });
  const VB = `float f = aKeep > 0.5 ? uKeep : uFull * smoothstep(uGone - 0.025, uGone, aU);
    vec3 transformed = vec3(position.x, position.y * uH * f + 0.1, position.z);`;
  mat.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, U);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', `#include <common>
        attribute float aU; attribute float aKeep; uniform float uFull, uKeep, uGone, uH; varying float vKeep;`)
      .replace('#include <begin_vertex>', `${VB}\n vKeep = aKeep;`);
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>
        uniform float uKeepGlow; varying float vKeep;`)
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
        totalEmissiveRadiance += vec3(1.0, 0.78, 0.5) * uKeepGlow * step(0.5, vKeep) * 1.2;`);
  };
  const depth = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking });
  depth.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, U);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', `#include <common>
        attribute float aU; attribute float aKeep; uniform float uFull, uKeep, uGone, uH;`)
      .replace('#include <begin_vertex>', VB);
  };
  const mesh = new THREE.Mesh(g, mat);
  mesh.customDepthMaterial = depth;
  mesh.castShadow = true; mesh.receiveShadow = true; mesh.frustumCulled = false;
  return { obj: mesh, U, mat };
}

// The wall read from afar: a glowing ring that goes dark stretch by stretch; surviving stretches stay lit in gold.
function makeWallLine(wall) {
  const P = [...wall.pts, wall.pts[0]], K = [...wall.keep, wall.keep[0]];
  const lines = [];
  for (let i = 0; i < P.length - 1; i++) lines.push({ pts: [P[i], P[i + 1]], width: 30, attrs: { aKeep: K[i] * K[i + 1], aRing: i / (P.length - 1) } });
  const g = ribbons(lines, 2.4, ['aKeep', 'aRing']);
  const U = { uOpacity: { value: 0 }, uGone: { value: 0 }, uKeepGlow: { value: 0 }, cWall: { value: C('#F4E6C8') }, cKeep: { value: PAL.street } };
  const mat = new THREE.ShaderMaterial({
    uniforms: U, transparent: true, depthWrite: false, side: THREE.DoubleSide,
    polygonOffset: true, polygonOffsetFactor: -7, polygonOffsetUnits: -7,
    vertexShader: `attribute float aKeep; attribute float aRing; varying float vK; varying float vR;
      void main(){ vK = aKeep; vR = aRing; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
    fragmentShader: `uniform float uOpacity, uGone, uKeepGlow; uniform vec3 cWall, cKeep; varying float vK; varying float vR;
      void main(){
        float keep = step(0.5, vK);
        float stand = keep + (1.0 - keep) * smoothstep(uGone - 0.012, uGone, vR);
        float front = (1.0 - keep) * smoothstep(0.03, 0.0, abs(vR - uGone)) * step(uGone, 1.0);
        if (stand + front < 0.01) discard;
        vec3 c = mix(cWall * 1.5, cKeep * 2.4, keep * uKeepGlow) + front * vec3(2.4, 1.6, 1.0);
        gl_FragColor = vec4(c, uOpacity * max(stand, front)); }`,
  });
  const mesh = new THREE.Mesh(g, mat);
  mesh.frustumCulled = false; mesh.renderOrder = 13;
  return { obj: mesh, U };
}

// Gate markers: soft glowing pads, land gates warm, water gates cyan. Revealed one by one.
function makeGates(gates) {
  const grp = new THREE.Group();
  const U = { uProg: { value: 0 }, uOpacity: { value: 0 } };
  const list = [];
  gates.forEach((g, i) => { list.push([g.land, PAL.bronze, i]); list.push([g.water, PAL.flow, i + 0.5]); });
  for (const [[x, y], col, i] of list) {
    const mat = new THREE.ShaderMaterial({
      uniforms: { ...U, uColor: { value: col }, uIdx: { value: i / 8 } }, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
      vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
      fragmentShader: `uniform float uProg, uOpacity, uIdx; uniform vec3 uColor; varying vec2 vUv;
        void main(){ float on = smoothstep(uIdx, uIdx + 0.08, uProg);
          float r = length(vUv - 0.5) * 2.0;
          float core = smoothstep(0.32, 0.18, r);
          float ring = smoothstep(0.08, 0.0, abs(r - 0.62 - 0.25 * (1.0 - on)));
          float halo = exp(-r * 3.2) * 0.6;
          gl_FragColor = vec4(uColor * (core * 2.2 + ring * 1.4 + halo) * on * uOpacity, 1.0); }`,
    });
    const m = new THREE.Mesh(new THREE.PlaneGeometry(220, 220), mat);
    m.rotation.x = -Math.PI / 2; m.position.set(x, 4, -y);
    m.renderOrder = 14; m.frustumCulled = false;
    grp.add(m);
  }
  return { obj: grp, U };
}

// Bridges: a pair of red rails per bridge, lit in a ripple from the old-city centre.
function makeBridges(list) {
  const lines = [];
  for (const [x, y, dx, dy, len] of list) {
    const L = Math.hypot(dx, dy) || 1, ux = dx / L, uy = dy / L, nx = -uy, ny = ux;
    const half = Math.max(len, 24) / 2, off = 6;
    const d = Math.hypot(x + 180, y) / 4200;
    for (const s of [-1, 1]) {
      lines.push({ pts: [[x - ux * half + nx * off * s, y - uy * half + ny * off * s], [x + ux * half + nx * off * s, y + uy * half + ny * off * s]],
        width: 5, attrs: { aDelay: Math.min(0.92, d * 0.8 + 0.08 * fract(Math.sin(x * 12.9898 + y * 78.233) * 43758.5453)) } });
    }
  }
  const g = ribbons(lines, 5, ['aDelay']);
  const U = { uProg: { value: 0 }, uOpacity: { value: 0 }, uColor: { value: PAL.cinnabar } };
  const mat = new THREE.ShaderMaterial({
    uniforms: U, transparent: true, depthWrite: false, side: THREE.DoubleSide,
    vertexShader: 'attribute float aDelay; varying float vD; void main(){ vD = aDelay; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
    fragmentShader: `uniform float uProg, uOpacity; uniform vec3 uColor; varying float vD;
      void main(){ float on = smoothstep(vD, vD + 0.06, uProg); float flash = smoothstep(0.0, 0.03, uProg - vD) * smoothstep(0.12, 0.03, uProg - vD);
        gl_FragColor = vec4(uColor * (1.8 + flash * 3.0), on * uOpacity); }`,
  });
  const mesh = new THREE.Mesh(g, mat);
  mesh.frustumCulled = false; mesh.renderOrder = 13;
  return { obj: mesh, U };
}
const fract = (x) => x - Math.floor(x);

function makeGardens(gardens) {
  const grp = new THREE.Group();
  const U = { uOpacity: { value: 0 } };
  const fillMat = new THREE.MeshBasicMaterial({ color: PAL.jade.clone().multiplyScalar(1.4), transparent: true, opacity: 0, depthWrite: false,
    polygonOffset: true, polygonOffsetFactor: -5, polygonOffsetUnits: -5 });
  const fill = new THREE.Mesh(polygons(gardens.map((g) => [g.pts]), 2.2), fillMat);
  fill.renderOrder = 11; fill.frustumCulled = false;
  const edge = lineLayer(gardens.map((g) => ({ pts: g.pts, width: 7 })), 2.4, PAL.jade.clone().multiplyScalar(1.6));
  edge.U.uProg.value = 1;
  grp.add(fill, edge.obj);
  return { obj: grp, U, set: (a) => { fillMat.opacity = 0.55 * a; edge.U.uOpacity.value = a; grp.visible = a > 0.001; } };
}

// Caoxieshan: paddy-field glow, expanding rings.
function makeCaoxieshan([x, y]) {
  const U = { uOn: { value: 0 }, uT: { value: 0 }, cA: { value: PAL.rice }, cB: { value: PAL.riceGreen } };
  const mat = new THREE.ShaderMaterial({
    uniforms: U, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
    fragmentShader: `uniform float uOn, uT; uniform vec3 cA, cB; varying vec2 vUv;
      void main(){
        vec2 p = (vUv - 0.5) * 2600.0; float r = length(p);
        float disc = smoothstep(520.0, 380.0, r);
        vec2 cell = fract(p / vec2(46.0, 30.0));
        float grid = 1.0 - smoothstep(0.0, 0.09, min(min(cell.x, 1.0 - cell.x), min(cell.y, 1.0 - cell.y)));
        float rings = 0.0;
        for (int i = 0; i < 3; i++) { float rr = mod(uT * 260.0 + float(i) * 430.0, 1300.0); rings += smoothstep(26.0, 0.0, abs(r - rr)) * (1.0 - rr / 1300.0); }
        float halo = exp(-r / 380.0) * 0.5;
        vec3 col = mix(cB, cA, 0.6) * disc * (0.35 + 0.65 * grid) * 1.6 + cA * (rings * 1.2 + halo);
        gl_FragColor = vec4(col * uOn, 1.0); }`,
  });
  const m = new THREE.Mesh(new THREE.PlaneGeometry(2600, 2600), mat);
  m.rotation.x = -Math.PI / 2; m.position.set(x, 3, -y);
  m.renderOrder = 15; m.frustumCulled = false;
  return { obj: m, U };
}

// stele layout: axis-aligned, uniform scale (1.15 m per stele px), centred on the camera's old-city target
// so the tall stele sits in frame
const steleXY = ([px, py]) => [-180 + (px - 2100) * 1.15, -(py - 3750) * 1.15];

// The old photo of the stele on a grid whose vertices carry both layouts: upright stele (position) and the
// georeferencing affine (posB). The lines morph between the same two, so the photo stays under its canals.
function makeStelePhoto(meta, tex) {
  const NX = 36, NY = 64, y = 1.2;
  const [[a, b, c], [d, e, f]] = meta.affine;
  const pos = [], posB = [], uv = [], idx = [];
  for (let j = 0; j <= NY; j++) {
    for (let i = 0; i <= NX; i++) {
      const px = meta.px0 + (i / NX) * (meta.px1 - meta.px0), py = meta.py0 + (j / NY) * (meta.py1 - meta.py0);
      const [sx, sy] = steleXY([px, py]);
      pos.push(sx, y, -sy);
      posB.push(a * px + b * py + c, y, -(d * px + e * py + f));
      uv.push(i / NX, 1 - j / NY);
    }
  }
  for (let j = 0; j < NY; j++) {
    for (let i = 0; i < NX; i++) {
      const k = j * (NX + 1) + i;
      idx.push(k, k + NX + 1, k + 1, k + 1, k + NX + 1, k + NX + 2);
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('posB', new THREE.Float32BufferAttribute(posB, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  const U = {
    uMap: { value: tex }, uMorph: { value: 0 }, uOpacity: { value: 0 }, uBlur: { value: 0 }, uLinesOnly: { value: 0 },
    cDark: { value: C('#17191d') }, cChalk: { value: C('#ece6d6') },
  };
  const mat = new THREE.ShaderMaterial({
    uniforms: U, transparent: true, depthWrite: false, side: THREE.DoubleSide,
    vertexShader: `
      attribute vec3 posB; uniform float uMorph; varying vec2 vUv;
      void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(mix(position, posB, uMorph), 1.0); }`,
    fragmentShader: `
      uniform sampler2D uMap; uniform float uOpacity, uBlur, uLinesOnly; uniform vec3 cDark, cChalk; varying vec2 vUv;
      void main() {
        // soften: a ring of taps on a coarser mip, wider as the blur grows
        float lod = uBlur * 4.5, r = uBlur * 0.011;
        float g = textureLod(uMap, vUv, lod).r * 0.28;
        for (int k = 0; k < 8; k++) {
          float an = float(k) * 0.7854 + 0.39;
          g += textureLod(uMap, vUv + vec2(cos(an), sin(an) * 0.574) * r, lod).r * 0.09;
        }
        vec2 e = min(vUv, 1.0 - vUv);
        float edge = smoothstep(0.0, 0.035, e.x) * smoothstep(0.0, 0.02, e.y);
        vec3 col = mix(cDark, cChalk, g);
        // lines-only: just the chalked canals, laid over a lit map
        float a = mix(1.0, smoothstep(0.42, 0.85, g), uLinesOnly);
        col = mix(col, cChalk * 1.25, uLinesOnly);
        gl_FragColor = vec4(col, uOpacity * edge * a);
      }`,
  });
  const mesh = new THREE.Mesh(g, mat);
  mesh.frustumCulled = false;
  mesh.renderOrder = 9;
  return { mesh, U };
}

// Sentinel-2 mosaic (10 m) laid on the ground above water and roads; buildings, when standing, cover it.
function makeSatellite(meta, tex) {
  const w = meta.x1 - meta.x0, h = meta.y1 - meta.y0;
  const g = new THREE.PlaneGeometry(w, h);
  g.rotateX(-Math.PI / 2);
  g.translate((meta.x0 + meta.x1) / 2, 0.85, -(meta.y0 + meta.y1) / 2);
  const U = { uMap: { value: tex }, uOpacity: { value: 0 } };
  const mat = new THREE.ShaderMaterial({
    uniforms: U, transparent: true, depthWrite: false,
    polygonOffset: true, polygonOffsetFactor: -3, polygonOffsetUnits: -3,
    vertexShader: `varying vec2 vUv; void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    fragmentShader: `
      uniform sampler2D uMap; uniform float uOpacity; varying vec2 vUv;
      void main() {
        vec3 c = texture2D(uMap, vUv).rgb;
        float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
        c = mix(vec3(l), c, 0.62) * vec3(0.92, 0.98, 1.04) * 1.15; // muted, slightly cool, to sit with the board
        vec2 e = min(vUv, 1.0 - vUv);
        float edge = smoothstep(0.0, 0.08, e.x) * smoothstep(0.0, 0.08, e.y);
        gl_FragColor = vec4(c, uOpacity * edge);
      }`,
  });
  const mesh = new THREE.Mesh(g, mat);
  mesh.renderOrder = 8;
  return { mesh, U };
}

function makePingjiang(pj) {
  const stele = steleXY;
  const lines = [];
  const kindOf = { canal_v: 0, canal_h: 1, street: 2, wall: 3 };
  let i = 0;
  const hash = (n) => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
  for (const c of pj.canals) {
    const kind = c.axis === 'v' ? kindOf.canal_v : kindOf.canal_h;
    const midY = c.spx[Math.floor(c.spx.length / 2)][1];
    lines.push({ pts: c.spx.map(stele), ptsB: c.pts, width: 11, attrs: { aKind: kind, aMatch: c.match ? 1 : 0, aDelay: 0.62 * ((midY - 2085) / 3335) + 0.08 * hash(i++) } });
  }
  for (const c of pj.streets) {
    const midY = c.spx[Math.floor(c.spx.length / 2)][1];
    lines.push({ pts: c.spx.map(stele), ptsB: c.pts, width: 7, attrs: { aKind: kindOf.street, aMatch: 0, aDelay: 0.62 * ((midY - 2085) / 3335) + 0.1 + 0.08 * hash(i++) } });
  }
  lines.push({ pts: pj.wall_spx.map(stele), ptsB: pj.wall, width: 34, attrs: { aKind: kindOf.wall, aMatch: 0, aDelay: 0.0 } });
  const g = ribbons(lines, 1.6, ['aKind', 'aMatch', 'aDelay']);
  const uniforms = {
    uMorph: { value: 0 }, uDraw: { value: 0 }, uOpacity: { value: 1 },
    uCanalV: { value: 0 }, uCanalH: { value: 0 }, uStreet: { value: 0 }, uMatch: { value: 0 }, uStone: { value: 1 }, uLost: { value: 0 }, uT: { value: 0 },
    cLine: { value: PAL.line }, cCanal: { value: PAL.canal }, cStreet: { value: PAL.street }, cMatch: { value: PAL.match }, cLost: { value: PAL.lost },
  };
  const mat = new THREE.ShaderMaterial({
    uniforms, transparent: true, depthWrite: false, side: THREE.DoubleSide,
    polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -4,
    vertexShader: `
      attribute vec3 posB; attribute float aU; attribute float aKind; attribute float aMatch; attribute float aDelay; attribute float aSide;
      uniform float uMorph;
      varying float vU; varying float vKind; varying float vMatch; varying float vDelay; varying float vSide;
      void main() {
        vec3 p = mix(position, posB, uMorph);
        vU = aU; vKind = aKind; vMatch = aMatch; vDelay = aDelay; vSide = aSide;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
      }`,
    fragmentShader: `
      uniform float uDraw, uOpacity, uCanalV, uCanalH, uStreet, uMatch, uStone, uLost, uT;
      uniform vec3 cLine, cCanal, cStreet, cMatch, cLost;
      varying float vU; varying float vKind; varying float vMatch; varying float vDelay; varying float vSide;
      void main() {
        // carve: each line draws from u=0 to 1 after its delay
        float span = 0.3;
        float prog = clamp((uDraw * (1.0 + span + 0.7) - vDelay) / span, 0.0, 1.0);
        if (vU > prog) discard;
        float head = smoothstep(0.08, 0.0, prog - vU) * step(prog, 0.999);
        bool isV = vKind < 0.5, isH = vKind > 0.5 && vKind < 1.5, isS = vKind > 1.5 && vKind < 2.5, isW = vKind > 2.5;
        vec3 col = cLine;
        float glow = 0.0;
        if (isV) { col = mix(cLine, cCanal, uCanalV); glow = uCanalV; }
        if (isH) { col = mix(cLine, cCanal, uCanalH); glow = uCanalH; }
        if (isS) { col = mix(cLine * 0.8, cStreet, uStreet); glow = uStreet * 0.8; }
        if (isW) { col = cLine * 0.75; }
        if (vMatch > 0.5) { col = mix(col, cMatch, uMatch); glow = max(glow, uMatch * 1.8); }
        else if (!isW) { col = mix(col, vec3(dot(col, vec3(0.33))) * 0.55, uMatch); glow *= 1.0 - 0.85 * uMatch; }
        // on the white model the lines must read against light ground: darken base, keep glow
        float onWhite = 1.0 - uStone;
        vec3 base = mix(col, col * vec3(0.55, 0.62, 0.7), onWhite * (1.0 - glow));
        // incised groove: bright floor, dark lips at the edges (strongest on stone)
        float across = abs(vSide - 0.5) * 2.0;
        float groove = mix(1.0, 0.45 + 0.55 * smoothstep(1.0, 0.55, across), uStone * (1.0 - glow));
        vec3 outc = base * groove * (1.0 + glow * 1.6) + head * vec3(2.4, 2.2, 1.9);
        float a = uOpacity * (isW ? 0.85 : 1.0) * (isS ? mix(0.75, 1.0, uStreet) : 1.0);
        if (vMatch < 0.5 && !isW) a *= 1.0 - 0.55 * uMatch;
        // lost-canal mode: only stele canals with no counterpart today, dashed and flickering
        if (uLost > 0.0) {
          bool lostLine = (isV || isH) && vMatch < 0.5;
          float dash = step(0.42, fract(vU * 16.0 + vDelay * 7.0));
          float flick = 0.75 + 0.25 * sin(uT * 9.0 + vDelay * 40.0);
          outc = mix(outc, cLost * (1.3 + 0.8 * flick), uLost);
          a = mix(a, lostLine ? dash * flick * uOpacity : 0.0, uLost);
        }
        gl_FragColor = vec4(outc, a);
      }`,
  });
  const mesh = new THREE.Mesh(g, mat);
  mesh.frustumCulled = false;
  mesh.renderOrder = 10;
  return { mesh, uniforms };
}

const val = (s, k, d) => (s[k] === undefined ? d : s[k]);

function applyState(W, s) {
  const st = s.stone;
  const t = s.f / 24;
  W.boardMat.color.copy(mixC(PAL.ground, PAL.groundStone, st));
  W.waterMat.color.copy(mixC(PAL.water, PAL.waterStone, st));
  // roads fade into the board when the scene is pre-modern; glow gold in the finale
  const roadBase = mixC(PAL.road, PAL.roadStone, st);
  W.roadMat.color.copy(roadBase.lerp(W.boardMat.color, val(s, 'roadFade', 0)));
  W.roadMat.emissive.copy(PAL.street).multiplyScalar(val(s, 'roadGlow', 0) * 0.9);
  W.roadMesh.visible = val(s, 'roadFade', 0) < 0.999 || val(s, 'roadGlow', 0) > 0;
  W.hemi.intensity = THREE.MathUtils.lerp(1.15, 0.5, st) * val(s, 'light', 1);
  W.sun.intensity = 2.4 * val(s, 'light', 1);

  const wu = W.waterU;
  wu.uWave.value = val(s, 'wave', 0); wu.uWaveOn.value = val(s, 'waveOn', 0);
  wu.uMoat.value = val(s, 'moatGlow', 0); wu.uGlow.value = val(s, 'waterGlow', 0);

  const b = W.bldU;
  W.buildings.userData.mat.color.copy(mixC(PAL.bld, PAL.bldStone, st));
  b.uGrow.value = s.grow;
  b.uStory.value = val(s, 'fo', s.f); b.uRevealAll.value = val(s, 'revealAll', 1);
  b.uYear.value = val(s, 'bldYear', 2030);
  b.uZoneGrow.value.set(val(s, 'zoneOld', 1), val(s, 'zoneOut', 1), val(s, 'zoneOut', 1), val(s, 'zoneOut', 1));
  b.uCorrGrow.value = val(s, 'corrGrow', 0);
  b.uOldTint.value = val(s, 'fenqiang', 0); b.uRoof.value = val(s, 'fenqiang', 0);
  b.uGray.value = val(s, 'gray', 0); b.uNewTint.value = val(s, 'newTint', 0); b.uFresh.value = val(s, 'fresh', 0);
  b.uRamp.value = val(s, 'ramp', 0); b.uDim.value = val(s, 'dim', 0);
  b.uFire.value = val(s, 'fire', 0); b.uFireOn.value = val(s, 'fireOn', 0);
  W.buildings.visible = s.grow > 0.001;

  // pagodas: stand only once built (by the HUD year), sink with the stone
  const pg = val(s, 'pagoda', s.grow);
  const pyear = val(s, 'pagodaYear', 2030);
  W.pagodas.userData.mat.color.copy(mixC(PAL.bld, PAL.bldStone, st)).lerp(PAL.gray, val(s, 'gray', 0) * 0.6);
  for (const m of W.pagodas.children) {
    const on = THREE.MathUtils.clamp((pyear - m.userData.year + 40) / 40, 0, 1);
    m.scale.set(1, Math.max(0.001, pg * on), 1);
    m.visible = pg * on > 0.002;
  }
  // towers follow the outer city and the year
  const tvis = val(s, 'zoneOut', 1) * s.grow * THREE.MathUtils.clamp((val(s, 'bldYear', 2030) - 2013) / 4, 0, 1);
  W.towerU.uRise.value = Math.max(0.001, val(s, 'towerRise', 1) * tvis);
  W.towerU.uRamp.value = val(s, 'ramp', 0);
  W.towers.userData.mat.color.copy(mixC(PAL.bld, PAL.bldStone, st)).multiplyScalar(1 - 0.72 * val(s, 'dim', 0));
  W.towers.visible = tvis > 0.002;

  const L = (layer, prog, op) => { layer.U.uProg.value = prog; layer.U.uOpacity.value = op; layer.U.uT && (layer.U.uT.value = t); layer.obj.visible = op > 0.001; };
  L(W.moatLine, val(s, 'moatDraw', 0), val(s, 'moatLine', 0));
  L(W.shantang, val(s, 'shantang', 0), val(s, 'shantangOn', 0));
  W.shantang.U.uColor.value.copy(PAL.cinnabar).lerp(PAL.ember, val(s, 'fireOn', 0));
  L(W.route, val(s, 'route', 0), val(s, 'routeOn', 0));
  L(W.frame, val(s, 'frame', 0), val(s, 'frameOn', 0));
  L(W.gates, val(s, 'gates', 0), val(s, 'gatesOn', 0));
  L(W.bridges, val(s, 'bridges', 0), val(s, 'bridgesOn', 0));
  W.gardens.set(val(s, 'gardens', 0));
  W.cao.U.uOn.value = val(s, 'cao', 0); W.cao.U.uT.value = t; W.cao.obj.visible = val(s, 'cao', 0) > 0.001;

  const wl = W.wall.U;
  wl.uFull.value = val(s, 'wallFull', 0); wl.uKeep.value = val(s, 'wallKeep', 0);
  wl.uGone.value = val(s, 'wallGone', 0); wl.uKeepGlow.value = val(s, 'keepGlow', 0);
  W.wall.mat.color.copy(mixC(PAL.bld, PAL.bldStone, st)).lerp(PAL.gray, val(s, 'gray', 0) * 0.5);
  W.wall.obj.visible = wl.uFull.value > 0.001 || wl.uKeep.value > 0.001;
  const wlU = W.wallLine.U;
  wlU.uOpacity.value = val(s, 'wallLine', 0); wlU.uGone.value = val(s, 'wallGone', 0); wlU.uKeepGlow.value = val(s, 'keepGlow', 0);
  W.wallLine.obj.visible = wlU.uOpacity.value > 0.001;

  const u = W.pj.uniforms;
  u.uMorph.value = s.pjMorph; u.uDraw.value = s.pjDraw; u.uOpacity.value = s.pjOpacity;
  u.uCanalV.value = s.canalV; u.uCanalH.value = s.canalH; u.uStreet.value = s.street; u.uMatch.value = s.match;
  u.uStone.value = st; u.uLost.value = val(s, 'lost', 0); u.uT.value = t;
  W.pj.mesh.visible = s.pjOpacity > 0.001;

  const ph = W.photo.U;
  ph.uOpacity.value = val(s, 'photo', 0); ph.uBlur.value = val(s, 'photoBlur', 0); ph.uMorph.value = s.pjMorph;
  ph.uLinesOnly.value = val(s, 'photoLines', 0);
  W.photo.mesh.visible = ph.uOpacity.value > 0.001;
  W.sat.U.uOpacity.value = val(s, 'sat', 0);
  W.sat.mesh.visible = W.sat.U.uOpacity.value > 0.001;
}

// Sun + shadow frustum follow the camera target so the 4k shadow map stays sharp.
export function fitSun(W, cam) {
  const t = new THREE.Vector3(cam.tx, 0, -cam.ty);
  const dir = new THREE.Vector3(-0.55, 0.62, 0.56).normalize(); // light from the south-west, ~38 deg up
  const span = THREE.MathUtils.clamp(cam.dist * 0.75, 400, 16000);
  W.sun.position.copy(t).addScaledVector(dir, span * 3);
  W.sun.target.position.copy(t);
  const sc = W.sun.shadow.camera;
  sc.left = -span; sc.right = span; sc.top = span; sc.bottom = -span;
  sc.near = span * 0.5; sc.far = span * 6;
  sc.updateProjectionMatrix();
}
