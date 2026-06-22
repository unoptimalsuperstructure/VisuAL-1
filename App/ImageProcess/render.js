'use strict';

let canvas, ctx;

// ── Canvas setup ──────────────────────────────────────────────────

function setupCanvas() {
  canvas = document.getElementById('canvas');
  ctx    = canvas.getContext('2d');
  resize();
  window.addEventListener('resize', resize);

  canvas.addEventListener('mousedown', onMouseDown);
}

function resize() {
  const p   = canvas.parentElement;
  const dpr = devicePixelRatio || 1;

  canvas.width  = p.clientWidth  * dpr;
  canvas.height = p.clientHeight * dpr;
  canvas.style.width  = p.clientWidth  + 'px';
  canvas.style.height = p.clientHeight + 'px';

  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  renderFrame();
}

// ── Render ────────────────────────────────────────────────────────

function renderFrame() {
  if (!ctx) return;
  const dpr = devicePixelRatio || 1;
  const cw  = canvas.width  / dpr;
  const ch  = canvas.height / dpr;

  drawBackground(cw, ch);

  const active = getActiveLayer();
  if (!active) return;

  const PAD    = 24;
  const scale  = Math.min((cw - PAD * 2) / active.width,
                           (ch - PAD * 2) / active.height, 1);
  const dw     = Math.round(active.width  * scale);
  const dh     = Math.round(active.height * scale);
  const dx     = Math.round((cw - dw) / 2);
  const dy     = Math.round((ch - dh) / 2);

  ctx.imageSmoothingEnabled = scale < 1;
  ctx.drawImage(active.canvas, dx, dy, dw, dh);
}

function drawBackground(w, h) {
  const sz = 16;
  ctx.fillStyle = '#e0e0e0';
  ctx.fillRect(0, 0, w, h);
  ctx.fillStyle = '#cccccc';
  for (let y = 0; y * sz < h; y++)
    for (let x = 0; x * sz < w; x++)
      if ((x + y) % 2 === 0) ctx.fillRect(x*sz, y*sz, sz, sz);
}

// ── Mouse actions ──────────────────────────────────────────────────────────

function onMouseDown(e) {
  const { x, y } = cssPt(e);
  const dpr = devicePixelRatio || 1;
  const cw  = canvas.width  / dpr;
  const ch  = canvas.height / dpr;
  const PAD = 24;

  for (const l of IMG.layers) {
    const scale = Math.min((cw - PAD * 2) / l.width,
                            (ch - PAD * 2) / l.height, 1);
    const dw = Math.round(l.width  * scale);
    const dh = Math.round(l.height * scale);
    const dx = Math.round((cw - dw) / 2);
    const dy = Math.round((ch - dh) / 2);
    if (x >= dx && x < dx + dw && y >= dy && y < dy + dh) {
      selectLayer(l.id);
      return;
    }
  }
}

function cssPt(e) {
  const r = canvas.getBoundingClientRect();
  return { x: e.clientX - r.left, y: e.clientY - r.top };
}

// ── Boot ──────────────────────────────────────────────────────────

function boot() {
  setupCanvas();
  initUI();
  refreshLayerList();
  refreshStepsList();
  renderFrame();
}

document.addEventListener('DOMContentLoaded', boot);