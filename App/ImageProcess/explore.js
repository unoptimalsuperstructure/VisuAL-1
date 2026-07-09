'use strict';

const CX_KERNELS = {
  box:      { name: 'Box blur 1/9',   k: [1,1,1, 1,1,1, 1,1,1].map(v => v/9) },
  gaussian: { name: 'Gaussian 1/16', k: [1,2,1, 2,4,2, 1,2,1].map(v => v/16) },
  sharpen:  { name: 'Sharpen',       k: [0,-1,0, -1,5,-1, 0,-1,0] },
  sobelx:   { name: 'Sobel ∂/∂x',    k: [-1,0,1, -2,0,2, -1,0,1] },
  sobely:   { name: 'Sobel ∂/∂y',    k: [-1,-2,-1, 0,0,0, 1,2,1] },
  laplace:  { name: 'Laplacian',     k: [0,1,0, 1,-4,1, 0,1,0] },
};

const CX = {
  gray: null, w: 0, h: 0,
  ox: 0, oy: 0,
  N: 11,
  kx: 1, ky: 1,
  kernel: 'box',
  out: null,
  playing: false, raf: 0, lastTick: 0,
};

function cxOpen() {
  const l = getActiveLayer();
  if (!l) return warn('Select a layer first.');
  const id = l.getImageData(), d = id.data;
  CX.w = l.width; CX.h = l.height;
  CX.gray = new Float64Array(CX.w * CX.h);
  for (let i = 0, p = 0; i < d.length; i += 4, p++)
    CX.gray[p] = Math.round(0.2126*d[i] + 0.7152*d[i+1] + 0.0722*d[i+2]);
  CX.ox = Math.max(0, (CX.w - CX.N) >> 1);
  CX.oy = Math.max(0, (CX.h - CX.N) >> 1);
  cxResetRun();
  document.getElementById('cx-overlay').style.display = 'flex';
  cxDrawPreview();
  cxDrawAll();
}

function cxClose() {
  cxStop();
  document.getElementById('cx-overlay').style.display = 'none';
}

function cxResetRun() {
  CX.kx = 1; CX.ky = 1;
  CX.out = new Array(CX.N * CX.N).fill(null);
}

function cxPix(x, y) {
  x = x < 0 ? 0 : x >= CX.w ? CX.w - 1 : x;
  y = y < 0 ? 0 : y >= CX.h ? CX.h - 1 : y;
  return CX.gray[y * CX.w + x];
}

function cxConvolveAt(wx, wy) {
  const k = CX_KERNELS[CX.kernel].k;
  const patch = [], prods = [];
  let sum = 0;
  for (let dy = -1; dy <= 1; dy++)
    for (let dx = -1; dx <= 1; dx++) {
      const v = cxPix(CX.ox + wx + dx, CX.oy + wy + dy);
      const w = k[(dy + 1) * 3 + (dx + 1)];
      patch.push(v); prods.push(v * w); sum += v * w;
    }
  return { patch, prods, sum };
}

function cxDrawPreview() {
  const cv = document.getElementById('cx-preview');
  const g = cv.getContext('2d');
  const l = getActiveLayer(); if (!l) return;
  const scale = Math.min(cv.width / CX.w, cv.height / CX.h);
  const dw = CX.w * scale, dh = CX.h * scale;
  g.clearRect(0, 0, cv.width, cv.height);
  g.imageSmoothingEnabled = true;
  g.drawImage(l.canvas, (cv.width - dw)/2, (cv.height - dh)/2, dw, dh);

  g.strokeStyle = '#e07030'; g.lineWidth = 2;
  g.strokeRect((cv.width - dw)/2 + CX.ox*scale, (cv.height - dh)/2 + CX.oy*scale,
               CX.N*scale, CX.N*scale);
  cv.onclick = e => {
    const r = cv.getBoundingClientRect();
    const px = Math.round(((e.clientX - r.left) * (cv.width / r.width) - (cv.width - dw)/2) / scale);
    const py = Math.round(((e.clientY - r.top)  * (cv.height / r.height) - (cv.height - dh)/2) / scale);
    CX.ox = Math.min(Math.max(0, px - (CX.N >> 1)), Math.max(0, CX.w - CX.N));
    CX.oy = Math.min(Math.max(0, py - (CX.N >> 1)), Math.max(0, CX.h - CX.N));
    cxResetRun(); cxDrawPreview(); cxDrawAll();
  };
}

function cxCell(cv) { return Math.floor(cv.width / CX.N); }

function cxDrawGrid(cvId, valueAt, highlight) {
  const cv = document.getElementById(cvId);
  const g = cv.getContext('2d');
  const cell = cxCell(cv);
  g.clearRect(0, 0, cv.width, cv.height);
  g.font = `${Math.floor(cell * 0.32)}px monospace`;
  g.textAlign = 'center'; g.textBaseline = 'middle';
  for (let y = 0; y < CX.N; y++)
    for (let x = 0; x < CX.N; x++) {
      const v = valueAt(x, y);
      const px = x * cell, py = y * cell;
      if (v === null) {
        g.fillStyle = '#00000010';
        g.fillRect(px, py, cell, cell);
      } else {
        const c = Math.max(0, Math.min(255, Math.round(v)));
        g.fillStyle = `rgb(${c},${c},${c})`;
        g.fillRect(px, py, cell, cell);
        g.fillStyle = c > 140 ? '#00000090' : '#ffffff90';
        g.fillText(String(Math.round(v)), px + cell/2, py + cell/2);
      }
      g.strokeStyle = '#00000022'; g.strokeRect(px + 0.5, py + 0.5, cell, cell);
    }
  if (highlight) {
    g.strokeStyle = '#e07030'; g.lineWidth = 3;
    g.strokeRect((CX.kx - 1) * cell + 1.5, (CX.ky - 1) * cell + 1.5, cell * 3 - 3, cell * 3 - 3);
    g.lineWidth = 1;
  }
}

function cxDrawMath() {
  const { patch, prods, sum } = cxConvolveAt(CX.kx, CX.ky);
  const k = CX_KERNELS[CX.kernel].k;
  const f = v => (Math.round(v * 100) / 100).toString();
  let rows = '';
  for (let r = 0; r < 3; r++) {
    const p = patch.slice(r*3, r*3+3).map(v => String(Math.round(v)).padStart(3)).join(' ');
    const w = k.slice(r*3, r*3+3).map(v => f(v).padStart(6)).join(' ');
    const m = prods.slice(r*3, r*3+3).map(v => f(v).padStart(7)).join(' ');
    rows += `[${p}]   [${w}]   [${m}]\n`;
  }
  const clamped = Math.max(0, Math.min(255, Math.round(sum)));
  document.getElementById('cx-math').textContent =
    `  patch (luma)          kernel                products\n` + rows +
    `\nΣ products = ${f(sum)}   →  clamp to [0,255]  →  output = ${clamped}`;
}

function cxDrawAll() {
  cxDrawGrid('cx-src', (x, y) => cxPix(CX.ox + x, CX.oy + y), true);
  cxDrawGrid('cx-out', (x, y) => CX.out[y * CX.N + x], false);
  cxDrawMath();
  document.getElementById('cx-kernel-name').textContent = CX_KERNELS[CX.kernel].name;
}

// ── stepping / playing ──

function cxStepOnce() {
  CX.out[CX.ky * CX.N + CX.kx] = cxConvolveAt(CX.kx, CX.ky).sum;
  CX.kx++;
  if (CX.kx > CX.N - 2) { CX.kx = 1; CX.ky++; }
  if (CX.ky > CX.N - 2) { CX.ky = 1; return false; }
  return true;
}

function cxPlayLoop(now) {
  if (!CX.playing) return;
  const speed = +document.getElementById('cx-speed').value;
  if (now - CX.lastTick >= 1000 / speed) {
    CX.lastTick = now;
    if (!cxStepOnce()) cxStop();
    cxDrawAll();
  }
  CX.raf = requestAnimationFrame(cxPlayLoop);
}

function cxPlay() {
  if (CX.playing) return cxStop();
  CX.playing = true;
  document.getElementById('cx-play').textContent = '⏸ Pause';
  CX.lastTick = 0;
  CX.raf = requestAnimationFrame(cxPlayLoop);
}

function cxStop() {
  CX.playing = false;
  cancelAnimationFrame(CX.raf);
  const b = document.getElementById('cx-play');
  if (b) b.textContent = '▶ Play';
}

const RC = {
  pts: [],
  mean: [0,0,0],
  eig: null,
  svd: null,
  step: 0,
  yaw: 0.7, pitch: 0.45, dragging: false, lx: 0, ly: 0,
};

const RC_SCALE = 1 / 128;
function rcOpen() {
  const l = getActiveLayer();
  if (!l) return warn('Select a layer first.');
  const id = l.getImageData(), d = id.data;
  const total = l.width * l.height;
  const step = Math.max(1, Math.floor(total / 3000));

  const raw = [];
  const mean = [0, 0, 0];
  for (let p = 0; p < total; p += step) {
    const i = p * 4;
    raw.push([d[i], d[i+1], d[i+2]]);
    mean[0] += d[i]; mean[1] += d[i+1]; mean[2] += d[i+2];
  }
  const n = raw.length;
  mean[0] /= n; mean[1] /= n; mean[2] /= n;
  RC.mean = mean;

  RC.pts = raw.map(c => ({
    p: [(c[0]-mean[0]) * RC_SCALE, (c[1]-mean[1]) * RC_SCALE, (c[2]-mean[2]) * RC_SCALE],
    css: `rgb(${c[0]},${c[1]},${c[2]})`,
  }));

  const C = new Array(9).fill(0);
  for (const c of raw) {
    const x = c[0]-mean[0], y = c[1]-mean[1], z = c[2]-mean[2];
    C[0]+=x*x; C[1]+=x*y; C[2]+=x*z; C[4]+=y*y; C[5]+=y*z; C[8]+=z*z;
  }
  const dn = Math.max(1, n - 1);
  C[0]/=dn; C[1]/=dn; C[2]/=dn; C[4]/=dn; C[5]/=dn; C[8]/=dn;
  C[3]=C[1]; C[6]=C[2]; C[7]=C[5];
  RC.eig = eigSymmetric3(C);

  const sv = RC.eig.values.map(v => Math.sqrt(Math.max(0, v)) * RC_SCALE);
  const V = RC.eig.vectors, Vt = mat3T(V);
  const M = matMul3x3(matMul3x3(V, [sv[0],0,0, 0,sv[1],0, 0,0,sv[2]]), Vt);
  RC.svd = { ...svd3(M), M };
  RC.step = 0;

  document.getElementById('rc-overlay').style.display = 'flex';
  rcRender();
}

function rcClose() { document.getElementById('rc-overlay').style.display = 'none'; }

function rcProject(p, W, H, zoom) {
  const cy = Math.cos(RC.yaw), sy = Math.sin(RC.yaw);
  const cp = Math.cos(RC.pitch), sp = Math.sin(RC.pitch);
  const x1 = p[0]*cy - p[2]*sy, z1 = p[0]*sy + p[2]*cy;
  const y2 = p[1]*cp - z1*sp,  z2 = p[1]*sp + z1*cp;
  return [W/2 + x1*zoom, H/2 - y2*zoom, z2];
}

const RC_STEPS = [
  { key:'I',  label:'0 · Unit sphere',                     mat: () => identity3() },
  { key:'Vt', label:'1 · Vᵀ — rotate to principal colours', mat: () => RC.svd.Vt },
  { key:'S',  label:'2 · Σ — stretch by colour std-devs',   mat: () => matMul3x3([RC.svd.S[0],0,0, 0,RC.svd.S[1],0, 0,0,RC.svd.S[2]], RC.svd.Vt) },
  { key:'U',  label:'3 · U — rotate back · M = UΣVᵀ',       mat: () => RC.svd.M },
];

function rcRender() {
  const cv = document.getElementById('rc-canvas');
  const g = cv.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const W = cv.width = cv.clientWidth * dpr, H = cv.height = cv.clientHeight * dpr;
  const zoom = Math.min(W, H) * 0.32;
  g.clearRect(0, 0, W, H);

  const axes = [[[1.2,0,0],'#d6455c','R'], [[0,1.2,0],'#2f9e44','G'], [[0,0,1.2],'#3b7dd8','B']];
  g.lineWidth = dpr; g.font = `${11*dpr}px arial`; g.textAlign = 'center';
  for (const [dir, col, name] of axes) {
    const a = rcProject([-dir[0],-dir[1],-dir[2]], W, H, zoom);
    const b = rcProject(dir, W, H, zoom);
    g.strokeStyle = col; g.globalAlpha = 0.6;
    g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke();
    g.globalAlpha = 1; g.fillStyle = col;
    g.fillText(name, b[0], b[1] - 5*dpr);
  }

  const pr = RC.pts.map(o => ({ q: rcProject(o.p, W, H, zoom), css: o.css }));
  pr.sort((a, b) => a.q[2] - b.q[2]);
  const r = 1.6 * dpr;
  for (const { q, css } of pr) {
    g.fillStyle = css;
    g.fillRect(q[0] - r/2, q[1] - r/2, r, r);
  }

  const M = RC_STEPS[RC.step].mat();
  g.lineWidth = 1.4 * dpr; g.strokeStyle = '#111'; g.globalAlpha = 0.75;
  for (const plane of [[0,1],[0,2],[1,2]]) {
    g.beginPath();
    for (let a = 0; a <= 48; a++) {
      const t = a / 48 * Math.PI * 2;
      const u = [0,0,0];
      u[plane[0]] = Math.cos(t); u[plane[1]] = Math.sin(t);
      const v = [ M[0]*u[0]+M[1]*u[1]+M[2]*u[2],
                  M[3]*u[0]+M[4]*u[1]+M[5]*u[2],
                  M[6]*u[0]+M[7]*u[1]+M[8]*u[2] ];
      const q = rcProject(v, W, H, zoom);
      a === 0 ? g.moveTo(q[0], q[1]) : g.lineTo(q[0], q[1]);
    }
    g.stroke();
  }
  g.globalAlpha = 1;

  // panel text
  document.getElementById('rc-step-label').textContent = RC_STEPS[RC.step].label;
  const S = RC.svd.S.map(s => (s / RC_SCALE).toFixed(1));   // back to colour units
  document.getElementById('rc-info').textContent =
    `σ (colour std-devs): ${S.join(', ')}   ·   mean colour ≈ rgb(${RC.mean.map(Math.round).join(', ')})`;
  const key = RC_STEPS[RC.step].key;
  const mat = key === 'I' ? identity3() : key === 'Vt' ? RC.svd.Vt
            : key === 'S' ? [RC.svd.S[0]/RC_SCALE,0,0, 0,RC.svd.S[1]/RC_SCALE,0, 0,0,RC.svd.S[2]/RC_SCALE]
            : RC.svd.U;
  const f = v => (v >= 0 ? ' ' : '-') + Math.abs(v).toFixed(key === 'S' ? 1 : 3);
  document.getElementById('rc-matrix').textContent =
    (key === 'I' ? 'I' : key === 'Vt' ? 'Vᵀ' : key === 'S' ? 'Σ (colour units)' : 'U') + ' =\n' +
    [0,1,2].map(r2 => '[' + f(mat[r2*3]) + ' ' + f(mat[r2*3+1]) + ' ' + f(mat[r2*3+2]) + ' ]').join('\n');
}

function rcInitDrag() {
  const cv = document.getElementById('rc-canvas');
  cv.addEventListener('mousedown', e => { RC.dragging = true; RC.lx = e.clientX; RC.ly = e.clientY; });
  window.addEventListener('mouseup', () => { RC.dragging = false; });
  window.addEventListener('mousemove', e => {
    if (!RC.dragging) return;
    RC.yaw   += (e.clientX - RC.lx) * 0.008;
    RC.pitch  = Math.max(-1.4, Math.min(1.4, RC.pitch + (e.clientY - RC.ly) * 0.008));
    RC.lx = e.clientX; RC.ly = e.clientY;
    rcRender();
  });
}

function exploreInit() {
  const bind = (id, fn) => document.getElementById(id)?.addEventListener('click', fn);
  bind('btn-conv-explore', cxOpen);
  bind('cx-close', cxClose);
  bind('cx-play', cxPlay);
  bind('cx-step', () => { cxStepOnce(); cxDrawAll(); });
  bind('cx-reset', () => { cxResetRun(); cxDrawAll(); });
  document.getElementById('cx-kernel')?.addEventListener('change', e => {
    CX.kernel = e.target.value; cxResetRun(); cxDrawAll();
  });

  bind('btn-rgb-cloud', rcOpen);
  bind('rc-close', rcClose);
  bind('rc-prev', () => { RC.step = Math.max(0, RC.step - 1); rcRender(); });
  bind('rc-next', () => { RC.step = Math.min(3, RC.step + 1); rcRender(); });
  rcInitDrag();
  window.addEventListener('resize', () => {
    if (document.getElementById('rc-overlay')?.style.display === 'flex') rcRender();
  });
}

if (document.readyState === 'loading')
  document.addEventListener('DOMContentLoaded', exploreInit);
else
  exploreInit();