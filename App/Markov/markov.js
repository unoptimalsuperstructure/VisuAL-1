'use strict';

const NODE_R  = 26;
const SELF_R  = 32;
const TRAIL_N = 40;

const COLORS = [
  '#e05555','#4a90d9','#50b86c','#e09c30',
  '#9b59b6','#e07030','#2ebdbd','#c0396b',
];

let nodeIdCtr = 0;
let edgeIdCtr = 0;

const state = {
  nodes:   [],
  edges:   [],
  prob:    null,  
  history: [],
  fullHistory: [],
  step:    0,
  mode: 'dtmc',
  time: 0,
  converged: false,
};

const HIST_MAX = 600;
const CT_DT    = 0.20;
const CT_SUB   = 4;

function getEpsilon() {
  const v = parseFloat(document.getElementById('mk-eps')?.value);
  return (isFinite(v) && v > 0) ? v : 1e-4;
}

// Matrix ────────────────────────────────────────────── 

function buildMatrix() {
  const n   = state.nodes.length;
  const ids = state.nodes.map(nd => nd.id);
  const idx = {};
  ids.forEach((id, i) => { idx[id] = i; });

  const P = Array.from({ length: n }, () => new Float64Array(n));
  for (const e of state.edges) {
    const i = idx[e.to], j = idx[e.from];
    if (i !== undefined && j !== undefined) P[i][j] += e.weight;
  }
  for (let j = 0; j < n; j++) {
    let s = 0;
    for (let i = 0; i < n; i++) s += P[i][j];
    if (s < 1e-12) P[j][j] = 1;
    else for (let i = 0; i < n; i++) P[i][j] /= s;
  }
  return { P, idx, ids };
}

function buildGenerator() {
  const n   = state.nodes.length;
  const ids = state.nodes.map(nd => nd.id);
  const idx = {};
  ids.forEach((id, i) => { idx[id] = i; });
  const Q = Array.from({ length: n }, () => new Float64Array(n));
  for (const e of state.edges) {
    const i = idx[e.to], j = idx[e.from];
    if (i !== undefined && j !== undefined && i !== j) Q[i][j] += e.weight;
  }
  for (let j = 0; j < n; j++) {
    let s = 0;
    for (let i = 0; i < n; i++) if (i !== j) s += Q[i][j];
    Q[j][j] = -s;
  }
  return { Q, idx, ids };
}

// Simulate ────────────────────────────────────────────── 

let autoTimer    = null;
let autoInterval = 600;

function simStep() {
  if (!state.prob) {
    openDistModal();   
    return;
  }
  if (state.nodes.length === 0) return;

  const n    = state.nodes.length;
  const prev = state.prob;
  let next;
 
  if (state.mode === 'ctmc') {
    const { Q } = buildGenerator();
    const f = p => {
      const r = new Float64Array(n);
      for (let i = 0; i < n; i++)
        for (let j = 0; j < n; j++) r[i] += Q[i][j] * p[j];
      return r;
    };
    let p = Float64Array.from(prev);
    const h = CT_DT / CT_SUB;
    for (let ss = 0; ss < CT_SUB; ss++) {
      const k1 = f(p);
      const p2 = p.map((v, i) => v + 0.5*h*k1[i]);
      const k2 = f(p2);
      const p3 = p.map((v, i) => v + 0.5*h*k2[i]);
      const k3 = f(p3);
      const p4 = p.map((v, i) => v + h*k3[i]);
      const k4 = f(p4);
      p = p.map((v, i) => v + (h/6)*(k1[i] + 2*k2[i] + 2*k3[i] + k4[i]));
    }
    next = p;
    state.time += CT_DT;
  } else {
    const { P } = buildMatrix();
    next = new Float64Array(n);
    for (let i = 0; i < n; i++)
      for (let j = 0; j < n; j++)
        next[i] += P[i][j] * prev[j];
    state.step++;
  }

  let s = 0;
  for (let i = 0; i < n; i++) { next[i] = Math.max(0, next[i]); s += next[i]; }
  if (s > 1e-12) for (let i = 0; i < n; i++) next[i] /= s;
  state.prob = next;
  state.fullHistory.length = state.step + 1;
  state.fullHistory.push(next.slice());
  state.history.push(next.slice());
  if (state.history.length > TRAIL_N) state.history.shift();
  state.fullHistory.push({ t: state.mode === 'ctmc' ? state.time : state.step,
                        p: Array.from(next) });
  if (state.fullHistory.length > HIST_MAX) state.fullHistory.shift();
  
  let delta = 0;
  for (let i = 0; i < n; i++) delta += Math.abs(next[i] - prev[i]);
  if (state.mode === 'ctmc') delta /= CT_DT;
  if (autoTimer && delta < getEpsilon()) {
    state.converged = true;
    toggleAuto();
    setConvStatus(state.mode === 'ctmc'
      ? `Converged at t = ${state.time.toFixed(1)}  (‖dπ/dt‖₁ < ε)`
      : `Converged at step ${state.step}  (‖Δπ‖₁ < ε)`);
  }

  updateStepBadge();
  renderDistPanel();
  render();
}

function setConvStatus(msg) {
  const el = document.getElementById('mk-conv-status');
  if (el) { el.textContent = msg; el.style.display = msg ? 'block' : 'none'; }
}

function setChainMode(mode) {
  if (mode === state.mode) return;
  state.mode = mode;
  document.getElementById('btn-chain-dtmc')?.classList.toggle('active', mode === 'dtmc');
  document.getElementById('btn-chain-ctmc')?.classList.toggle('active', mode === 'ctmc');
  simReset();
  renderMatrixPanel();
}

function simStepBack() {
  if (state.step === 0) return;
  state.step--;
  state.prob = state.fullHistory[state.step].slice();
  state.history.pop();

  updateStepBadge();
  renderDistPanel();
  render();
}

function simReset() {
  state.prob    = null;
  state.history = [];
  state.fullHistory = [];
  state.step    = 0;
  state.time = 0;
  state.converged = false;
  setConvStatus('');
  updateStepBadge();
  renderDistPanel();
  if (typeof renderHistoryChart === 'function') renderHistoryChart();
  render();
}

function toggleAuto() {
  if (autoTimer) {
    clearInterval(autoTimer);
    autoTimer = null;
    document.getElementById('btn-auto').textContent = '▶  Auto-step';
  } else {
    if (!state.prob) { openDistModal(); return; }
    autoTimer = setInterval(simStep, autoInterval);
    document.getElementById('btn-auto').textContent = '⏸  Pause';
  }
}

function onSpeedChange() {
  autoInterval = 1100 - parseInt(document.getElementById('mk-speed').value) * 100;
  if (autoTimer) { clearInterval(autoTimer); autoTimer = setInterval(simStep, autoInterval); }
}

function updateStepBadge() {
  document.getElementById('mk-step-badge').textContent = `Step ${state.step}`;
}

function stationary() {
  if (!state.nodes.length) return null;

  const { P } = buildMatrix();
  const n = P.length;
  let v = new Float64Array(n).fill(1 / n);
  
  for (let iter = 0; iter < 500; iter++) {
    const next = new Float64Array(n);
    for (let i = 0; i < n; i++)
      for (let j = 0; j < n; j++)
        next[i] += P[i][j] * v[j];
    let diff = 0;
    for (let i = 0; i < n; i++) diff += Math.abs(next[i] - v[i]);
    v = next;
    if (diff < 1e-10) break;
  }
  return v;
}

// Tidy graph ──────────────────────────────────────────────

// To fix: Make graph stay within canvas, tired

function frLayout(nodes, edges, W, H) {
  const n = nodes.length;
  if (n < 2) return nodes.map(nd => ({ x: W / 2, y: H / 2 }));

  const pairs = new Set();
  const idx = {};
  nodes.forEach((nd, i) => { idx[nd.id] = i; });
  for (const e of edges) {
    const a = idx[e.from], b = idx[e.to];
    if (a === undefined || b === undefined || a === b) continue;
    pairs.add(a < b ? a * 4096 + b : b * 4096 + a);
  }
 
  const P = nodes.map(nd => ({ x: nd.x, y: nd.y }));

  for (let i = 0; i < n; i++)
    for (let j = i + 1; j < n; j++)
      if (Math.abs(P[i].x - P[j].x) < 1 && Math.abs(P[i].y - P[j].y) < 1) {
        P[j].x += (Math.random() - 0.5) * 20;
        P[j].y += (Math.random() - 0.5) * 20;
      }
 
  const k = 0.1 * Math.sqrt((W * H) / n);
  const ITER = 250;
  let temp = Math.max(W, H) / 50;
  const cool = Math.pow(1 / temp, 1 / ITER);
 
  const disp = P.map(() => ({ x: 0, y: 0 }));
  for (let it = 0; it < ITER; it++) {
    disp.forEach(d => { d.x = 0; d.y = 0; });
    for (let i = 0; i < n; i++)
      for (let j = i + 1; j < n; j++) {
        let dx = P[i].x - P[j].x, dy = P[i].y - P[j].y;
        let d = Math.hypot(dx, dy) || 0.01;
        const f = (k * k) / d;
        dx /= d; dy /= d;
        disp[i].x += dx * f; disp[i].y += dy * f;
        disp[j].x -= dx * f; disp[j].y -= dy * f;
      }
    for (const key of pairs) {
      const a = Math.floor(key / 4096), b = key % 4096;
      let dx = P[a].x - P[b].x, dy = P[a].y - P[b].y;
      const d = Math.hypot(dx, dy) || 0.01;
      const f = (d * d) / k;
      dx /= d; dy /= d;
      disp[a].x -= dx * f; disp[a].y -= dy * f;
      disp[b].x += dx * f; disp[b].y += dy * f;
    }
    for (let i = 0; i < n; i++) {
      disp[i].x += (W / 2 - P[i].x) * 0.03;
      disp[i].y += (H / 2 - P[i].y) * 0.03;
    }
    for (let i = 0; i < n; i++) {
      const d = Math.hypot(disp[i].x, disp[i].y) || 1;
      const step = Math.min(d, temp);
      P[i].x += (disp[i].x / d) * step;
      P[i].y += (disp[i].y / d) * step;
    }
    temp *= cool;
  }

  const M = NODE_R * 2.6;
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  for (const p of P) {
    minX = Math.min(minX, p.x); maxX = Math.max(maxX, p.x);
    minY = Math.min(minY, p.y); maxY = Math.max(maxY, p.y);
  }
  const bw = Math.max(1, maxX - minX), bh = Math.max(1, maxY - minY);
  const scale = Math.min((W - 2 * M) / bw, (H - 2 * M) / bh, 1.6);
  const ox = W / 2 - scale * (minX + bw / 2);
  const oy = H / 2 - scale * (minY + bh / 2);
  return P.map(p => ({ x: p.x * scale + ox, y: p.y * scale + oy }));
}
 
let neatenAnim = 0;
 
function neatenGraph() {
  if (state.nodes.length < 2 || neatenAnim) return;
  const canvas = document.getElementById('mk-canvas');
  const W = canvas?.width || 800, H = canvas?.height || 600;
  const target = frLayout(state.nodes, state.edges, W, H);
  const from = state.nodes.map(nd => ({ x: nd.x, y: nd.y }));
  const start = performance.now(), dur = 500;
  const ease = t => t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
  const tick = now => {
    const u = Math.min(1, (now - start) / dur);
    const t = ease(u);
    state.nodes.forEach((nd, i) => {
      nd.x = from[i].x + (target[i].x - from[i].x) * t;
      nd.y = from[i].y + (target[i].y - from[i].y) * t;
    });
    render();
    if (u < 1) neatenAnim = requestAnimationFrame(tick);
    else neatenAnim = 0;
  };
  neatenAnim = requestAnimationFrame(tick);
}