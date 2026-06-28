'use strict';

function onCSVChosen(file) {
  const reader = new FileReader();
  reader.onload = e => {
    const grid = parseCSV(e.target.result);
    if (grid.length < 2) { alert('CSV needs a header row and at least one data row.'); return; }
    DATA.headers = grid[0].map(h => h.trim());
    DATA.rows    = grid.slice(1);
    DATA.numericIdx = DATA.headers.map((_, c) => c).filter(c => isNumericColumn(DATA.rows, c));
    if (DATA.numericIdx.length < 3) {
      alert('Need at least 3 numeric columns; found ' + DATA.numericIdx.length + '.');
      return;
    }
    DATA.sel = null;
    openColumnModal();
  };
  reader.onerror = () => alert('Could not read the file.');
  reader.readAsText(file);
}

function buildColumnModal() {
  if (document.getElementById('de-modal-bg')) return;
  const bg = document.createElement('div');
  bg.className = 'modal-bg';
  bg.id = 'de-modal-bg';
  bg.style.display = 'none';
  bg.innerHTML = `
    <div class="modal">
      <h3>Map CSV Columns</h3>
      <div class="desc">Choose three numeric columns for the X, Y and Z axes,
        and, optionally, a column to colour points by category.</div>

      <div class="field-row"><label style="width:auto;min-width:64px">X axis</label><select id="de-x" class="de-select"></select></div>
      <div class="field-row"><label style="width:auto;min-width:64px">Y axis</label><select id="de-y" class="de-select"></select></div>
      <div class="field-row"><label style="width:auto;min-width:64px">Z axis</label><select id="de-z" class="de-select"></select></div>
      <div class="field-row"><label style="width:auto;min-width:64px">Colour</label><select id="de-cat" class="de-select"></select></div>

      <label style="font-size:12px;display:flex;align-items:center;gap:6px;margin-top:8px">
        <input type="checkbox" id="de-standardise" checked/> Standardise each axis (z-score)
      </label>
      <div class="error-msg" id="de-modal-err"></div>
      <div class="modal-actions">
        <button class="btn" id="de-cancel">Cancel</button>
        <button class="btn primary" id="de-apply">Plot points</button>
      </div>
    </div>`;
  bg.addEventListener('click', e => { if (e.target === bg) bg.style.display = 'none'; });
  document.body.appendChild(bg);
  document.getElementById('de-cancel').addEventListener('click', () => { bg.style.display = 'none'; });
  document.getElementById('de-apply').addEventListener('click', applyColumnModal);
}

function openColumnModal() {
  buildColumnModal();

  const numOpts = DATA.numericIdx
    .map(c => `<option value="${c}">${DATA.headers[c]}</option>`).join('');
  const allOpts = '<option value="-1">None</option>' +
    DATA.headers.map((h, c) => `<option value="${c}">${h}</option>`).join('');

  const x = document.getElementById('de-x'), y = document.getElementById('de-y'),
        z = document.getElementById('de-z'), cat = document.getElementById('de-cat');

  x.innerHTML = y.innerHTML = z.innerHTML = numOpts;
  cat.innerHTML = allOpts;
  const sel = DATA.sel;

  if (sel) {
    x.value = sel.cx; y.value = sel.cy; z.value = sel.cz; cat.value = sel.cc;
    document.getElementById('de-standardise').checked = sel.standardise;
  } else {
    x.selectedIndex = 0;
    y.selectedIndex = Math.min(1, DATA.numericIdx.length - 1);
    z.selectedIndex = Math.min(2, DATA.numericIdx.length - 1);
  }

  document.getElementById('de-modal-err').textContent = '';
  document.getElementById('de-modal-bg').style.display = 'flex';
}

function applyColumnModal() {
  const cx = +document.getElementById('de-x').value;
  const cy = +document.getElementById('de-y').value;
  const cz = +document.getElementById('de-z').value;
  const cc = +document.getElementById('de-cat').value;
  const standardise = document.getElementById('de-standardise').checked;
  const err = document.getElementById('de-modal-err');

  if (cx === cy || cx === cz || cy === cz) {
    err.textContent = 'Pick three different columns for X, Y and Z.';
    return;
  }

  const raw = [], cats = [];
  for (const r of DATA.rows) {
    const vx = parseFloat(r[cx]), vy = parseFloat(r[cy]), vz = parseFloat(r[cz]);
    if (!isFinite(vx) || !isFinite(vy) || !isFinite(vz)) continue;
    raw.push([vx, vy, vz]);
    cats.push(cc >= 0 ? (r[cc] ?? '').trim() : null);
  }
  if (!raw.length) { err.textContent = 'No rows with valid numeric values.'; return; }

  DATA.pts  = preprocess(raw, standardise);
  DATA.cats = cc >= 0 ? cats : null;
  DATA.sel  = { cx, cy, cz, cc, standardise };
  document.getElementById('de-modal-bg').style.display = 'none';

  clearAnalysis();
  buildPointCloud();
  if (typeof resetCamera === 'function') resetCamera();
  document.getElementById('data-analysis').style.display = 'block';
  document.getElementById('data-summary').textContent =
    `${DATA.pts.length} points · axes: ${DATA.headers[cx]}, ${DATA.headers[cy]}, ${DATA.headers[cz]}`
    + (cc >= 0 ? ` · coloured by ${DATA.headers[cc]}` : '');
}

let legendOpen = true;

function renderLegend() {
  const el = document.getElementById('data-legend');
  if (!el) return;
  if (!DATA.cats) { el.innerHTML = ''; return; }

  let rows = '';
  for (const [cat, col] of DATA.catColors)
    rows += `<div class="de-legend-row"><span class="de-swatch" style="background:${col}"></span>` +
            `<span>${cat || '(blank)'}</span></div>`;

  el.innerHTML =
    `<div class="de-legend-head${legendOpen ? '' : ' collapsed'}" id="de-legend-head">` +
      `<span>Categories</span><span class="chevron">▾</span></div>` +
    `<div id="de-legend-list" style="display:${legendOpen ? 'block' : 'none'}">${rows}</div>`;
  document.getElementById('de-legend-head').addEventListener('click', toggleLegend);
}

function toggleLegend() {
  legendOpen = !legendOpen;
  const list = document.getElementById('de-legend-list');
  const head = document.getElementById('de-legend-head');
  if (list) list.style.display = legendOpen ? 'block' : 'none';
  if (head) head.classList.toggle('collapsed', !legendOpen);
}

// SVD frames animation ────────────────────────────────────────────── 

function renderSVDStep() {
  const d = DATA.svd; if (!d) return;
  document.getElementById('svd-step-label').textContent = SVD_STEPS[d.step].label;
  const key = SVD_STEPS[d.step].key;
  let mat, caption;
  if (key === 'I')      { mat = identity3();                                   caption = 'I'; }
  else if (key === 'Vt'){ mat = d.Vt;                                      caption = 'Vᵀ'; }
  else if (key === 'S') { mat = [d.S[0],0,0, 0,d.S[1],0, 0,0,d.S[2]];      caption = 'Σ'; }
  else                  { mat = d.U;                                       caption = 'U'; }
  document.getElementById('svd-matrix').textContent = caption + ' =\n' + fmtMat3(mat);
}

function fmtMat3(m) {
  const f = v => (v >= 0 ? ' ' : '-') + Math.abs(v).toFixed(3);
  let out = '';
  for (let r = 0; r < 3; r++)
    out += '[' + f(m[r*3]) + ' ' + f(m[r*3+1]) + ' ' + f(m[r*3+2]) + ' ]\n';
  return out;
}

// Reset/clear analysis/data ────────────────────────────────────────────── 

function clearAnalysis() {
  if (DATA.fitLine) { scene.remove(DATA.fitLine); DATA.fitLine.geometry.dispose(); DATA.fitLine = null; }
  stopSVD();
}

function clearData() {
  clearAnalysis();
  if (DATA.cloud) { scene.remove(DATA.cloud); DATA.cloud = null; }
  DATA.pts = []; DATA.cats = null; DATA.sel = null;
  const hide = document.getElementById('chk-hide-data');
  if (hide) hide.checked = false;
  document.getElementById('data-analysis').style.display = 'none';
  document.getElementById('data-summary').textContent = '';
  const lg = document.getElementById('data-legend'); if (lg) lg.innerHTML = '';
}

function initDataEngineering() {
  if (typeof sectionOpen !== 'undefined') sectionOpen.data = true;

  const file = document.getElementById('csv-input');
  if (file) file.addEventListener('change', e => {
    if (e.target.files[0]) onCSVChosen(e.target.files[0]);
    e.target.value = '';
  });

  bind('btn-fit-line', toggleFitLine);
  bind('btn-change-cols', openColumnModal);

  const hide = document.getElementById('chk-hide-data');
  if (hide) hide.addEventListener('change', () => {
    if (DATA.cloud) DATA.cloud.visible = !hide.checked;
  });
  bind('btn-svd',      () => { DATA.svd ? stopSVD() : startSVD(); });
  bind('btn-clear-data', clearData);
  bind('btn-svd-next', () => svdGoto((DATA.svd?.step ?? 0) + 1));
  bind('btn-svd-prev', () => svdGoto((DATA.svd?.step ?? 0) - 1));
  bind('btn-svd-reset', () => svdGoto(0));
}

function bind(id, fn) {
  const el = document.getElementById(id);
  if (el) el.addEventListener('click', fn);
}

if (document.readyState === 'loading')
  document.addEventListener('DOMContentLoaded', initDataEngineering);
else
  initDataEngineering();