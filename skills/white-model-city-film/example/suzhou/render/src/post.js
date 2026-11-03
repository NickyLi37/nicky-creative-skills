// Post chain: HDR scene (MSAA + depth) -> depth-of-field gather -> bloom -> grade/grain/vignette -> canvas.
import * as THREE from 'three';
import { FullScreenQuad } from 'three/addons/postprocessing/Pass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';

const DOF_FRAG = `
  uniform sampler2D tColor; uniform sampler2D tDepth;
  uniform float uNear, uFar, uFocus, uAperture, uMaxBlur; uniform vec2 uRes;
  varying vec2 vUv;
  float viewZ(float d) { float z = d * 2.0 - 1.0; return (2.0 * uNear * uFar) / (uFar + uNear - z * (uFar - uNear)); }
  float coc(float z) { return clamp(uAperture * abs(z - uFocus) / max(z, 1.0), 0.0, uMaxBlur); }
  void main() {
    float zc = viewZ(texture2D(tDepth, vUv).x);
    float cc = coc(zc);
    vec4 acc = vec4(texture2D(tColor, vUv).rgb, 1.0);
    const int N = 48;
    const float GA = 2.39996323;
    for (int i = 1; i < N; i++) {
      float r = sqrt(float(i) / float(N));
      float a = float(i) * GA;
      vec2 off = vec2(cos(a), sin(a)) * r * max(cc, 0.0) / uRes;
      vec2 uv = vUv + off;
      float zs = viewZ(texture2D(tDepth, uv).x);
      float cs = coc(zs);
      // a sample contributes if its own blur reaches here; background does not bleed over sharp foreground
      float w = smoothstep(r * cc - 1.0, r * cc, cs) ;
      w = (zs < zc) ? smoothstep(r * cc - 1.0, r * cc, cs) : 1.0;
      acc += vec4(texture2D(tColor, uv).rgb * w, w);
    }
    gl_FragColor = vec4(acc.rgb / acc.a, 1.0);
  }`;

const FINAL_FRAG = `
  uniform sampler2D tColor; uniform float uExposure, uGrain, uVignette, uSeed, uFade;
  varying vec2 vUv;
  vec3 aces(vec3 x) { const float a=2.51,b=0.03,c=2.43,d=0.59,e=0.14; return clamp((x*(a*x+b))/(x*(c*x+d)+e),0.0,1.0); }
  float h(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233)) + uSeed * 0.731) * 43758.5453); }
  vec3 toSRGB(vec3 c) { return mix(c * 12.92, 1.055 * pow(c, vec3(1.0/2.4)) - 0.055, step(0.0031308, c)); }
  void main() {
    vec3 c = texture2D(tColor, vUv).rgb * uExposure;
    c = aces(c);
    vec2 q = vUv - 0.5;
    c *= 1.0 - uVignette * smoothstep(0.25, 0.85, dot(q, q) * 2.2);
    c = toSRGB(c);
    c += (h(gl_FragCoord.xy) - 0.5) * uGrain;
    gl_FragColor = vec4(c * uFade, 1.0);
  }`;

const VERT = `varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`;

export class Post {
  constructor(renderer, w, h) {
    this.renderer = renderer;
    this.rtScene = new THREE.WebGLRenderTarget(w, h, { type: THREE.HalfFloatType, samples: 4 });
    this.rtScene.depthTexture = new THREE.DepthTexture(w, h, THREE.FloatType);
    this.rtDof = new THREE.WebGLRenderTarget(w, h, { type: THREE.HalfFloatType });
    this.dof = new FullScreenQuad(new THREE.ShaderMaterial({
      vertexShader: VERT, fragmentShader: DOF_FRAG,
      uniforms: { tColor: { value: null }, tDepth: { value: null }, uNear: { value: 1 }, uFar: { value: 1e5 },
        uFocus: { value: 1000 }, uAperture: { value: 0 }, uMaxBlur: { value: 14 }, uRes: { value: new THREE.Vector2(w, h) } },
    }));
    this.bloom = new UnrealBloomPass(new THREE.Vector2(w, h), 0.55, 0.6, 0.92);
    this.final = new FullScreenQuad(new THREE.ShaderMaterial({
      vertexShader: VERT, fragmentShader: FINAL_FRAG,
      uniforms: { tColor: { value: null }, uExposure: { value: 1.0 }, uGrain: { value: 0.022 }, uVignette: { value: 0.35 }, uSeed: { value: 0 }, uFade: { value: 1 } },
    }));
  }

  render(scene, camera, s, look) {
    const r = this.renderer;
    r.setRenderTarget(this.rtScene);
    r.render(scene, camera);
    const du = this.dof.material.uniforms;
    du.tColor.value = this.rtScene.texture; du.tDepth.value = this.rtScene.depthTexture;
    du.uNear.value = camera.near; du.uFar.value = camera.far;
    du.uFocus.value = look.focus; du.uAperture.value = look.aperture; du.uMaxBlur.value = look.maxBlur;
    r.setRenderTarget(this.rtDof);
    this.dof.render(r);
    this.bloom.strength = look.bloom;
    this.bloom.render(r, null, this.rtDof, 0, false);
    const fu = this.final.material.uniforms;
    fu.tColor.value = this.rtDof.texture; fu.uExposure.value = look.exposure; fu.uSeed.value = s.f; fu.uFade.value = look.fade ?? 1;
    r.setRenderTarget(null);
    this.final.render(r);
  }
}
