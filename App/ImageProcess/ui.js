'use strict';
 
function initUI() {
  bindSectionToggles();
  bindSidebarButtons();
  bindFileInput();
  bindColorModal();
  bindBlurModal();
}
 
// Section collapse/expand ───────────────────────────────────────
 
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
 
// Sidebar action buttons ────────────────────────────────────────
 
function bindSidebarButtons() {
  on('btn-color',     openColorModal);
  on('btn-blur',      openBlurModal);
  on('btn-compress',  openCompressModal);
  on('compress-cancel', () => { document.getElementById('compress-modal-bg').style.display = 'none'; });
  on('compress-apply', applyCompress_UI);
  on('btn-sobel', () => {
    const l = getActiveLayer();
    if (!l) return warn('Select a layer first.');
    applySobelEdge(l);
    refreshStepsList();
    renderFrame();
  });
  on('btn-undo',      undoActiveLayer);
  on('btn-move-up',   moveLayerUp);
  on('btn-move-down', moveLayerDown);
  on('btn-delete',    removeActiveLayer);
  on('btn-save', () => {
    const l = getActiveLayer();
    if (l) saveLayer(l); else warn('Select a layer first.');
  });
}
 
function on(id, fn) {
  document.getElementById(id)?.addEventListener('click', fn);
}
 
// File input ────────────────────────────────────────────────────

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
 

// Layer list ────────────────────────────────────────────────────
 
function refreshLayerList() {
  const list  = document.getElementById('layer-list');
  const noMsg = document.getElementById('no-layers-msg');
  list.innerHTML = '';
  if (noMsg) noMsg.style.display = IMG.layers.length ? 'none' : '';

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
 
// Steps panel ───────────────────────────────────────────────────

let dragOpIdx = null;
 
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
  const opIdx      = i - 1;
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
 
  if (isOriginal) return row;

  const del = Object.assign(document.createElement('button'), {
    className:   'step-del',
    textContent: '×',
    title:       'Remove this filter from the pipeline',
  });
  del.addEventListener('click', e => {
    e.stopPropagation();
    removeLayerOp(opIdx);
  });
  row.appendChild(del);

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
 
// Warning flash ─────────────────────────────────────────────────
 
function warn(msg) {
  const el = document.getElementById('sidebar-warning');
  if (!el) return;
  el.textContent   = msg;
  el.style.opacity = '1';
  clearTimeout(el.t);
  el.t = setTimeout(() => { el.style.opacity = '0'; }, 2500);
}
 
// color Filter Modal ────────────────────────────────────────────── 
 
function openColorModal() {
  if (!getActiveLayer()) return warn('Select a layer first.');

  [['relR', 100, '%'], ['relG', 100, '%'], ['relB', 100, '%']].forEach(([id, val, sfx]) => {
    document.getElementById('color-' + id).value = val;
    document.getElementById('color-' + id + '-label').textContent = val + sfx;
  });

  [['absR', 0], ['absG', 0], ['absB', 0]].forEach(([id, val]) => {
    document.getElementById('color-' + id).value = val;
    document.getElementById('color-' + id + '-label').textContent = '0';
  });

  document.querySelector('input[name="color-type"][value="color"]').checked = true;
  document.getElementById('color-gray').value = 100;
  document.getElementById('color-gray-label').textContent = '100%';
  document.getElementById('color-inv').value = 100;
  document.getElementById('color-inv-label').textContent = '100%';
  setColorType('color');
  document.getElementById('color-modal-bg').style.display = 'flex';
}
 
function bindColorModal() {

  document.querySelectorAll('input[name="color-type"]').forEach(r =>
    r.addEventListener('change', () => setColorType(r.value))
  );

  ['relR', 'relG', 'relB'].forEach(id => {
    const s = document.getElementById('color-' + id);
    const l = document.getElementById('color-' + id + '-label');
    s.addEventListener('input', () => { l.textContent = s.value + '%'; });
  });

  ['absR', 'absG', 'absB'].forEach(id => {
    const s = document.getElementById('color-' + id);
    const l = document.getElementById('color-' + id + '-label');
    s.addEventListener('input', () => {
      const v = +s.value;
      l.textContent = (v >= 0 ? '+' : '') + v;
    });
  });
  on('color-cancel', () => { document.getElementById('color-modal-bg').style.display = 'none'; });
  on('color-apply',  applyColor);

  ['gray', 'inv'].forEach(id => {
    const s = document.getElementById('color-' + id);
    const l = document.getElementById('color-' + id + '-label');
    if (s && l) s.addEventListener('input', () => { l.textContent = s.value + '%'; });
  });
}
 
function setColorType(type) {
  document.getElementById('color-adjust-fields').style.display = type === 'color'    ? '' : 'none';
  document.getElementById('sepia-fields').style.display         = type === 'sepia'     ? '' : 'none';
  document.getElementById('grayscale-fields').style.display     = type === 'grayscale' ? '' : 'none';
  document.getElementById('inversion-fields').style.display     = type === 'inversion' ? '' : 'none';
  document.getElementById('rotation-fields').style.display      = type === 'rotation'  ? '' : 'none';
}
 
function applyColor() {
  const l = getActiveLayer();
  if (!l) return;
  const type = document.querySelector('input[name="color-type"]:checked')?.value;
  if (type === 'sepia') {
    applySepiaFilter(l);
  } else if (type === 'grayscale') {
    applyGrayscale(l, +document.getElementById('color-gray').value / 100);
  } else if (type === 'inversion') {
    applyInversion(l, +document.getElementById('color-inv').value / 100);
  } else if (type === 'rotation') {
    applyColorRotation(l, document.getElementById('color-rot').value);
  } else {
    applyColorFilter(
      l,
      +document.getElementById('color-relR').value / 100,
      +document.getElementById('color-relG').value / 100,
      +document.getElementById('color-relB').value / 100,
      +document.getElementById('color-absR').value,
      +document.getElementById('color-absG').value,
      +document.getElementById('color-absB').value,
    );
  }
  refreshStepsList();
  renderFrame();
  document.getElementById('color-modal-bg').style.display = 'none';
}
 
// Blur Modal ──────────────────────────────────────────────
 
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

function openCompressModal() {
  if (!getActiveLayer()) return warn('Select a layer first.');
  const bg = document.getElementById('compress-modal-bg');
  if (!bg) return warn('Compress dialog is missing from the page.');
  const err = document.getElementById('compress-error');
  if (err) err.textContent = '';
  document.getElementById('compress-k')?.classList.remove('err');
  bg.style.display = 'flex';
}
 
function applyCompress_UI() {
  const l = getActiveLayer(); if (!l) return;
  const k = parseInt(document.getElementById('compress-k').value, 10);
  if (isNaN(k) || k < 1) {
    document.getElementById('compress-k').classList.add('err');
    document.getElementById('compress-error').textContent = 'k must be a positive integer.';
    return;
  }
  document.getElementById('compress-modal-bg').style.display = 'none';
  applyCompress(l, k);
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

