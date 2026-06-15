'use strict';

// Node

let selectedNode = null;

function nodeAt(x, y) {
  for (let i = state.nodes.length - 1; i >= 0; i--) {
    const n = state.nodes[i];
    const dx = x - n.x, dy = y - n.y;
    if (dx*dx + dy*dy <= NODE_R*NODE_R) return n;
  }
  return null;
}

function addNode(x, y) {
  const id    = ++nodeIdCtr;
  const label = String.fromCharCode(64 + id);
  const color = COLORS[(id - 1) % COLORS.length];
  state.nodes.push({ id, x, y, label, color });
  state.prob    = null;
  state.history = [];
  state.step    = 0;

  updateStepBadge();
  renderSidebar();
  render();
}

function deleteSelected() {
  if (!selectedNode) return;

  const id = selectedNode.id;
  state.nodes = state.nodes.filter(n => n.id !== id);
  state.edges = state.edges.filter(e => e.from !== id && e.to !== id);
  selectedNode = null;
  state.prob    = null;
  state.history = [];
  state.step    = 0;

  updateStepBadge();
  renderSidebar();
  render();
}

function selectNode(nd) {
  selectedNode = (selectedNode && selectedNode.id === nd.id) ? null : nd;
  document.getElementById('btn-delete-node').style.display =
    selectedNode ? 'flex' : 'none';
  renderNodeList();
  render();
}

// Edge

function edgeBetween(fromId, toId) {
  return state.edges.find(e => e.from === fromId && e.to === toId) || null;
}

const EDGE_HIT_DIST = 18;   

function edgeAt(x, y) {
  let best = null, bestD = EDGE_HIT_DIST;

  for (const e of state.edges) {
    const from = state.nodes.find(n => n.id === e.from);
    const to   = state.nodes.find(n => n.id === e.to);
    if (!from || !to) continue;

    let lx, ly;

    if (e.from === e.to) {
      const angle = -Math.PI / 2;
      const cx = from.x + Math.cos(angle) * (NODE_R + SELF_R * 0.9);
      const cy = from.y + Math.sin(angle) * (NODE_R + SELF_R * 0.9);
      lx = cx;
      ly = cy - SELF_R - 6;
    } else {
      const dx = to.x - from.x, dy = to.y - from.y;
      const len = Math.sqrt(dx*dx + dy*dy);
      if (len < 1e-3) continue;
      const ux = dx/len, uy = dy/len;
      const px = -uy, py = ux;
      const hasBoth = state.edges.some(r => r.from === e.to && r.to === e.from);
      const offset  = (hasBoth) ? 12 : 0;
      const sx = from.x + ux*NODE_R + px*offset;
      const sy = from.y + uy*NODE_R + py*offset;
      const ex = to.x   - ux*NODE_R + px*offset;
      const ey = to.y   - uy*NODE_R + py*offset;
      const bend = offset ? 0.3 : 0.0;
      // Bezier midpoint (t=0.5)
      const mx = (sx+ex)/2 + px*len*bend;
      const my = (sy+ey)/2 + py*len*bend;
      // Label is perpendicular offset from midpoint
      lx = mx + px*10;
      ly = my + py*10;
    }

    const d = Math.sqrt((x-lx)**2 + (y-ly)**2);
    if (d < bestD) { bestD = d; best = e; }
  }
  return best;
}