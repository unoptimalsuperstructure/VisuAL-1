'use strict';

const canvas = document.getElementById('mk-canvas');
const ctx    = canvas.getContext('2d');

function resizeCanvas() {
  const vp  = document.getElementById('viewport');
  canvas.width  = vp.clientWidth;
  canvas.height = vp.clientHeight;
  render();
}
window.addEventListener('resize', resizeCanvas);

// Mode section

const HINTS = {
  node: 'Click canvas to place a node · Drag any node to reposition it',
  edge: 'Click source \u2192 click target · Click same node twice or double-click for self-loop · Double-click any edge to edit its weight',
};

let mode       = 'node';
let edgeSrcNode = null;
let mouseCanvas = { x: 0, y: 0 };
let dragging    = null;

function setMode(m) {
  mode = m;
  edgeSrcNode = null;
  document.querySelectorAll('.mk-mode-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('btn-mode-' + m).classList.add('active');
  document.getElementById('mk-hint').textContent = HINTS[m];
  canvas.style.cursor = 'crosshair';
  render();
}

function hexAlpha(hex, alpha) {
  const r = parseInt(hex.slice(1,3), 16);
  const g = parseInt(hex.slice(3,5), 16);
  const b = parseInt(hex.slice(5,7), 16);
  return `rgba(${r},${g},${b},${alpha.toFixed(3)})`;
}

// Rendering

function render() {
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  // background grid
  ctx.strokeStyle = '#e8e8e8';
  ctx.lineWidth = 1;
  const g = 40;
  for (let x = 0; x < W; x += g) { ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,H); ctx.stroke(); }
  for (let y = 0; y < H; y += g) { ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(W,y); ctx.stroke(); }

  if (!state.nodes.length) return;

  const showStat    = document.getElementById('chk-stationary').checked;
  const showTrail   = document.getElementById('chk-trail').checked;
  const showWeights = document.getElementById('chk-weights').checked;
  const stat        = showStat ? stationary() : null;
  const { P, idx }  = buildMatrix();

  // ghost trail
  if (showTrail && state.prob && state.history.length > 1) {
    state.history.slice(0, -1).forEach((hv, hi) => {
      const age   = state.history.length - 1 - hi;
      const alpha = Math.max(0, 0.22 - age * (0.22 / TRAIL_N));
      state.nodes.forEach((nd, i) => {
        const r = NODE_R * (0.35 + hv[i] * 1.4);
        ctx.beginPath();
        ctx.arc(nd.x, nd.y, r, 0, Math.PI * 2);
        ctx.fillStyle = hexAlpha(nd.color, alpha);
        ctx.fill();
      });
    });
  }

  // edges
  for (const e of state.edges) {
    const from = state.nodes.find(n => n.id === e.from);
    const to   = state.nodes.find(n => n.id === e.to);
    if (!from || !to) continue;
    const fi = idx[e.from], ti = idx[e.to];
    const w  = (fi !== undefined && ti !== undefined) ? P[ti][fi] : 0;
    const hasBoth = state.edges.some(r => r.from === e.to && r.to === e.from);
    const offset  = (hasBoth && e.from !== e.to) ? 12 : 0;
    if (e.from === e.to) drawSelfLoop(from, w, e.weight, showWeights);
    else                 drawArrow(from, to, w, e.weight, offset, showWeights);
  }

  // live edge drawing
  if (mode === 'edge' && edgeSrcNode) {
    ctx.beginPath();
    ctx.moveTo(edgeSrcNode.x, edgeSrcNode.y);
    ctx.lineTo(mouseCanvas.x, mouseCanvas.y);
    ctx.strokeStyle = '#aaa';
    ctx.lineWidth   = 1.5;
    ctx.setLineDash([5, 4]);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  // stationary 
  if (stat) {
    state.nodes.forEach((nd, i) => {
      ctx.beginPath();
      ctx.arc(nd.x, nd.y, NODE_R * (0.35 + stat[i] * 1.4) + 6, 0, Math.PI * 2);
      ctx.strokeStyle = hexAlpha(nd.color, 0.35);
      ctx.lineWidth   = 2.5;
      ctx.setLineDash([4, 3]);
      ctx.stroke();
      ctx.setLineDash([]);
    });
  }

  // nodes
  state.nodes.forEach((nd, i) => {
    const p = state.prob ? state.prob[i] : null;
    const r = p !== null ? NODE_R * (0.35 + p * 1.4) : NODE_R;

    if (selectedNode?.id === nd.id) {
      ctx.beginPath();
      ctx.arc(nd.x, nd.y, r + 5, 0, Math.PI * 2);
      ctx.strokeStyle = '#333';
      ctx.lineWidth   = 2;
      ctx.stroke();
    }

    ctx.beginPath();
    ctx.arc(nd.x, nd.y, r, 0, Math.PI * 2);
    ctx.fillStyle   = nd.color;
    ctx.fill();
    ctx.strokeStyle = '#fff';
    ctx.lineWidth   = 2;
    ctx.stroke();

    ctx.fillStyle    = '#fff';
    ctx.font         = `bold ${Math.max(10, Math.round(r * 0.65))}px sans-serif`;
    ctx.textAlign    = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(nd.label, nd.x, nd.y);

    if (p !== null) {
      ctx.fillStyle    = '#444';
      ctx.font         = '10px monospace';
      ctx.textBaseline = 'top';
      ctx.fillText((p * 100).toFixed(1) + '%', nd.x, nd.y + r + 3);
    }
  });
}

// Draw-er functions

function drawArrow(from, to, normW, rawW, offset, showWeights) {
  const dx = to.x - from.x, dy = to.y - from.y;
  const len = Math.sqrt(dx*dx + dy*dy);
  if (len < 1e-3) return;
  const ux = dx/len, uy = dy/len, px = -uy, py = ux;
  const sx = from.x + ux*NODE_R + px*offset;
  const sy = from.y + uy*NODE_R + py*offset;
  const ex = to.x   - ux*NODE_R + px*offset;
  const ey = to.y   - uy*NODE_R + py*offset;
  const bend = offset ? 0.3 : 0.0;
  const mx   = (sx+ex)/2 + px*len*bend;
  const my   = (sy+ey)/2 + py*len*bend;
  const alpha = 0.25 + normW*0.75;

  ctx.beginPath();
  ctx.moveTo(sx, sy);
  ctx.quadraticCurveTo(mx, my, ex, ey);
  ctx.strokeStyle = hexAlpha(to.color, alpha);
  ctx.lineWidth   = 1 + normW * 3.5;
  ctx.stroke();

  // arrowhead
  const t   = 0.85;
  const hx  = (1-t)*(1-t)*sx + 2*(1-t)*t*mx + t*t*ex;
  const hy  = (1-t)*(1-t)*sy + 2*(1-t)*t*my + t*t*ey;
  const adx = ex-hx, ady = ey-hy;
  const al  = Math.sqrt(adx*adx+ady*ady) || 1;
  const ax  = adx/al, ay = ady/al;
  const hw  = 5 + normW*5;
  ctx.beginPath();
  ctx.moveTo(ex, ey);
  ctx.lineTo(ex - ax*hw*1.6 + ay*hw*0.7, ey - ay*hw*1.6 - ax*hw*0.7);
  ctx.lineTo(ex - ax*hw*1.6 - ay*hw*0.7, ey - ay*hw*1.6 + ax*hw*0.7);
  ctx.closePath();
  ctx.fillStyle = hexAlpha(to.color, alpha);
  ctx.fill();

  if (showWeights) {
    ctx.fillStyle = '#333'; ctx.font = '10px monospace';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(rawW % 1 === 0 ? rawW : rawW.toFixed(2), mx + px*10, my + py*10);
  }
}

function drawSelfLoop(nd, normW, rawW, showWeights) {
  const angle = -Math.PI / 2;
  const cx = nd.x + Math.cos(angle) * (NODE_R + SELF_R * 0.9);
  const cy = nd.y + Math.sin(angle) * (NODE_R + SELF_R * 0.9);
  const alpha = 0.25 + normW * 0.75;

  ctx.beginPath();
  ctx.arc(cx, cy, SELF_R, 0, Math.PI * 2);
  ctx.strokeStyle = hexAlpha(nd.color, alpha);
  ctx.lineWidth   = 1 + normW * 3.5;
  ctx.stroke();

  // arrowhead at re-entry point
  const reX = nd.x + Math.cos(angle - 0.35) * NODE_R;
  const reY = nd.y + Math.sin(angle - 0.35) * NODE_R;
  const tgX = Math.cos(angle - 0.35 + Math.PI/2);
  const tgY = Math.sin(angle - 0.35 + Math.PI/2);
  const hw  = 5 + normW * 4;
  ctx.beginPath();
  ctx.moveTo(reX, reY);
  ctx.lineTo(reX - tgX*hw*1.5 + tgY*hw*0.6, reY - tgY*hw*1.5 - tgX*hw*0.6);
  ctx.lineTo(reX - tgX*hw*1.5 - tgY*hw*0.6, reY - tgY*hw*1.5 + tgX*hw*0.6);
  ctx.closePath();
  ctx.fillStyle = hexAlpha(nd.color, alpha);
  ctx.fill();

  if (showWeights) {
    ctx.fillStyle = '#333'; ctx.font = '10px monospace';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(rawW % 1 === 0 ? rawW : rawW.toFixed(2), cx, cy - SELF_R - 6);
  }
}

// Canvas events

function canvasXY(e) {
  const rect = canvas.getBoundingClientRect();
  return { x: e.clientX - rect.left, y: e.clientY - rect.top };
}

canvas.addEventListener('mousedown', e => {
  const { x, y } = canvasXY(e);
  const hit = nodeAt(x, y);

  if (mode === 'node') {
    if (hit) {
      selectNode(hit);
      dragging = { node: hit, ox: x - hit.x, oy: y - hit.y };
    } else {
      addNode(x, y);
    }
    return;
  }

  if (mode === 'edge') {
    if (!edgeSrcNode) {
      if (hit) { edgeSrcNode = hit; render(); }
    } else {
      if (hit) openEdgeModal(edgeSrcNode.id, hit.id);
      edgeSrcNode = null;
      render();
    }
    return;
  }
});

canvas.addEventListener('dblclick', e => {
  // dbl click shortcuts
  const { x, y } = canvasXY(e);

  if (mode === 'edge') {
    // self loop
    const hitNode = nodeAt(x, y);
    if (hitNode) {
      edgeSrcNode = null;
      openEdgeModal(hitNode.id, hitNode.id);
      return;
    }
    // edit weight
    const hitEdge = edgeAt(x, y);
    if (hitEdge) {
      edgeSrcNode = null;
      openEdgeModal(hitEdge.from, hitEdge.to);
      return;
    }
  }
});

canvas.addEventListener('mousemove', e => {
  const { x, y } = canvasXY(e);
  mouseCanvas = { x, y };
  if (dragging) {
    dragging.node.x = x - dragging.ox;
    dragging.node.y = y - dragging.oy;
    render(); return;
  }
  if (mode === 'edge' && edgeSrcNode) render();
  const overNode = nodeAt(x, y);
  const overEdge = !overNode && edgeAt(x, y);
  canvas.style.cursor = overNode ? 'grab' : overEdge ? 'pointer' : 'crosshair';
});

canvas.addEventListener('mouseup',    () => { dragging = null; });
canvas.addEventListener('mouseleave', () => { dragging = null; });

// To implement "arrange edges" for tidiness (ref to chem draw for auto arrangement of molecule drawing) 

// Load Canvas 

resizeCanvas();
setMode('node');
renderSidebar();