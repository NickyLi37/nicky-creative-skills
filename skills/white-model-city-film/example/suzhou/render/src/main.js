import * as THREE from 'three';
import { buildWorld, fitSun } from './world.js';
import { Post } from './post.js';
import { Hud } from './hud.js';
import { stateAt, TOTAL } from './timeline.js';

const W = 1920, H = 1080;
const canvas = document.getElementById('c');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
const dpr = window.devicePixelRatio || 1;
renderer.setPixelRatio(dpr);
renderer.setSize(W, H, false);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.NoToneMapping;
renderer.outputColorSpace = THREE.LinearSRGBColorSpace; // final pass encodes sRGB itself

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(30, W / H, 5, 80000);
const world = await buildWorld(scene, renderer);
const post = new Post(renderer, Math.round(W * dpr), Math.round(H * dpr));
const hud = new Hud(document.getElementById('hud'));
await document.fonts.load('300px Callig', '苏州'); // only seen on the end card: load it before the first frame
await document.fonts.ready;
if (hud.wm) {
  await hud.wm.decode().catch(() => { hud.wm.hidden = true; });
}

function placeCamera(c) {
  const az = THREE.MathUtils.degToRad(c.az), p = THREE.MathUtils.degToRad(Math.min(c.pitch, 89.6));
  const t = new THREE.Vector3(c.tx, 0, -c.ty);
  camera.position.set(t.x - Math.sin(az) * Math.cos(p) * c.dist, Math.sin(p) * c.dist, t.z + Math.cos(az) * Math.cos(p) * c.dist);
  camera.up.set(0, 1, 0);
  camera.fov = c.fov;
  camera.near = THREE.MathUtils.clamp(c.dist * 0.02, 5, 200);
  camera.far = c.dist * 12 + 20000;
  camera.updateProjectionMatrix();
  camera.lookAt(t);
}

window.renderFrame = (f) => {
  const s = stateAt(f);
  world.apply(s);
  placeCamera(s.cam);
  fitSun(world, s.cam);
  // shallower blur at grazing angles, where the near ground is very close to the lens
  const flat = THREE.MathUtils.clamp((s.cam.pitch - 20) / 30, 0, 1);
  const look = { focus: s.cam.dist, aperture: (6 + 10 * flat) * dpr, maxBlur: (7 + 7 * flat) * dpr, bloom: s.bloom ?? 0.5, exposure: s.exposure ?? 1.0, fade: s.fade ?? 1 };
  post.render(scene, camera, s, look);
  hud.update(s, camera);
  renderer.getContext().finish();
  return { f, chapter: s.chapter.id };
};
window.TOTAL = TOTAL;
window.ready = true;

const q = new URLSearchParams(location.search);
if (q.has('f')) window.renderFrame(Number(q.get('f')));
