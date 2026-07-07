'use strict';

const sectionOpen = { data: true };
 
function toggleSection(id) {
  sectionOpen[id] = !sectionOpen[id];
  const body = document.getElementById('section-' + id);
  const head = document.getElementById('shead-' + id);
  if (body) body.style.display = sectionOpen[id] ? 'block' : 'none';
  if (head) head.classList.toggle('collapsed', !sectionOpen[id]);
}

// Col Modal ────────────────────────────────────────────── 

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
        and, optionally, a column to color points by category.</div>

      <div class="field-row"><label style="width:auto;min-width:64px">X axis</label><select id="de-x" class="de-select"></select></div>
      <div class="field-row"><label style="width:auto;min-width:64px">Y axis</label><select id="de-y" class="de-select"></select></div>
      <div class="field-row"><label style="width:auto;min-width:64px">Z axis</label><select id="de-z" class="de-select"></select></div>
      <div class="field-row"><label style="width:auto;min-width:64px">color</label><select id="de-cat" class="de-select"></select></div>

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
    + (cc >= 0 ? ` · colored by ${DATA.headers[cc]}` : '');
}

// Legend ────────────────────────────────────────────── 

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

function renderPCAStep() {
  const d = DATA.pca; if (!d) return;
  if (pcaSvdOpen) renderPCASVDLink();

  const st = PCA_STEPS[d.step];
  document.getElementById('pca-step-label').textContent = st.label;
  const why = document.getElementById('pca-step-why');
  if (why) why.textContent = st.why;

  const total = d.values.reduce((a, b) => a + Math.max(0, b), 0) || 1;
  const surviving = 3 - d.step;
  const dropping = PCA_DROP[d.step];
  const hex = c => '#' + c.toString(16).padStart(6, '0');
  const legend = document.getElementById('pca-legend');
  if (legend) legend.innerHTML = [0, 1, 2].map(c => {
    const share = (Math.max(0, d.values[c]) / total * 100).toFixed(1);
    const dropped = c >= surviving;
    const isNext = c === dropping;
    const cls = 'pca-pc' + (dropped ? ' dropped' : '') + (isNext ? ' dropping' : '');
    return `<div class="${cls}"><span class="pca-swatch" style="background:${hex(PC_COLORS[c])}"></span>` +
           `<span class="pca-pc-name">${PC_NAMES[c]}</span>` +
           `<span class="pca-pc-var">${share}% var</span>` +
           `${isNext ? '<span class="pca-pc-tag">removing →</span>' : ''}</div>`;
  }).join('');

  const dropEl = document.getElementById('pca-dropped');
  if (dropEl) {
    const justDropped = st.dim < 3 ? st.dim : null;
    if (justDropped !== null) {
      const share = (Math.max(0, d.values[justDropped]) / total * 100).toFixed(1);
      dropEl.innerHTML = `Dropped <strong>${PC_NAMES[justDropped]}</strong> — the ` +
        `direction of least remaining variance (${share}%).`;
      dropEl.style.display = 'block';
    } else {
      dropEl.style.display = 'none';
    }
  }
 
  const rv = document.getElementById('pca-retained');
  if (rv) rv.textContent =
    'Variance retained: ' + (d.retained[d.step] * 100).toFixed(1) + '%';
  document.getElementById('pca-matrix').textContent =
    'P =\n' + fmtMat3(d.projs[d.step]);
}

// PCA via SVD ──────────────────────────────────────────────

let pcaSvdOpen = false;
 
function renderPCASVDLink() {
  const d = DATA.pca; if (!d || !d.svdlink) return;
  const L = d.svdlink;
  const f = v => v.toFixed(3).padStart(9);
  let rows = ' i   σᵢ (SVD of X)   √((n−1)λᵢ)   |vᵢ·PCᵢ|\n';
  for (let i = 0; i < 3; i++)
    rows += ` ${i + 1}   ${f(L.sigma[i])}      ${f(L.fromC[i])}     ${L.align[i].toFixed(6)}\n`;
  rows += `\n(n = ${L.n} points — identical columns and alignments of 1\n mean both routes produce the same decomposition)`;
  document.getElementById('pca-svd-table').textContent = rows;
}
 
function togglePCASVD() {
  pcaSvdOpen = !pcaSvdOpen;
  const body = document.getElementById('pca-svd-body');
  const head = document.getElementById('pca-svd-head');
  if (body) body.style.display = pcaSvdOpen ? 'block' : 'none';
  if (head) head.classList.toggle('collapsed', !pcaSvdOpen);
  if (pcaSvdOpen) renderPCASVDLink();
}

function fmtMat3(m) {
  const f = v => (v >= 0 ? ' ' : '-') + Math.abs(v).toFixed(3);
  let out = '';
  for (let r = 0; r < 3; r++)
    out += '[' + f(m[r*3]) + ' ' + f(m[r*3+1]) + ' ' + f(m[r*3+2]) + ' ]\n';
  return out;
}

// Reset/clear analysis/data ────────────────────────────────────────────── 

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
  bind('btn-pca',      () => { DATA.pca ? stopPCA() : startPCA(); });
  bind('btn-pca-next', () => pcaGoto((DATA.pca?.step ?? 0) + 1));
  bind('btn-pca-prev', () => pcaGoto((DATA.pca?.step ?? 0) - 1));
  bind('btn-pca-reset',() => pcaGoto(0));
  bind('pca-svd-head', togglePCASVD);
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