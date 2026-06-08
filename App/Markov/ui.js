'use strict';

// Section 

const sectionOpen = { nodes: true, sim: true };

function toggleSection(id) {
  sectionOpen[id] = !sectionOpen[id];
  const body = document.getElementById('section-' + id);
  const head = document.getElementById('shead-' + id);
  if (body) body.style.display = sectionOpen[id] ? 'block' : 'none';
  if (head) head.classList.toggle('collapsed', !sectionOpen[id]);
}

// Render sidebar

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
  
  const { P } = buildMatrix();
  let html =
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

// ═══════════════════════════════════════════════════════════════════
//  EDGE WEIGHT MODAL
//  Depends on: markov.js (state), scene.js (edgeBetween)
// ═══════════════════════════════════════════════════════════════════

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

// Dist mopal

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
  state.prob    = v;
  state.history = [v.slice()];
  state.step    = 0;
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

// Keyboard shortcuts

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