'use strict';
 
function initUI() {
  bindSectionToggles();
  bindSidebarButtons();
  bindFileInput();
  bindColourModal();
  bindBlurModal();
}
 
// ── Section collapse/expand ───────────────────────────────────────
 
function bindSectionToggles() {
  document.querySelectorAll('.section-head').forEach(head => {
    head.addEventListener('click', () => {
      head.classList.toggle('collapsed');
      const body = head.nextElementSibling;
      if (body?.classList.contains('section-body'))
        body.style.display = head.classList.contains('collapsed') ? 'none' : '';
    });
  });
}
 
// ── Sidebar action buttons ────────────────────────────────────────
 
function bindSidebarButtons() {
  on('btn-colour',    openColourModal);
  on('btn-blur',      openBlurModal);
  on('btn-sobel', () => {
    const l = getActiveLayer();
    if (!l) return warn('Select an image first.');
    applySobelEdge(l);
    refreshStepsList();
    renderFrame();
  });
  on('btn-undo',      undoActiveLayer);
  on('btn-delete',    removeActiveLayer);
  on('btn-save', () => {
    const l = getActiveLayer();
    if (l) saveLayer(l); else warn('Select an image first.');
  });
}
 
function on(id, fn) {
  document.getElementById(id)?.addEventListener('click', fn);
}
 
// ── File input ────────────────────────────────────────────────────

const ALLOWED_TYPES = new Set(['image/png','image/jpeg','image/gif','image/bmp','image/webp']);

function bindFileInput() {
  document.getElementById('file-input').addEventListener('change', async e => {
    const files = Array.from(e.target.files);
    for (const file of files) {
      if (!ALLOWED_TYPES.has(file.type)) {
        warn(`"${file.name}" is not a supported image type (PNG, JPG, GIF, BMP, WebP).`);
        continue;
      }
      try {
        const layer = await layerFromFile(file);
        addLayer(layer);
      } catch {
        warn(`"${file.name}" could not be decoded — the file may be corrupt.`);
      }
    }
    e.target.value = '';
  });
}
 

// ── Layer list ────────────────────────────────────────────────────
 
function refreshLayerList() {
  const list  = document.getElementById('layer-list');
  const noMsg = document.getElementById('no-layers-msg');
  list.innerHTML = '';
  if (noMsg) noMsg.style.display = IMG.layers.length ? 'none' : '';
 
  // Display top-to-bottom (visually on top = highest index)
  [...IMG.layers].reverse().forEach(layer => {
    const row  = document.createElement('div');
    row.className = 'obj-row' + (layer.id === IMG.activeId ? ' active' : '');
 
    const dot  = Object.assign(document.createElement('span'), { className: 'obj-dot' });
    const name = Object.assign(document.createElement('span'), {
      className:   'layer-name',
      textContent: layer.name,
      title:       layer.name,
    });
    row.append(dot, name);
    row.addEventListener('click', () => selectLayer(layer.id));
    list.appendChild(row);
  });
}
 
// ── Steps panel ───────────────────────────────────────────────────

let dragOpIdx = null;   // op index being dragged, or null
 
function refreshStepsList() {
  const list  = document.getElementById('step-list');
  const noMsg = document.getElementById('no-steps-msg');
  if (!list) return;
  list.innerHTML = '';
 
  const l = getActiveLayer();
  if (noMsg) noMsg.style.display = l ? 'none' : '';
  if (!l) return;
 
  for (let i = 0; i < l.stepCount; i++)
    list.appendChild(buildStepRow(l, i));
}
 
function buildStepRow(l, i) {
  const isOriginal = i === 0;
  const opIdx      = i - 1;                       // index into l.ops
  const op         = isOriginal ? null : l.ops[opIdx];
 
  const row = document.createElement('div');
  row.className = 'obj-row step-row'
    + (i === l.step ? ' active' : '')
    + (i >  l.step ? ' future' : '');
 
  const idx  = Object.assign(document.createElement('span'), {
    className:   'step-idx',
    textContent: i,
  });
  const name = Object.assign(document.createElement('span'), {
    className:   'layer-name',
    textContent: isOriginal ? 'Original' : op.label,
    title:       isOriginal ? l.name : (op.detail || op.label),
  });
  row.append(idx, name);
  row.addEventListener('click', () => gotoLayerStep(i));
 
  if (isOriginal) return row;                     // not draggable, not deletable
 
  // ── Delete ──
  const del = Object.assign(document.createElement('button'), {
    className:   'step-del',
    textContent: '×',
    title:       'Remove this filter from the pipeline',
  });
  del.addEventListener('click', e => {
    e.stopPropagation();                          // don't also jump to the step
    removeLayerOp(opIdx);
  });
  row.appendChild(del);
 
  // ── Drag to reorder ──
  row.draggable = true;
  row.addEventListener('dragstart', e => {
    dragOpIdx = opIdx;
    e.dataTransfer.effectAllowed = 'move';
    row.classList.add('dragging');
  });
  row.addEventListener('dragend', () => {
    dragOpIdx = null;
    row.classList.remove('dragging');
    document.querySelectorAll('.step-row.drag-over')
            .forEach(r => r.classList.remove('drag-over'));
  });
  row.addEventListener('dragover', e => {
    if (dragOpIdx === null || dragOpIdx === opIdx) return;
    e.preventDefault();                           // required to allow drop
    e.dataTransfer.dropEffect = 'move';
    row.classList.add('drag-over');
  });
  row.addEventListener('dragleave', () => row.classList.remove('drag-over'));
  row.addEventListener('drop', e => {
    e.preventDefault();
    row.classList.remove('drag-over');
    if (dragOpIdx !== null && dragOpIdx !== opIdx)
      moveLayerOp(dragOpIdx, opIdx);
  });
 
  return row;
}
 
// ── Warning flash ─────────────────────────────────────────────────
 
function warn(msg) {
  const el = document.getElementById('sidebar-warning');
  if (!el) return;
  el.textContent   = msg;
  el.style.opacity = '1';
  clearTimeout(el.t);
  el.t = setTimeout(() => { el.style.opacity = '0'; }, 2500);
}
 
// ── Colour Filter Modal ────────────────────────────────────────────── 
 
function openColourModal() {
  if (!getActiveLayer()) return warn('Select an image first.');
  // Reset to defaults each open
  [['relR', 100, '%'], ['relG', 100, '%'], ['relB', 100, '%']].forEach(([id, val, sfx]) => {
    document.getElementById('colour-' + id).value = val;
    document.getElementById('colour-' + id + '-label').textContent = val + sfx;
  });
  [['absR', 0], ['absG', 0], ['absB', 0]].forEach(([id, val]) => {
    document.getElementById('colour-' + id).value = val;
    document.getElementById('colour-' + id + '-label').textContent = '0';
  });
  document.querySelector('input[name="colour-type"][value="colour"]').checked = true;
  setColourType('colour');
  document.getElementById('colour-modal-bg').style.display = 'flex';
}
 
function bindColourModal() {
  document.querySelectorAll('input[name="colour-type"]').forEach(r =>
    r.addEventListener('change', () => setColourType(r.value))
  );

  // Relative sliders
  ['relR', 'relG', 'relB'].forEach(id => {
    const s = document.getElementById('colour-' + id);
    const l = document.getElementById('colour-' + id + '-label');
    s.addEventListener('input', () => { l.textContent = s.value + '%'; });
  });

  // Absolute sliders
  ['absR', 'absG', 'absB'].forEach(id => {
    const s = document.getElementById('colour-' + id);
    const l = document.getElementById('colour-' + id + '-label');
    s.addEventListener('input', () => {
      const v = +s.value;
      l.textContent = (v >= 0 ? '+' : '') + v;
    });
  });
  on('colour-cancel', () => { document.getElementById('colour-modal-bg').style.display = 'none'; });
  on('colour-apply',  applyColour);
}
 
function setColourType(type) {
  document.getElementById('colour-adjust-fields').style.display = type === 'colour' ? '' : 'none';
  document.getElementById('sepia-fields').style.display         = type === 'sepia'  ? '' : 'none';
}
 
function applyColour() {
  const l = getActiveLayer();
  if (!l) return;
  const type = document.querySelector('input[name="colour-type"]:checked')?.value;
  if (type === 'sepia') {
    applySepiaFilter(l);
  } else {
    applyColourFilter(
      l,
      +document.getElementById('colour-relR').value / 100,
      +document.getElementById('colour-relG').value / 100,
      +document.getElementById('colour-relB').value / 100,
      +document.getElementById('colour-absR').value,
      +document.getElementById('colour-absG').value,
      +document.getElementById('colour-absB').value,
    );
  }
  refreshStepsList();
  renderFrame();
  document.getElementById('colour-modal-bg').style.display = 'none';
}
 
/* ── Blur Modal ────────────────────────────────────────────── */
 
function openBlurModal() {
  if (!getActiveLayer()) return warn('Select an image first.');
  document.querySelector('input[name="blur-type"][value="median"]').checked = true;
  setBlurType('median');
  document.getElementById('blur-radius').value  = 1;
  document.getElementById('blur-sd').value      = 1.0;
  document.getElementById('blur-error').textContent = '';
  document.getElementById('blur-sd').classList.remove('err');
  document.getElementById('blur-radius').classList.remove('err');
  document.getElementById('blur-modal-bg').style.display = 'flex';
}
 
function bindBlurModal() {
  document.querySelectorAll('input[name="blur-type"]').forEach(r =>
    r.addEventListener('change', () => setBlurType(r.value))
  );
  on('blur-cancel', () => { document.getElementById('blur-modal-bg').style.display = 'none'; });
  on('blur-apply',  applyBlur);
}
 
function setBlurType(type) {
  document.getElementById('median-radius-row').style.display = type === 'median'   ? '' : 'none';
  document.getElementById('gaussian-sd-row').style.display   = type === 'gaussian' ? '' : 'none';
}
 
function applyBlur() {
  const l     = getActiveLayer();
  if (!l) return;
  const type  = document.querySelector('input[name="blur-type"]:checked')?.value;
  const errEl = document.getElementById('blur-error');
 
  if (type === 'gaussian') {
    const sd = parseFloat(document.getElementById('blur-sd').value);
    if (isNaN(sd) || sd <= 0) {
      document.getElementById('blur-sd').classList.add('err');
      errEl.textContent = 'Standard deviation must be greater than 0.';
      return;
    }
    document.getElementById('blur-sd').classList.remove('err');
    errEl.textContent = '';
    applyGaussianBlur(l, sd);
  } else {
    const r = parseInt(document.getElementById('blur-radius').value, 10);
    if (isNaN(r) || r < 1 || r > 5) {
      document.getElementById('blur-radius').classList.add('err');
      errEl.textContent = 'Kernel radius must be an integer from 1 to 5.';
      return;
    }
    document.getElementById('blur-radius').classList.remove('err');
    errEl.textContent = '';
    applyMedianBlur(l, r);
  }
  refreshStepsList();
  renderFrame();
  document.getElementById('blur-modal-bg').style.display = 'none';
}