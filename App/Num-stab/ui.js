'use strict';

const nsTranspose = m => m[0].map((_, c) => m.map(r => r[c]));

function displayVectorRows(fmtd) {
  return fmtd.map(r => r.map(x => '[' + x + ']').join(' ')).join('\n');
}

function nsRender() {
  const disp = document.getElementById('ns-matrix');
  const opEl = document.getElementById('ns-op');
  const pager = document.getElementById('ns-pager');
  const solnEl = document.getElementById('ns-soln');
  const empty = document.getElementById('ns-empty');

  const has = !!NS.matrix;
  empty.style.display = has ? 'none' : 'block';
  disp.style.display = has ? 'block' : 'none';
  document.getElementById('btn-ns-action').disabled = !has;
  document.getElementById('btn-ns-reset').disabled = !has;
  document.getElementById('ns-calc-acc').disabled = NS.ran;
  if (!has) { opEl.textContent = ''; pager.style.display = 'none'; solnEl.style.display = 'none'; return; }

  const cur = NS.hist.length ? NS.hist[NS.page].m : NS.matrix;
  const fmtd = formatMatrix(cur, NS.displayAcc);
  disp.textContent = NS.vectorLines
    ? displayVectorRows(fmtd)
    : (NS.asMatrix ? displayAsMatrix(fmtd, NS.augcol) : displayAsBasis(fmtd));

  opEl.textContent = NS.hist.length ? NS.hist[NS.page].op : '';
  pager.style.display = NS.hist.length > 1 ? 'flex' : 'none';
  document.getElementById('ns-page-label').textContent =
    `Step ${NS.page + 1} of ${NS.hist.length}`;

  if (NS.soln) {
    solnEl.style.display = 'block';
    solnEl.textContent = NS.soln.text;
    solnEl.style.color = NS.soln.color || 'var(--text)';
  } else solnEl.style.display = 'none';

  if (typeof nsVizRender === 'function') nsVizRender();
}

function nsSetMatrix(m) {
  NS.matrix = m;
  NS.hist = []; NS.page = 0; NS.augcol = 0; NS.asMatrix = true;
  NS.vectorLines = false; NS.gsVectors = null;
  NS.soln = null; NS.ran = false;
  document.getElementById('ns-summary').textContent =
    `${m.length} × ${m[0].length} matrix loaded`;
  nsRender();
}

function nsLoadCSV(file) {
  const reader = new FileReader();
  reader.onload = e => {
    const rows = parseCSV(e.target.result)
      .filter(r => r.length && r.some(c => c.trim().length))
      .map(r => r.map(c => Number(c.trim())));
    if (!rows.length) return alert('CSV is empty.');
    const w = rows[0].length;
    if (rows.some(r => r.length !== w))
      return alert('Matrix has inconsistent dimensions. Please try again.');
    if (rows.some(r => r.some(v => !isFinite(v))))
      return alert('At least one of your entries is invalid. Please try again.');
    nsSetMatrix(rows);
  };
  reader.onerror = () => alert('Could not read the file.');
  reader.readAsText(file);
}

function nsGenerate() {
  const kind = document.querySelector('input[name="ns-gen"]:checked')?.value;
  const err = document.getElementById('ns-gen-err');
  if (kind === 'hilbert') {
    const n = parseInt(document.getElementById('ns-gen-n').value, 10);
    if (!(n >= 2 && n <= 10)) { err.textContent = 'n must be 2 – 10.'; return; }
    nsSetMatrix(hilbertMatrix(n));
  } else {
    const r = parseInt(document.getElementById('ns-gen-rows').value, 10);
    const c = parseInt(document.getElementById('ns-gen-cols').value, 10);
    if (!(r >= 1 && r <= 10 && c >= 1 && c <= 10)) {
      err.textContent = 'Rows and columns must be 1 – 10.'; return;
    }
    nsSetMatrix(randomMatrix(r, c));
  }
  document.getElementById('ns-gen-modal').style.display = 'none';
}

function nsShowActionFields() {
  const a = document.querySelector('input[name="ns-action"]:checked')?.value;
  document.getElementById('ns-gauss-fields').style.display = a === 'gauss' ? 'block' : 'none';
  document.getElementById('ns-gs-fields').style.display = a === 'gs' ? 'block' : 'none';
}

function nsResidualLine(label, r) {
  const verdict = r < 1e-12 ? ['Good', '#2f9e44']
                : r < 1e-8  ? ['Fair', '#e09c30']
                :             ['Poor', '#d6455c'];
  return { text: `${label} = ${r.toExponential(3)}  (${verdict[0]})`,
           color: verdict[1] };
}

function nsRunAction() {
  const a = document.querySelector('input[name="ns-action"]:checked')?.value;
  if (!a) return;
  if (!NS.matrix) return;
  NS.ran = true;

  if (a === 'lu' || a === 'invert' || a === 'diag') { nsRunExtra(a); return; }

  if (a === 'gauss') {
    const pivot = document.querySelector('input[name="ns-pivot"]:checked')?.value === '1';
    NS.augcol = 1; NS.asMatrix = true; NS.vectorLines = false;
    const { hist } = gaussianEliminate(NS.matrix, pivot);
    NS.hist = hist; NS.page = 0;
    const sol = gaussianSolve(NS.matrix, pivot);
    NS.soln = { text: sol.text, color: 'var(--text)' };
  } else {
    const modified = document.querySelector('input[name="ns-gs"]:checked')?.value === '1';
    const normed = document.getElementById('ns-gs-norm').checked;
    const asCols = document.querySelector('input[name="ns-gs-vec"]:checked')?.value === 'cols';
    const vecs = asCols ? nsTranspose(NS.matrix) : mcopy(NS.matrix);
    NS.asMatrix = false; NS.augcol = 0;
    NS.vectorLines = true;
    NS.gsVectors = vecs; 
    const { hist, error } = gramSchmidt(vecs, modified, normed, NS.calcAcc);
    NS.hist = hist; NS.page = 0;
    if (error === null) {
      NS.soln = { text: 'Orthogonality error: N/A (process terminated early)',
                  color: 'var(--muted)' };
    } else {
      const verdict = error < 1e-12 ? ['Good', '#2f9e44']
                    : error < 1e-8  ? ['Fair', '#e09c30']
                    :                 ['Poor', '#d6455c'];
      NS.soln = {
        text: `Orthogonality error ‖QQᵀ − I‖_F = ${error.toExponential(3)}  (${verdict[0]})`,
        color: verdict[1],
      };
    }
  }
  document.getElementById('ns-action-modal').style.display = 'none';
  nsRender();
}

function nsRunExtra(a) {
  if (a === 'lu') {
    const r = luDecompose(NS.matrix);
    if (r.error) { alert(r.error); NS.ran = false; return; }
    NS.asMatrix = true; NS.augcol = 0; NS.vectorLines = false;
    NS.hist = r.hist; NS.page = 0;
    NS.soln = nsResidualLine('PA = LU verified · ‖PA − LU‖_F', r.residual);
  } else if (a === 'invert') {
    const r = invertMatrix(NS.matrix);
    if (r.error) { alert(r.error); NS.ran = false; return; }
    NS.asMatrix = true; NS.vectorLines = false;
    NS.hist = r.hist; NS.page = 0;
    if (r.singular) {
      NS.augcol = NS.matrix.length;
      NS.soln = { text: 'Matrix is singular (rank < n) — no inverse exists.',
                  color: '#d6455c' };
    } else {
      NS.augcol = NS.matrix.length;
      NS.soln = nsResidualLine('‖A·A⁻¹ − I‖_F', r.residual);
    }
  } else if (a === 'diag') {
    const r = diagonalize(NS.matrix);
    if (r.error) { alert(r.error); NS.ran = false; return; }
    NS.asMatrix = true; NS.augcol = 0; NS.vectorLines = false;
    if (r.fail) {
      NS.hist = [{ m: mcopy(NS.matrix), op: 'A — the matrix as loaded' }];
      NS.page = 0;
      NS.soln = { text: r.fail, color: '#d6455c' };
    } else {
      NS.hist = [
        { m: mcopy(NS.matrix), op: 'A — the matrix as loaded' },
        { m: r.D,    op: 'D — eigenvalues on the diagonal' +
                         (r.symmetric ? ' (symmetric input → Jacobi)' : '') },
        { m: r.P,    op: 'P — eigenvector columns' +
                         (r.symmetric ? ' (orthonormal)' : '') },
        { m: r.Pinv, op: 'P⁻¹ — so that A = P D P⁻¹' },
      ];
      NS.page = 0;
      const lams = r.values.map(v => roundTo(v, 4)).join(', ');
      const q = nsResidualLine('‖AP − PD‖_F', r.residual);
      NS.soln = { text: `λ = ${lams}    ·    ${q.text}`, color: q.color };
    }
  }
  document.getElementById('ns-action-modal').style.display = 'none';
  nsRender();
}

function nsInit() {
  const file = document.getElementById('ns-csv');
  file?.addEventListener('change', e => {
    if (e.target.files[0]) nsLoadCSV(e.target.files[0]);
    e.target.value = '';
  });

  const bind = (id, fn) => document.getElementById(id)?.addEventListener('click', fn);
  bind('btn-ns-generate', () => {
    document.getElementById('ns-gen-err').textContent = '';
    document.getElementById('ns-gen-modal').style.display = 'flex';
  });
  bind('ns-gen-apply', nsGenerate);
  bind('ns-gen-cancel', () => { document.getElementById('ns-gen-modal').style.display = 'none'; });
  bind('btn-ns-action', () => {
    document.getElementById('ns-action-modal').style.display = 'flex';
    nsShowActionFields();
  });
  bind('ns-action-apply', nsRunAction);
  bind('ns-action-cancel', () => { document.getElementById('ns-action-modal').style.display = 'none'; });
  bind('btn-ns-reset', () => { if (NS.matrix) nsSetMatrix(NS.matrix); });
  bind('btn-ns-prev', () => { if (NS.page > 0) { NS.page--; nsRender(); } });
  bind('btn-ns-next', () => { if (NS.page < NS.hist.length - 1) { NS.page++; nsRender(); } });

  document.querySelectorAll('input[name="ns-action"]').forEach(r =>
    r.addEventListener('change', nsShowActionFields));
  document.querySelectorAll('input[name="ns-gen"]').forEach(r =>
    r.addEventListener('change', () => {
      const h = document.querySelector('input[name="ns-gen"]:checked')?.value === 'hilbert';
      document.getElementById('ns-gen-size-row').style.display = h ? 'none' : 'block';
      document.getElementById('ns-gen-n-row').style.display = h ? 'flex' : 'none';
    }));

  const dAcc = document.getElementById('ns-display-acc');
  dAcc?.addEventListener('input', () => {
    const v = parseInt(dAcc.value, 10);
    if (v >= 2 && v <= 12) { NS.displayAcc = v; nsRender(); }
  });
  const cAcc = document.getElementById('ns-calc-acc');
  cAcc?.addEventListener('input', () => {
    const v = parseInt(cAcc.value, 10);
    if (v >= 2 && v <= 16) NS.calcAcc = v;
  });

  nsRender();
}

if (document.readyState === 'loading')
  document.addEventListener('DOMContentLoaded', nsInit);
else
  nsInit();