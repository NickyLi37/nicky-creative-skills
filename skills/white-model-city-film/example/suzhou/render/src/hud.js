// HUD overlay (DOM). Positions are in the 1920x1080 design space.
import * as THREE from 'three';

const TICKS = [[-4000, '前4000'], [-514, '前514'], [1, '公元'], [589, '589'], [1229, '1229'], [1759, '1759'], [1900, '1900'], [2000, '2000'], [2025, '今']];
const TPOS = [0, 0.12, 0.2, 0.3, 0.46, 0.62, 0.72, 0.88, 1.0];
const TL = { x0: 600, x1: 1320, y: 74 };

export function yearToT(y) {
  if (y <= TICKS[0][0]) return 0;
  for (let i = 1; i < TICKS.length; i++) {
    if (y <= TICKS[i][0]) {
      const t = (y - TICKS[i - 1][0]) / (TICKS[i][0] - TICKS[i - 1][0]);
      return TPOS[i - 1] + (TPOS[i] - TPOS[i - 1]) * t;
    }
  }
  return 1;
}
const fmtYear = (y) => (y < 0 ? `前${-y}` : y >= 2025 ? '今' : `${y}`);
const fmtYearEn = (y) => (y < 0 ? `${-y} BC` : y >= 2025 ? 'today' : y < 1000 ? `AD ${y}` : `${y}`);

const css = (el, o) => Object.assign(el.style, o);
const div = (parent, style = {}, html = '') => { const d = document.createElement('div'); css(d, { position: 'absolute', ...style }); d.innerHTML = html; parent.appendChild(d); return d; };

export class Hud {
  constructor(root) {
    this.root = root;
    // watermark: Sumi Studio, top-left (1080p spec x48 y40 w180)
    const wm = document.createElement('img');
    wm.src = '/brand/sumi-studio-logo.png';
    css(wm, { position: 'absolute', left: '48px', top: '40px', width: '180px', opacity: '0.96' });
    root.appendChild(wm);
    this.wm = wm;

    // top scrim keeps the timeline and labels legible over the white model
    this.scrimT = div(root, { left: '0', top: '0', width: '1920px', height: '190px', opacity: '0',
      background: 'linear-gradient(180deg, rgba(10,11,13,0.5) 0%, rgba(10,11,13,0.22) 55%, rgba(10,11,13,0) 100%)' });
    root.insertBefore(this.scrimT, root.firstChild);

    // place label, top-right
    this.place = div(root, { right: '64px', top: '50px', textAlign: 'right' },
      `<div style="font:700 22px NSans;letter-spacing:2px">苏州 · 枕河而居 · 1:10000 白模</div>
       <div style="font:400 14px Inter;color:#B9B6AE;margin-top:6px;letter-spacing:0.3px">Suzhou · Living on the Water · CMAB · OpenStreetMap</div>`);

    // timeline
    this.tl = div(root, { left: `${TL.x0}px`, top: `${TL.y}px`, width: `${TL.x1 - TL.x0}px`, height: '40px' });
    div(this.tl, { left: '0', top: '0', width: '100%', height: '1px', background: 'rgba(245,243,238,0.42)' });
    TICKS.forEach(([y, label], i) => {
      const x = TPOS[i] * (TL.x1 - TL.x0);
      div(this.tl, { left: `${x}px`, top: '-4px', width: '1px', height: '9px', background: 'rgba(245,243,238,0.55)' });
      div(this.tl, { left: `${x - 40}px`, top: '10px', width: '80px', textAlign: 'center', font: '400 11px Inter, NSans', color: '#B9B6AE' }, label);
    });
    this.marker = div(this.tl, { top: '-34px', width: '120px', textAlign: 'center' },
      `<div class="y" style="font:700 16px Inter, NSans;color:#F5F3EE"></div>
       <div style="width:0;height:0;margin:3px auto 0;border-left:6px solid transparent;border-right:6px solid transparent;border-top:8px solid #E8C36A"></div>`);
    this.markerY = this.marker.querySelector('.y');
    this.markerEn = div(this.tl, { top: '24px', width: '120px', textAlign: 'center', font: '500 11px Inter', color: '#E8C36A' });

    // soft scrims so type stays legible over the white model
    this.scrimL = div(root, { left: '0', top: '300px', width: '900px', height: '420px', background: 'radial-gradient(ellipse 60% 55% at 22% 50%, rgba(12,13,15,0.62), rgba(12,13,15,0) 100%)' });
    this.scrimB = div(root, { left: '0', top: '840px', width: '1920px', height: '240px', background: 'radial-gradient(ellipse 42% 75% at 50% 78%, rgba(12,13,15,0.6), rgba(12,13,15,0) 100%)' });

    // chapter block, left
    this.card = div(root, { left: '96px', top: '388px', width: '640px' });
    this.cardHead = div(this.card, { left: '0', top: '0', whiteSpace: 'nowrap' });
    this.cardBig = div(this.card, { left: '0', top: '34px', whiteSpace: 'nowrap' });
    this.cardSub = div(this.card, { left: '4px', top: '176px', whiteSpace: 'nowrap' });

    // subtitles
    this.sub = div(root, { left: '0', width: '1920px', top: '952px', textAlign: 'center' });
    this.subCn = div(this.sub, { left: '0', width: '100%', top: '0', font: '500 30px NSans', letterSpacing: '1.5px', textShadow: '0 1px 3px rgba(0,0,0,0.7), 0 0 14px rgba(0,0,0,0.55)' });
    this.subEn = div(this.sub, { left: '0', width: '100%', top: '48px', font: '400 18px Inter', color: '#E3E0D8', textShadow: '0 1px 3px rgba(0,0,0,0.7), 0 0 12px rgba(0,0,0,0.55)' });

    // illustrative / hedge note, under the place label
    this.note = div(root, { right: '64px', top: '112px', textAlign: 'right', maxWidth: '760px' });

    // end card
    this.titleScrim = div(root, { left: '0', top: '0', width: '1920px', height: '1080px', opacity: '0',
      background: 'linear-gradient(90deg, rgba(8,9,11,0.82) 0%, rgba(8,9,11,0.6) 42%, rgba(8,9,11,0) 75%)' });
    root.insertBefore(this.titleScrim, this.wm);
    this.titleCard = div(root, { left: '120px', top: '300px', width: '1100px', opacity: '0' },
      `<div style="font:300 104px NSerif;letter-spacing:10px;line-height:1.1">人家尽枕河</div>
       <div style="font:300 30px Inter;letter-spacing:1px;color:#E3E0D8;margin-top:18px">Homes Pillowed on the River</div>
       <div style="font:400 18px NSans;color:#CFCBC2;margin-top:26px;letter-spacing:1px">题出唐 · 杜荀鹤《送人游吴》</div>
       <div style="font:400 14px Inter;color:#A9A59C;margin-top:6px">Title from Du Xunhe, “Seeing a Friend Off to Wu”, Tang dynasty</div>
       <div style="width:56px;height:2px;background:#E8C36A;margin:40px 0 26px"></div>
       <div style="font:500 16px NSans;letter-spacing:1px;color:#E3E0D8">苏州 · 白模投影 1:10000</div>
       <div style="font:400 13px NSans;color:#A9A59C;line-height:1.85;margin-top:10px">
         建筑：CMAB 数据集（Zhang, Zhao &amp; Long, 2024，CC BY 4.0）<br>
         道路水系：© OpenStreetMap contributors（ODbL）<br>
         平江图：南宋石刻，藏苏州文庙 · 示意重绘（描线参考 Siyuwj / Wikimedia Commons，CC BY-SA 4.0）<br>
         平江图碑旧照：《亚细亚大观》第14辑（Wikimedia Commons，公有领域）<br>
         卫星图：Sentinel-2 cloudless 2016 by EOX（CC BY 4.0，含修改后的 Copernicus Sentinel 数据）<br>
         史料：《吴越春秋》、白居易诗、杜荀鹤诗、《姑苏繁华图》等 · 配乐、旁白：Sumi Studio 生成
       </div>`);

    // calligraphy 苏州, upright on the right of the end card (Ma Shan Zheng brush kaishu, OFL); written top to bottom
    this.callig = div(root, { right: '190px', top: '170px', opacity: '0', writingMode: 'vertical-rl', font: '330px Callig',
      lineHeight: '1', color: '#F2EEE4', textShadow: '0 0 36px rgba(6,7,9,0.55)' }, '<span>苏</span><span>州</span>');

    // callouts
    this.calls = div(root, { left: '0', top: '0', width: '1920px', height: '1080px' });
    this.v = new THREE.Vector3();
  }

  update(s, camera) {
    this.place.style.opacity = s.hudPlace;
    this.scrimT.style.opacity = s.hudPlace;
    this.tl.style.opacity = s.hudPlace;
    const t = yearToT(s.year);
    this.marker.style.left = `${t * (TL.x1 - TL.x0) - 60}px`;
    this.markerEn.style.left = `${t * (TL.x1 - TL.x0) - 60}px`;
    this.markerY.textContent = fmtYear(s.year);
    this.markerEn.textContent = fmtYearEn(s.year);

    const c = s.card;
    if (c && c.alpha > 0.001) {
      this.card.style.opacity = c.alpha;
      this.scrimL.style.opacity = c.alpha * (s.scrim ?? 1);
      this.cardHead.innerHTML = `<span style="font:500 15px Inter;color:#E8C36A;border-bottom:2px solid #E8C36A;padding-bottom:4px">${c.idx}</span>
        <span style="font:700 18px NSans;margin-left:16px;letter-spacing:2px">${c.cn}</span>
        <span style="font:400 15px Inter;color:#B9B6AE;margin-left:10px">${c.en}</span>`;
      this.cardBig.style.opacity = c.bigAlpha;
      this.cardBig.innerHTML = `<span style="font:250 124px NSerif;letter-spacing:-2px;line-height:1">${c.num}</span><span style="font:400 36px NSerif;margin-left:10px">${c.unit}</span>`;
      this.cardSub.style.opacity = c.bigAlpha;
      this.cardSub.innerHTML = c.subCn ? `<div style="font:700 22px NSans;letter-spacing:1px">${c.subCn}</div><div style="font:400 15px Inter;color:#B9B6AE;margin-top:6px">${c.subEn}</div>` : '';
    } else { this.card.style.opacity = 0; this.scrimL.style.opacity = 0; }

    if (s.sub) {
      this.sub.style.opacity = s.sub.alpha;
      this.scrimB.style.opacity = s.sub.alpha * (s.scrim ?? 1);
      this.subCn.textContent = s.sub.cn; this.subEn.textContent = s.sub.en;
    } else { this.sub.style.opacity = 0; this.scrimB.style.opacity = 0; }

    if (s.note && s.note.alpha > 0.001) {
      this.note.style.opacity = s.note.alpha * s.hudPlace;
      this.note.innerHTML = `<span style="font:500 13px NSans;color:#E8C36A;letter-spacing:1px">${s.note.cn}</span><br><span style="font:400 11px Inter;color:#B9B6AE">${s.note.en}</span>`;
    } else this.note.style.opacity = 0;
    this.titleCard.style.opacity = s.title ?? 0;
    this.titleScrim.style.opacity = s.title ?? 0;
    this.callig.style.opacity = s.title ?? 0;
    // each character wipes in from the top with a soft edge, 苏 then 州
    [...this.callig.children].forEach((sp, i) => {
      const e = Math.min(1, Math.max(0, (s.callig ?? 0) * 2 - i)) * 125 - 25;
      sp.style.webkitMaskImage = sp.style.maskImage = `linear-gradient(180deg, #000 ${e}%, transparent ${e + 25}%)`;
    });

    this.calls.innerHTML = '';
    for (const co of s.callouts) {
      this.v.set(co.xy[0], co.h, -co.xy[1]).project(camera);
      const x = (this.v.x * 0.5 + 0.5) * 1920, y = (-this.v.y * 0.5 + 0.5) * 1080;
      if (this.v.z > 1) continue;
      const dx = co.side === 'left' ? -150 : 70, dy = -86;
      const box = div(this.calls, { left: `${x + dx}px`, top: `${y + dy - 22}px`, opacity: co.alpha, padding: '7px 11px 8px',
        background: 'rgba(20,20,22,0.72)', border: '1px solid rgba(245,243,238,0.45)', whiteSpace: 'nowrap' },
        `<div style="font:500 16px NSans">${co.cn}</div><div style="font:400 11px Inter;color:#B9B6AE;margin-top:3px">${co.en}</div>`);
      box.style.position = 'absolute';
      const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      css(svg, { position: 'absolute', left: '0', top: '0', width: '1920px', height: '1080px', opacity: co.alpha, overflow: 'visible' });
      const lx = x + (co.side === 'left' ? dx + 140 : dx), ly = y + dy + 6;
      svg.innerHTML = `<line x1="${x}" y1="${y}" x2="${lx}" y2="${ly}" stroke="rgba(245,243,238,0.7)" stroke-width="1"/>
        <circle cx="${x}" cy="${y}" r="3.5" fill="#E8C36A"/>`;
      this.calls.appendChild(svg);
    }
  }
}
