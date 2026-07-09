'use strict';

// Section ────────────────────────────────────────────── 

const sectionOpen = { nodes: true, sim: true };

function toggleSection(id) {
  sectionOpen[id] = !sectionOpen[id];
  const body = document.getElementById('section-' + id);
  const head = document.getElementById('shead-' + id);
  if (body) body.style.display = sectionOpen[id] ? 'block' : 'none';
  if (head) head.classList.toggle('collapsed', !sectionOpen[id]);
}

// Render sidebar ────────────────────────────────────────────── 

function renderSidebar() {
  renderNodeList();
  renderDistPanel();
  renderMatrixPanel();
  document.getElementById('node-count-badge').textContent = state.nodes.length;
  document.getElementById('btn-set-dist').style.display =
    state.nodes.length ? 'flex' : 'none';
}

function renderNodeList() {
  const list = document.getElementById('node-list');
  list.innerHTML = '';
  if (!state.nodes.length) {
    list.innerHTML = '<div id="no-obj">No nodes yet</div>';
    document.getElementById('btn-delete-node').style.display = 'none';
    return;
  }

  state.nodes.forEach(nd => {
    const row = document.createElement('div');
    row.className = 'obj-row' + (selectedNode?.id === nd.id ? ' active' : '');
    row.innerHTML =
      `<div class="obj-dot" style="background:${nd.color}"></div>` +
      `<span style="flex:1">Node ${nd.label}</span>` +
      (selectedNode?.id === nd.id ? '<span class="tag">selected</span>' : '');
    row.onclick = () => selectNode(nd);
    list.appendChild(row);
  });
}

function renderDistPanel() {
  renderPlot();
  const panel = document.getElementById('mk-dist-panel');
  document.getElementById('btn-set-dist').style.display =
    state.nodes.length ? 'flex' : 'none';

  if (!state.nodes.length) {
    panel.innerHTML = '<div style="font-size:12px;color:var(--muted)">No nodes yet</div>';
    return;
  }
  if (!state.prob) {
    panel.innerHTML =
      '<div style="font-size:12px;color:var(--muted);line-height:1.5">' +
      'No distribution set.<br>Use <em>Set initial distribution</em> to begin.' +
      '</div>';
    return;
  }
  panel.innerHTML = '';
  state.nodes.forEach((nd, i) => {
    const p   = state.prob[i];
    const pct = (p * 100).toFixed(1);
    const row = document.createElement('div');
    row.className = 'mk-dist-row';
    row.innerHTML =
      `<div class="mk-dist-swatch" style="background:${nd.color}"></div>` +
      `<span style="width:14px;color:var(--muted)">${nd.label}</span>` +
      `<div class="mk-dist-bar-wrap">` +
        `<div class="mk-dist-bar" style="width:${pct}%;background:${nd.color}"></div>` +
      `</div>` +
      `<span class="mk-dist-val">${pct}%</span>`;
    panel.appendChild(row);
  });
}

function renderMatrixPanel() {
  const panel = document.getElementById('mk-matrix-panel');
  const n = state.nodes.length;

  if (n === 0) {
    panel.innerHTML = '<div id="no-obj">Add nodes to see the matrix</div>';
    return;
  }
  
  const ctmc = state.mode === 'ctmc';
  const { P } = ctmc ? (g => ({ P: g.Q }))(buildGenerator()) : buildMatrix();
  let html = ctmc
    ? '<div style="font-size:10px;color:var(--muted);margin:0 0 4px" ' +
      'data-tip="CTMC generator: off-diagonal entries are jump rates j → i; each diagonal is minus its column sum, so columns sum to 0. Evolution: dπ/dt = Qπ.">' +
      'Generator Q (rates · columns sum to 0)</div>'
    : '';
  html +=
    '<table style="font-family:var(--font-maths);font-size:11px;' +
    'border-collapse:collapse;width:100%">' +
    '<tr><td style="padding:2px 4px;color:var(--muted)">to \\ from</td>';
  for (const nd of state.nodes)
    html += `<td style="padding:2px 6px;text-align:center;color:var(--muted);` +
            `font-weight:600">${nd.label}</td>`;
  html += '</tr>';
  for (let i = 0; i < n; i++) {
    const nd = state.nodes[i];
    html += `<tr><td style="padding:2px 4px;font-weight:600;color:${nd.color}">` +
            `${nd.label}</td>`;
    for (let j = 0; j < n; j++) {
      const v     = P[i][j];
      const alpha = Math.round((0.15 + v * 0.85) * 255).toString(16).padStart(2, '0');
      html +=
        `<td style="padding:3px 6px;text-align:center;` +
        `background:${nd.color}${alpha};border-radius:3px">` +
        `${v.toFixed(2)}</td>`;
    }
    html += '</tr>';
  }
  html += '</table>';
  panel.innerHTML = html;
}

//  Edge weight modal ────────────────────────────────────────────── 

let pendingEdge = null;

function openEdgeModal(fromId, toId) {
  pendingEdge = { from: fromId, to: toId };
  const existing  = edgeBetween(fromId, toId);
  const fromLabel = state.nodes.find(n => n.id === fromId)?.label ?? fromId;
  const toLabel   = state.nodes.find(n => n.id === toId)?.label   ?? toId;
  document.getElementById('modal-title').textContent =
    fromId === toId ? `Self-loop on ${fromLabel}` : `Edge  ${fromLabel} \u2192 ${toLabel}`;
  document.getElementById('modal-desc').textContent =
    'Enter a positive weight. Weights on outgoing edges are normalised to sum to 1 automatically.';
  document.getElementById('mf-weight').value = existing ? existing.weight : '1';
  document.getElementById('modal-err').textContent = '';
  document.getElementById('btn-delete-edge').style.display = existing ? 'flex' : 'none';
  document.getElementById('modal-bg').style.display = 'flex';
  const inp = document.getElementById('mf-weight');
  inp.focus(); inp.select();
}

function deleteEdge() {
  if (!pendingEdge) return;
  const { from, to } = pendingEdge;
  state.edges = state.edges.filter(e => !(e.from === from && e.to === to));
  closeModal();
  renderMatrixPanel();
  render();
}
 
function submitEdgeModal() {
  const raw = parseFloat(document.getElementById('mf-weight').value);
  if (!isFinite(raw) || raw <= 0) {
    document.getElementById('modal-err').textContent = 'Weight must be a positive number.';
    return;
  }

  const { from, to } = pendingEdge;
  const existing = edgeBetween(from, to);

  if (existing) existing.weight = raw;
  else state.edges.push({ id: ++edgeIdCtr, from, to, weight: raw });
  closeModal();
  renderMatrixPanel();
  render();
}

function closeModal() {
  document.getElementById('modal-bg').style.display = 'none';
  pendingEdge = null;
}

function closeBgClick(e) {
  if (e.target === document.getElementById('modal-bg')) closeModal();
}

// Dist modal ──────────────────────────────────────────────

function openDistModal() {
  const n = state.nodes.length;
  if (n === 0) return;
  const fields = document.getElementById('dist-modal-fields');
  fields.innerHTML = '';
  state.nodes.forEach((nd, i) => {
    const row = document.createElement('div');
    row.className = 'field-row';
    const current = state.prob ? state.prob[i] : 1 / n;
    row.innerHTML =
      `<label style="width:auto;min-width:20px;color:${nd.color};font-weight:600">` +
      `${nd.label}</label>` +
      `<input id="dp-${nd.id}" type="text" value="${current.toFixed(4)}" placeholder="0"/>`;
    fields.appendChild(row);
  });
  document.getElementById('dist-modal-err').textContent = '';
  document.getElementById('dist-modal-bg').style.display = 'flex';
  fields.querySelector('input')?.focus();
}

function submitDistModal() {
  const vals = [];
  let err = false;
  state.nodes.forEach(nd => {
    const inp = document.getElementById('dp-' + nd.id);
    const v   = parseFloat(inp.value);
    if (!isFinite(v) || v < 0) { inp.classList.add('err'); err = true; }
    else { inp.classList.remove('err'); vals.push(v); }
  });

  if (err) {
    document.getElementById('dist-modal-err').textContent =
      'All values must be non-negative numbers.';
    return;
  }

  const sum = vals.reduce((a, b) => a + b, 0);
  if (sum < 1e-12) {
    document.getElementById('dist-modal-err').textContent =
      'At least one value must be positive.';
    return;
  }

  const v = new Float64Array(vals.map(x => x / sum));
  state.prob        = v;
  state.history     = [v.slice()];
  state.fullHistory = [v.slice()];
  state.step        = 0;
  closeDistModal();
  updateStepBadge();
  renderDistPanel();
  render();
}

function closeDistModal() {
  document.getElementById('dist-modal-bg').style.display = 'none';
}

function closeDistModalBg(e) {
  if (e.target === document.getElementById('dist-modal-bg')) closeDistModal();
}

// Keyboard shortcuts ────────────────────────────────────────────── 

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') { closeModal(); closeDistModal(); }
  if (e.key === 'Enter') {
    if (pendingEdge) { submitEdgeModal(); return; }
    if (document.getElementById('dist-modal-bg').style.display !== 'none') {
      submitDistModal(); return;
    }
  }
  if ((e.key === 'Delete' || e.key === 'Backspace') &&
      document.activeElement.tagName !== 'INPUT') deleteSelected();
});

function drawDistChart() {
  const cv = document.getElementById('mk-dist-chart');
  if (!cv) return;
  const n = state.nodes.length;
  cv.style.display = (n && state.prob) ? 'block' : 'none';
  if (!n || !state.prob) return;
 
  const W = cv.width = cv.clientWidth * (window.devicePixelRatio || 1);
  const H = cv.height = 90 * (window.devicePixelRatio || 1);
  const g = cv.getContext('2d');
  g.clearRect(0, 0, W, H);
  const pad = 4 * (window.devicePixelRatio || 1);
  const bw  = (W - pad * 2) / n;
  const fs  = 10 * (window.devicePixelRatio || 1);
  g.font = `${fs}px sans-serif`;
  g.textAlign = 'center';
 
  for (let i = 0; i < n; i++) {
    const p = state.prob[i];
    const h = p * (H - fs * 2.4);
    const x = pad + i * bw;
    g.fillStyle = state.nodes[i].color;
    g.fillRect(x + bw * 0.15, H - fs * 1.4 - h, bw * 0.7, h);
    g.fillStyle = getComputedStyle(document.body).getPropertyValue('--muted') || '#888';
    g.fillText(state.nodes[i].label, x + bw / 2, H - 2);
    if (p > 0.001)
      g.fillText((p * 100).toFixed(0) + '%', x + bw / 2,
                 Math.max(fs, H - fs * 1.8 - h));
  }
}
 
// Probability-vs-time line chart in the strip under the graph.
function renderHistoryChart() {
  const cv = document.getElementById('mk-history-canvas');
  if (!cv) return;
  const strip = document.getElementById('mk-history-strip');
  const hasData = state.fullHistory.length > 1;
  if (strip) strip.style.display = hasData ? 'block' : 'none';
  if (!hasData) return;
 
  const dpr = window.devicePixelRatio || 1;
  const W = cv.width  = cv.clientWidth * dpr;
  const H = cv.height = cv.clientHeight * dpr;
  const g = cv.getContext('2d');
  g.clearRect(0, 0, W, H);
 
  const padL = 30 * dpr, padR = 8 * dpr, padT = 8 * dpr, padB = 16 * dpr;
  const iw = W - padL - padR, ih = H - padT - padB;
  const T = state.fullHistory;
  const t0 = T[0].t, t1 = T[T.length - 1].t || 1;
  const X = t => padL + iw * (t - t0) / Math.max(1e-9, t1 - t0);
  const Y = p => padT + ih * (1 - p);
 
  const muted = getComputedStyle(document.body).getPropertyValue('--muted') || '#888';
  g.strokeStyle = muted; g.lineWidth = dpr * 0.6; g.globalAlpha = 0.5;
  for (const p of [0, 0.5, 1]) {                       // gridlines 0 / ½ / 1
    g.beginPath(); g.moveTo(padL, Y(p)); g.lineTo(W - padR, Y(p)); g.stroke();
  }
  g.globalAlpha = 1;
  g.fillStyle = muted; g.font = `${9 * dpr}px sans-serif`; g.textAlign = 'right';
  g.fillText('1', padL - 3 * dpr, Y(1) + 3 * dpr);
  g.fillText('½', padL - 3 * dpr, Y(0.5) + 3 * dpr);
  g.fillText('0', padL - 3 * dpr, Y(0) + 3 * dpr);
  g.textAlign = 'center';
  g.fillText(state.mode === 'ctmc' ? 'time t' : 'step', padL + iw / 2, H - 3 * dpr);
 
  state.nodes.forEach((nd, i) => {
    g.strokeStyle = nd.color; g.lineWidth = 1.4 * dpr;
    g.beginPath();
    T.forEach((s, k) => {
      const x = X(s.t), y = Y(s.p[i] ?? 0);
      k === 0 ? g.moveTo(x, y) : g.lineTo(x, y);
    });
    g.stroke();
  });
}
 
window.addEventListener('resize', () => { drawDistChart(); renderHistoryChart(); });