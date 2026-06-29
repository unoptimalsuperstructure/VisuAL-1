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
};

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

// Simulate ────────────────────────────────────────────── 

let autoTimer    = null;
let autoInterval = 600;
const epsilon    = 1e-6; // |curr step - prev step| < \epsilon. Increase value if ppl say it takes too long to converge

function simStep() {
  if (!state.prob) {
    openDistModal();   
    return;
  }
  if (state.nodes.length === 0) return;

  const { P } = buildMatrix();
  const n     = state.nodes.length;

  const next  = new Float64Array(n);
  for (let i = 0; i < n; i++)
    for (let j = 0; j < n; j++)
      next[i] += P[i][j] * state.prob[j];

  let s = 0;
  for (let i = 0; i < n; i++) { next[i] = Math.max(0, next[i]); s += next[i]; }
  if (s > 1e-12) for (let i = 0; i < n; i++) next[i] /= s;
  state.prob = next;
  state.fullHistory.length = state.step + 1;
  state.fullHistory.push(next.slice());
  state.history.push(next.slice());
  if (state.history.length > TRAIL_N) state.history.shift();
  state.step++;

  updateStepBadge();
  renderDistPanel();
  render();
}

function simStepBack() {
  // Probability in step back is not reflected but the rest are fine?????

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
  state.step    = 0;

  updateStepBadge();
  renderDistPanel();
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