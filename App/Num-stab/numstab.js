'use strict';

const NS = {
  matrix:  null,
  hist:    [],
  page:    0,
  augcol:  0,
  asMatrix: true,
  soln:    null,
  displayAcc: 6,
  calcAcc: 16,
  ran:     false,
};

const roundTo = (x, acc) => {
  const f = Math.pow(10, acc);
  return Math.round(x * f) / f;
};
const vnorm  = v => Math.hypot(...v);
const vdot   = (a, b) => a.reduce((s, x, i) => s + x * b[i], 0);
const mcopy  = m => m.map(r => r.slice());
const infNorm = m => Math.max(...m.map(r => r.reduce((s, x) => s + Math.abs(x), 0)));

// GE

function gaussianEliminate(mat, pivot) {
  const m = mcopy(mat);
  const rows = m.length, cols = m[0].length;
  const hist = [{ m: mcopy(m), op: '' }];
  const norm = infNorm(m);

  let top = 0;
  while (top < rows) {
    const sub = m.slice(top);

    let i = 0;
    for (; i < cols; i++)
      if (sub.some(r => r[i] !== 0)) break;
    if (i === cols) break;

    let swap = 0;
    if (pivot) {
      let best = -1;
      sub.forEach((r, k) => {
        if (Math.abs(r[i]) > best) { best = Math.abs(r[i]); swap = k; }
      });
    } else {
      while (sub[swap][i] === 0) swap++;
    }
    if (swap > 0) {
      [m[top], m[top + swap]] = [m[top + swap], m[top]];
      hist.push({ m: mcopy(m), op: `R${top + 1} ↔ R${top + swap + 1}` });
    }

    for (let k = top + 1; k < rows; k++) {
      const coeff = m[k][i] / m[top][i];
      for (let c = 0; c < cols; c++) m[k][c] -= coeff * m[top][c];

      if (Math.abs(m[k][i]) < 1e-6 * norm) m[k][i] = 0;
      const val = roundTo(coeff, 3);
      hist.push({
        m: mcopy(m),
        op: `R${k + 1} ${val >= 0 ? '−' : '+'} ${Math.abs(val)}·R${top + 1}`,
      });
    }
    top++;
  }
  return { final: m, hist };
}

// Gaussian elim

function findPivots(m) {
  const cols = m[0].length;
  const pivots = [];
  for (const row of m) {
    const i = row.findIndex(x => x !== 0);
    if (i >= 0) pivots.push(i);
  }
  const nonpivots = [];
  for (let i = 0; i < cols; i++)
    if (!pivots.includes(i)) nonpivots.push(i);
  return { pivots, nonpivots };
}

function gaussianSolve(mat, pivot) {
  const { final } = gaussianEliminate(mat, pivot);
  const cols = final[0].length;
  const nvars = cols - 1;
  const { pivots, nonpivots } = findPivots(final);

  if (pivots.includes(cols - 1)) return { text: 'No solution', vals: null };

  const freeIdx = nonpivots.filter(i => i < nvars);
  const nfree = freeIdx.length;

  const value = Array.from({ length: nvars },
    () => new Float64Array(1 + nfree));
  freeIdx.forEach((v, k) => { value[v][1 + k] = 1; });   // xv = t(k+1)

  for (let r = pivots.length - 1; r >= 0; r--) {
    const j = pivots[r];
    if (j >= nvars) continue;
    const row = final[r];
    const accum = new Float64Array(1 + nfree);
    accum[0] = row[cols - 1];
    for (let k = j + 1; k < nvars; k++)
      if (row[k] !== 0)
        for (let t = 0; t <= nfree; t++)
          accum[t] -= row[k] * value[k][t];
    for (let t = 0; t <= nfree; t++) value[j][t] = accum[t] / row[j];
  }

  const fmt = x => {
    const r = roundTo(x, 4);
    return Object.is(r, -0) ? '0' : String(r);
  };
  const parts = value.map((v, i) => {
    let s = `x${i + 1} = ${fmt(v[0])}`;
    for (let t = 1; t <= nfree; t++) {
      if (v[t] === 0) continue;
      s += ` ${v[t] > 0 ? '+' : '−'} ${fmt(Math.abs(v[t]))}·t${t}`;
    }
    return s;
  });
  return {
    text: parts.join('    ') +
          (nfree ? `    (t1…t${nfree} free)` : ''),
    vals: value,
  };
}

// Gram schmidt 

function gsProj(u, v, acc) {
  const n2 = vnorm(v) ** 2;
  if (vnorm(v) < Math.pow(10, -(acc - 1))) return null;
  const d = roundTo(vdot(u, v), acc);
  return v.map(x => roundTo(x * d / n2, acc));
}

function gramSchmidt(mat, modified, normed, acc) {
  const m = mcopy(mat).map(r => r.slice());
  const n = m.length;
  if (vnorm(m[0]) < Math.pow(10, -acc))
    return { hist: [{ m: mcopy(m), op: 'Norm of first vector is 0 or close to it; process terminated' }], error: null };

  const hist = [{ m: mcopy(m), op: 'Start: let u1 = v1' }];

  for (let i = 1; i < n; i++) {
    if (modified) {
      for (let j = i; j < n; j++) {
        const p = gsProj(m[j], m[i - 1], acc);
        if (!p) return { hist: [...hist, { m: mcopy(m), op: 'Zero vector encountered; process terminated' }], error: null };
        m[j] = m[j].map((x, c) => x - p[c]);
        hist.push({ m: mcopy(m), op: `Subtract proj of v${j + 1} onto u${i} from u${j + 1}` });
      }
    } else {
      const projs = m.slice(0, i).map(v => gsProj(m[i], v, acc));
      for (let j = 0; j < i; j++) {
        if (!projs[j]) return { hist: [...hist, { m: mcopy(m), op: 'Zero vector encountered; process terminated' }], error: null };
        m[i] = m[i].map((x, c) => x - projs[j][c]);
        hist.push({ m: mcopy(m), op: `Subtract proj of v${i + 1} onto u${j + 1} from u${i + 1}` });
      }
    }
    if (vnorm(m[i]) < Math.pow(10, -(acc - 1))) {
      hist[hist.length - 1].op += '\nLinear dependence encountered; process terminated';
      return { hist, error: null };
    }
    if (i < n - 1) hist[hist.length - 1].op += `\nu${i + 1} formed; let u${i + 2} = v${i + 2}`;
  }

  for (let i = 0; i < n; i++) {
    const L = vnorm(m[i]);
    m[i] = m[i].map(x => roundTo(x / L, acc));
    if (normed) hist.push({ m: mcopy(m), op: `Normalise vector ${i + 1}` });
  }
  hist[hist.length - 1].op += '\nOrthogonalisation complete!';

  let err = 0;
  for (let i = 0; i < n; i++)
    for (let j = 0; j < n; j++) {
      const d = vdot(m[i], m[j]) - (i === j ? 1 : 0);
      err += d * d;
    }
  return { hist, error: Math.sqrt(err) };
}

function randomMatrix(rows, cols) {
  return Array.from({ length: rows }, () =>
    Array.from({ length: cols }, () => roundTo(Math.random() * 20 - 10, 2)));
}

function hilbertMatrix(n) {
  return Array.from({ length: n }, (_, i) =>
    Array.from({ length: n }, (_, j) => 1 / (i + j + 1)));
}


function jacobiEigSym(S, n) {
  const A = S.slice();
  const V = new Array(n * n).fill(0);
  for (let i = 0; i < n; i++) V[i*n + i] = 1;
  for (let sweep = 0; sweep < 60; sweep++) {
    let off = 0;
    for (let p = 0; p < n; p++)
      for (let q = p + 1; q < n; q++) off += A[p*n+q] * A[p*n+q];
    if (off < 1e-24) break;
    for (let p = 0; p < n; p++)
      for (let q = p + 1; q < n; q++) {
        if (Math.abs(A[p*n+q]) < 1e-18) continue;
        const theta = (A[q*n+q] - A[p*n+p]) / (2 * A[p*n+q]);
        const t = Math.sign(theta || 1) / (Math.abs(theta) + Math.sqrt(theta*theta + 1));
        const c = 1 / Math.sqrt(t*t + 1), s2 = t * c;
        for (let k = 0; k < n; k++) {
          const akp = A[k*n+p], akq = A[k*n+q];
          A[k*n+p] = c*akp - s2*akq;
          A[k*n+q] = s2*akp + c*akq;
        }
        for (let k = 0; k < n; k++) {
          const apk = A[p*n+k], aqk = A[q*n+k];
          A[p*n+k] = c*apk - s2*aqk;
          A[q*n+k] = s2*apk + c*aqk;
        }
        for (let k = 0; k < n; k++) {
          const vkp = V[k*n+p], vkq = V[k*n+q];
          V[k*n+p] = c*vkp - s2*vkq;
          V[k*n+q] = s2*vkp + c*vkq;
        }
      }
  }
  const vals = [];
  for (let i = 0; i < n; i++) vals.push({ v: A[i*n+i], i });
  vals.sort((a, b) => b.v - a.v);
  return {
    values: vals.map(o => o.v),
    vectors: vals.map(o => {
      const col = [];
      for (let r = 0; r < n; r++) col.push(V[r*n + o.i]);
      return col;
    }),
  };
}

// LU decomp

function luDecompose(mat) {
  const n = mat.length;
  if (mat.some(r => r.length !== n))
    return { error: 'LU decomposition needs a square matrix.' };

  const U = mcopy(mat);
  const L = Array.from({ length: n }, (_, i) =>
    Array.from({ length: n }, (_, j) => (i === j ? 1 : 0)));
  const perm = Array.from({ length: n }, (_, i) => i);
  const norm = infNorm(mat) || 1;
  const hist = [{ m: mcopy(U), op: '' }];

  for (let k = 0; k < n; k++) {
    let piv = k;
    for (let i = k + 1; i < n; i++)
      if (Math.abs(U[i][k]) > Math.abs(U[piv][k])) piv = i;
    if (piv !== k) {
      [U[k], U[piv]] = [U[piv], U[k]];
      [perm[k], perm[piv]] = [perm[piv], perm[k]];
      for (let j = 0; j < k; j++)
        [L[k][j], L[piv][j]] = [L[piv][j], L[k][j]];
      hist.push({ m: mcopy(U), op: `R${k + 1} ↔ R${piv + 1}` });
    }
    if (Math.abs(U[k][k]) < 1e-12 * norm) continue;
    for (let i = k + 1; i < n; i++) {
      const l = U[i][k] / U[k][k];
      L[i][k] = l;
      for (let c = 0; c < n; c++) U[i][c] -= l * U[k][c];
      U[i][k] = 0;
      hist.push({
        m: mcopy(U),
        op: `R${i + 1} ${l >= 0 ? '−' : '+'} ${Math.abs(roundTo(l, 3))}·R${k + 1}` +
            `   (ℓ${i + 1}${k + 1} = ${roundTo(l, 4)})`,
      });
    }
  }

  const P = Array.from({ length: n }, (_, i) =>
    Array.from({ length: n }, (_, j) => (perm[i] === j ? 1 : 0)));
  hist.push({ m: mcopy(L), op: 'L — unit lower triangular (the multipliers ℓᵢⱼ)' });
  hist.push({ m: mcopy(P), op: 'P — permutation matrix from the row swaps' });

  let res = 0;
  for (let i = 0; i < n; i++)
    for (let j = 0; j < n; j++) {
      let lu = 0;
      for (let k = 0; k < n; k++) lu += L[i][k] * U[k][j];
      res += (mat[perm[i]][j] - lu) ** 2;
    }
  return { P, L, U, hist, residual: Math.sqrt(res) };
}

// GJ inv

function invertMatrix(mat, wantHist = true) {
  const n = mat.length;
  if (mat.some(r => r.length !== n))
    return { error: 'Inversion needs a square matrix.' };
  const norm = infNorm(mat) || 1;
  const M = mat.map((r, i) =>
    r.concat(Array.from({ length: n }, (_, j) => (i === j ? 1 : 0))));
  const hist = wantHist ? [{ m: mcopy(M), op: 'Augment with the identity: [A | I]' }] : [];

  for (let k = 0; k < n; k++) {
    let piv = k;
    for (let i = k + 1; i < n; i++)
      if (Math.abs(M[i][k]) > Math.abs(M[piv][k])) piv = i;
    if (Math.abs(M[piv][k]) < 1e-12 * norm)
      return { singular: true, hist };
    if (piv !== k) {
      [M[k], M[piv]] = [M[piv], M[k]];
      if (wantHist) hist.push({ m: mcopy(M), op: `R${k + 1} ↔ R${piv + 1}` });
    }
    const d = M[k][k];
    for (let c = 0; c < 2 * n; c++) M[k][c] /= d;
    if (wantHist) hist.push({ m: mcopy(M), op: `R${k + 1} ÷ ${roundTo(d, 4)}` });
    for (let i = 0; i < n; i++) {
      if (i === k || M[i][k] === 0) continue;
      const f = M[i][k];
      for (let c = 0; c < 2 * n; c++) M[i][c] -= f * M[k][c];
      M[i][k] = 0;
      if (wantHist) hist.push({
        m: mcopy(M),
        op: `R${i + 1} ${f >= 0 ? '−' : '+'} ${Math.abs(roundTo(f, 3))}·R${k + 1}`,
      });
    }
  }
  const inv = M.map(r => r.slice(n));
  let res = 0;
  for (let i = 0; i < n; i++)
    for (let j = 0; j < n; j++) {
      let acc2 = 0;
      for (let k = 0; k < n; k++) acc2 += mat[i][k] * inv[k][j];
      res += (acc2 - (i === j ? 1 : 0)) ** 2;
    }
  return { inv, hist, residual: Math.sqrt(res) };
}

// Eigen

const cadd = (a, b) => [a[0] + b[0], a[1] + b[1]];
const csub = (a, b) => [a[0] - b[0], a[1] - b[1]];
const cmul = (a, b) => [a[0]*b[0] - a[1]*b[1], a[0]*b[1] + a[1]*b[0]];
const cdiv = (a, b) => {
  const d = b[0]*b[0] + b[1]*b[1];
  return [(a[0]*b[0] + a[1]*b[1]) / d, (a[1]*b[0] - a[0]*b[1]) / d];
};
const cabs = a => Math.hypot(a[0], a[1]);
const conj = a => [a[0], -a[1]];
const csqrt = a => {
  const r = cabs(a);
  const re = Math.sqrt(Math.max(0, (r + a[0]) / 2));
  const im = Math.sign(a[1] || 1) * Math.sqrt(Math.max(0, (r - a[0]) / 2));
  return [re, im];
};

function hessenberg(A0) {
  const n = A0.length;
  const A = mcopy(A0);
  for (let k = 0; k < n - 2; k++) {
    let a = 0;
    for (let i = k + 1; i < n; i++) a += A[i][k] * A[i][k];
    a = Math.sqrt(a);
    if (a < 1e-300) continue;
    if (A[k + 1][k] > 0) a = -a;
    const v = new Array(n).fill(0);
    v[k + 1] = A[k + 1][k] - a;
    for (let i = k + 2; i < n; i++) v[i] = A[i][k];
    let vn = 0;
    for (let i = k + 1; i < n; i++) vn += v[i] * v[i];
    if (vn < 1e-300) continue;
    
    for (let j = 0; j < n; j++) {
      let dot = 0;
      for (let i = k + 1; i < n; i++) dot += v[i] * A[i][j];
      const f = 2 * dot / vn;
      for (let i = k + 1; i < n; i++) A[i][j] -= f * v[i];
    }
    for (let i = 0; i < n; i++) {
      let dot = 0;
      for (let j = k + 1; j < n; j++) dot += A[i][j] * v[j];
      const f = 2 * dot / vn;
      for (let j = k + 1; j < n; j++) A[i][j] -= f * v[j];
    }
  }
  return A;
}

function eigenvaluesQR(A0) {
  const n = A0.length;
  if (n === 1) return [[A0[0][0], 0]];
  // complex working copy of the Hessenberg form
  const Hr = hessenberg(A0);
  let H = Hr.map(r => r.map(x => [x, 0]));
  const scale = infNorm(A0) || 1;
  const evs = [];
  let m = n - 1, iter = 0;
  const MAXIT = 200 * n;

  while (m >= 0 && iter < MAXIT) {
    if (m === 0) { evs.push(H[0][0]); m--; continue; }
    
    const tail = cabs(H[m][m - 1]);
    if (tail < 1e-13 * (cabs(H[m - 1][m - 1]) + cabs(H[m][m]) + scale)) {
      evs.push(H[m][m]); m--; continue;
    }
    
    const a = H[m-1][m-1], b = H[m-1][m], c = H[m][m-1], d = H[m][m];
    const tr = cadd(a, d);
    const det = csub(cmul(a, d), cmul(b, c));
    const disc = csqrt(csub(cmul(tr, tr), [4*det[0], 4*det[1]]));
    const l1 = [(tr[0]+disc[0])/2, (tr[1]+disc[1])/2];
    const l2 = [(tr[0]-disc[0])/2, (tr[1]-disc[1])/2];
    const mu = cabs(csub(l1, d)) < cabs(csub(l2, d)) ? l1 : l2;

    const k = m + 1;
    const B = [];
    for (let i = 0; i < k; i++) {
      B.push([]);
      for (let j = 0; j < k; j++)
        B[i].push(i === j ? csub(H[i][j], mu) : H[i][j].slice());
    }
    
    const Q = Array.from({ length: k }, () => new Array(k).fill(0).map(() => [0, 0]));
    const R = Array.from({ length: k }, () => new Array(k).fill(0).map(() => [0, 0]));
    for (let j = 0; j < k; j++) {
      const col = [];
      for (let i = 0; i < k; i++) col.push(B[i][j].slice());
      for (let p = 0; p < j; p++) {
        let dot = [0, 0];
        for (let i = 0; i < k; i++) dot = cadd(dot, cmul(conj(Q[i][p]), col[i]));
        R[p][j] = dot;
        for (let i = 0; i < k; i++) col[i] = csub(col[i], cmul(dot, Q[i][p]));
      }
      let nrm = 0;
      for (let i = 0; i < k; i++) nrm += col[i][0]**2 + col[i][1]**2;
      nrm = Math.sqrt(nrm);
      R[j][j] = [nrm, 0];
      if (nrm < 1e-300) { Q.forEach(r2 => { r2[j] = [0, 0]; }); continue; }
      for (let i = 0; i < k; i++) Q[i][j] = [col[i][0]/nrm, col[i][1]/nrm];
    }
    for (let i = 0; i < k; i++)
      for (let j = 0; j < k; j++) {
        let acc2 = [0, 0];
        for (let p = i; p < k; p++) acc2 = cadd(acc2, cmul(R[i][p], Q[p][j]));
        H[i][j] = i === j ? cadd(acc2, mu) : acc2;
      }
    iter++;
  }
  return m < 0 ? evs : null;
}

// Null space

function nullspaceBasis(mat, tol) {
  const { final } = gaussianEliminate(mat, true);
  const rows = final.length, cols = final[0].length;
  const clean = final.map(r => r.map(x => (Math.abs(x) < tol ? 0 : x)));
  const pivots = [], pivotRow = {};
  for (let r = 0; r < rows; r++) {
    const i = clean[r].findIndex(x => x !== 0);
    if (i >= 0) { pivots.push(i); pivotRow[i] = r; }
  }
  const basis = [];
  for (let f = 0; f < cols; f++) {
    if (pivots.includes(f)) continue;
    const x = new Array(cols).fill(0);
    x[f] = 1;
    for (let pi = pivots.length - 1; pi >= 0; pi--) {
      const j = pivots[pi], row = clean[pivotRow[j]];
      let acc2 = 0;
      for (let k = j + 1; k < cols; k++) acc2 += row[k] * x[k];
      x[j] = -acc2 / row[j];
    }
    const L = Math.hypot(...x) || 1;
    basis.push(x.map(v => v / L));
  }
  return basis;
}

// Daigonilisation 

function diagonalise(mat) {
  const n = mat.length;
  if (mat.some(r => r.length !== n))
    return { error: 'Diagonalisation needs a square matrix.' };
  const norm = infNorm(mat) || 1;

  let sym = true;
  for (let i = 0; i < n && sym; i++)
    for (let j = i + 1; j < n; j++)
      if (Math.abs(mat[i][j] - mat[j][i]) > 1e-12 * norm) { sym = false; break; }

  let values, P;
  if (sym) {
    const flat = [];
    mat.forEach(r => flat.push(...r));
    const e = jacobiEigSym(flat, n);
    values = e.values;
    P = Array.from({ length: n }, (_, i) => e.vectors.map(col => col[i]));
  } else {
    const evs = eigenvaluesQR(mat);
    if (!evs) return { fail: 'Eigenvalue iteration did not converge.' };
    const scale = Math.max(1, ...evs.map(cabs));
    const complexOnes = evs.filter(e => Math.abs(e[1]) > 1e-7 * scale);
    if (complexOnes.length) {
      const ex = complexOnes[0];
      return { fail:
        `Not diagonalisable over ℝ: complex eigenvalues, e.g. ` +
        `λ = ${roundTo(ex[0], 4)} ${ex[1] >= 0 ? '+' : '−'} ${Math.abs(roundTo(ex[1], 4))}i ` +
        `(${complexOnes.length} of ${n} eigenvalues are non-real).` };
    }

    const reals = evs.map(e => e[0]).sort((a, b) => a - b);
    const tol = 1e-6 * scale;
    const clusters = [];
    for (const v of reals) {
      const c = clusters[clusters.length - 1];
      if (c && Math.abs(v - c.sum / c.k) < tol) { c.sum += v; c.k++; }
      else clusters.push({ sum: v, k: 1 });
    }
    values = [];
    P = Array.from({ length: n }, () => []);
    for (const c of clusters) {
      const lam = c.sum / c.k;
      const shifted = mat.map((r, i) => r.map((x, j) => x - (i === j ? lam : 0)));
      const basis = nullspaceBasis(shifted, 1e-8 * Math.max(norm, 1));
      if (basis.length < c.k)
        return { fail:
          `Not diagonalisable: λ = ${roundTo(lam, 4)} has algebraic multiplicity ` +
          `${c.k} but only ${basis.length} independent eigenvector` +
          `${basis.length === 1 ? '' : 's'} (defective matrix).` };
      for (let b = 0; b < c.k; b++) {
        values.push(lam);
        for (let i = 0; i < n; i++) P[i].push(basis[b][i]);
      }
    }
  }

  const D = Array.from({ length: n }, (_, i) =>
    Array.from({ length: n }, (_, j) => (i === j ? values[i] : 0)));
  const invRes = invertMatrix(P, false);
  if (invRes.singular || invRes.error)
    return { fail: 'Eigenvectors are numerically dependent; P is singular.' };

  let res = 0;
  for (let i = 0; i < n; i++)
    for (let j = 0; j < n; j++) {
      let ap = 0, pd = 0;
      for (let k = 0; k < n; k++) { ap += mat[i][k] * P[k][j]; pd += P[i][k] * D[k][j]; }
      res += (ap - pd) ** 2;
    }
  return { values, P, D, Pinv: invRes.inv, symmetric: sym,
           residual: Math.sqrt(res) };
}

function orthoProject(p, yaw, pitch, W, H, zoom) {
  const cy = Math.cos(yaw), sy = Math.sin(yaw);
  const cp = Math.cos(pitch), sp = Math.sin(pitch);
  const x1 = p[0] * cy - p[2] * sy, z1 = p[0] * sy + p[2] * cy;
  const y2 = p[1] * cp - z1 * sp,  z2 = p[1] * sp + z1 * cp;
  return [W / 2 + x1 * zoom, H / 2 - y2 * zoom, z2];
}
 
function attachOrbit(canvas, view, onChange) {
  let dragging = false, lx = 0, ly = 0;
  canvas.addEventListener('mousedown', e => {
    dragging = true; lx = e.clientX; ly = e.clientY;
  });
  window.addEventListener('mouseup', () => { dragging = false; });
  window.addEventListener('mousemove', e => {
    if (!dragging) return;
    view.yaw += (e.clientX - lx) * 0.008;
    view.pitch = Math.max(-1.4, Math.min(1.4, view.pitch + (e.clientY - ly) * 0.008));
    lx = e.clientX; ly = e.clientY;
    onChange();
  });
}
 