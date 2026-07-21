'use strict';

function serialiseData() {
  return { rows: DATA.rows, headers: DATA.headers, sel: DATA.sel };
}

function restoreData(p) {
  if (!p || !Array.isArray(p.rows) || !Array.isArray(p.headers))
    return 'This save does not look like a dataset.';
  DATA.headers = p.headers.map(h => String(h));
  DATA.rows = p.rows.filter(r => Array.isArray(r));
  DATA.numericIdx = DATA.headers.map((_, c) => c)
    .filter(c => isNumericColumn(DATA.rows, c));
  if (DATA.numericIdx.length < 3)
    return 'Saved data has fewer than 3 numeric columns.';

  const sel = p.sel;
  if (!sel || ![sel.cx, sel.cy, sel.cz].every(i => Number.isInteger(i))) {
    DATA.sel = null;
    openColumnModal();
    return null;
  }
  
  const { cx, cy, cz, cc, standardize } = sel;
  const raw = [], cats = [];
  for (const r of DATA.rows) {
    const vx = parseFloat(r[cx]), vy = parseFloat(r[cy]), vz = parseFloat(r[cz]);
    if (!isFinite(vx) || !isFinite(vy) || !isFinite(vz)) continue;
    raw.push([vx, vy, vz]);
    cats.push(cc >= 0 ? (r[cc] ?? '').trim() : null);
  }
  if (!raw.length) return 'Saved column mapping fits no rows.';
  DATA.pts = preprocess(raw, !!standardize);
  DATA.cats = cc >= 0 ? cats : null;
  DATA.sel = { cx, cy, cz, cc, standardize: !!standardize };
  clearAnalysis();
  buildPointCloud();
  if (typeof resetCamera === 'function') resetCamera();
  document.getElementById('data-analysis').style.display = 'block';
  document.getElementById('data-summary').textContent =
    `${DATA.pts.length} points · axes: ${DATA.headers[cx]}, ${DATA.headers[cy]}, ${DATA.headers[cz]}`
    + (cc >= 0 ? ` · coloured by ${DATA.headers[cc]}` : '');
  return null;
}

initToolSave({
  tool: 'data',
  serialise: serialiseData,
  restore: restoreData,
  empty: () => DATA.rows?.length ? false : 'Load a dataset first.',
});