'use strict';

function buildPointCloud() {
  if (DATA.cloud) { scene.remove(DATA.cloud); DATA.cloud = null; }

  const n = DATA.pts.length;
  const positions = new Float32Array(n * 3);
  const colors    = new Float32Array(n * 3);

  // color if catagorical is selected
  DATA.catColors = new Map();
  if (DATA.cats) {
    let ci = 0;
    for (const c of DATA.cats)
      if (!DATA.catColors.has(c)) DATA.catColors.set(c, CAT_PALETTE[ci++ % CAT_PALETTE.length]);
  }
  const baseCol = new THREE.Color(0x222222);

  for (let i = 0; i < n; i++) {
    positions[i*3]   = DATA.pts[i][0];
    positions[i*3+1] = DATA.pts[i][1];
    positions[i*3+2] = DATA.pts[i][2];
    const col = DATA.cats ? new THREE.Color(DATA.catColors.get(DATA.cats[i])) : baseCol;
    colors[i*3] = col.r; colors[i*3+1] = col.g; colors[i*3+2] = col.b;
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geo.setAttribute('color',    new THREE.BufferAttribute(colors, 3));
  const mat = new THREE.PointsMaterial({ size: POINT_SIZE, vertexColors: true, sizeAttenuation: true });
  DATA.cloud = new THREE.Points(geo, mat);
  const hide = document.getElementById('chk-hide-data');
  DATA.cloud.visible = !(hide && hide.checked);
  scene.add(DATA.cloud);

  renderLegend();
}

function clearCloud() {
  if (DATA.cloud) { scene.remove(DATA.cloud); DATA.cloud = null; }
}

function toggleFitLine() {
  if (DATA.fitLine) {
    scene.remove(DATA.fitLine);
    DATA.fitLine.geometry.dispose();
    DATA.fitLine = null;
    return;
  }
  if (!DATA.pts.length) return;
  const { vectors } = eigSymmetric3(covariance());
  const dir = [vectors[0], vectors[3], vectors[6]]; 
  let tMin = Infinity, tMax = -Infinity;
  for (const p of DATA.pts) {
    const t = p[0]*dir[0] + p[1]*dir[1] + p[2]*dir[2];
    if (t < tMin) tMin = t;
    if (t > tMax) tMax = t;
  }
  const geo = new THREE.BufferGeometry().setFromPoints([
    new THREE.Vector3(dir[0]*tMin, dir[1]*tMin, dir[2]*tMin),
    new THREE.Vector3(dir[0]*tMax, dir[1]*tMax, dir[2]*tMax),
  ]);
  DATA.fitLine = new THREE.Line(geo, new THREE.LineBasicMaterial({ color: 0xe07030, linewidth: 2 }));
  scene.add(DATA.fitLine);
}

const SVD_STEPS = [
  { label: '0 · Unit sphere (identity)',                          key: 'I'  },
  { label: '1 · Apply Vᵀ  — rotate into the principal frame',     key: 'Vt' },
  { label: '2 · Apply Σ   — stretch by the singular values',      key: 'S'  },
  { label: '3 · Apply U   — rotate back · result = M',            key: 'U'  },
];

function startSVD() {
  if (!DATA.pts.length) return;
  if (typeof stopPCA === 'function') stopPCA();

  const { values, vectors } = eigSymmetric3(covariance());
  const sv = values.map(v => STD_SCALE * Math.sqrt(Math.max(0, v)));
  const V  = vectors;
  const Vt = mat3T(V);
  const sqrtD = [sv[0],0,0, 0,sv[1],0, 0,0,sv[2]];
  const M  = matMul3x3(matMul3x3(V, sqrtD), Vt);
  const { U, S } = svd3(M);

  const group = new THREE.Group();
  group.matrixAutoUpdate = false;

  const sphere = new THREE.Mesh(
    new THREE.SphereGeometry(1, 24, 16),
    new THREE.MeshBasicMaterial({ color: 0x000000, wireframe: true, transparent: true, opacity: 0.4 })
  );
  group.add(sphere);

  const axisCols = [0xcc0000, 0x00aa00, 0x0000cc];
  
  for (let k = 0; k < 3; k++) {
    const to = [0,0,0]; to[k] = 1;
    const g = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0,0,0), new THREE.Vector3(...to)]);
    group.add(new THREE.Line(g, new THREE.LineBasicMaterial({ color: axisCols[k] })));
  }
  scene.add(group);

  const I  = mat4From3(identity3());
  const m4Vt = mat4From3(Vt);
  const m4S  = mat4From3([S[0],0,0, 0,S[1],0, 0,0,S[2]]);
  const m4U  = mat4From3(U);
  const B = [I, m4Vt, m4FromMul(m4S, m4Vt), m4FromMul(m4U, m4FromMul(m4S, m4Vt))];

  const factors = [
    { type: 'rot',   quat: quatFromMat4(m4Vt) },
    { type: 'scale', vec: new THREE.Vector3(S[0], S[1], S[2]) },
    { type: 'rot',   quat: quatFromMat4(m4U) },
  ];

  DATA.svd = { group, sphere, B, factors, U, S, Vt, M, step: 0, anim: null };
  setGlyphMatrix(group, B[0]);

  document.getElementById('svd-panel').style.display = 'block';
  document.getElementById('btn-svd').textContent = 'Stop SVD';
  renderSVDStep();
}

function stopSVD() {
  if (!DATA.svd) return;
  cancelAnimationFrame(DATA.svd.raf);
  scene.remove(DATA.svd.group);
  DATA.svd = null;
  document.getElementById('svd-panel').style.display = 'none';
  document.getElementById('btn-svd').textContent = 'Step-by-step SVD';
}

function svdGoto(target) {
  const d = DATA.svd;
  if (!d || d.anim) return;
  target = Math.max(0, Math.min(3, target));
  if (target === d.step) return;

  if (Math.abs(target - d.step) > 1) {
    d.step = target;
    setGlyphMatrix(d.group, d.B[target]);
    renderSVDStep();
    return;
  }

  const s   = Math.min(d.step, target);
  const f   = d.factors[s];
  const fwd = target > d.step;
  const base = d.B[s];
  const t0 = fwd ? 0 : 1, t1 = fwd ? 1 : 0;
  const start = performance.now(), dur = 600;

  d.anim = true;
  const tick = now => {
    const u = Math.min(1, (now - start) / dur);
    const tt = t0 + (t1 - t0) * easeInOut(u);
    let factorM;
    if (f.type === 'rot') {
      const q = new THREE.Quaternion().slerp(f.quat, tt);
      factorM = new THREE.Matrix4().makeRotationFromQuaternion(q);
    } else {
      const sx = 1 + (f.vec.x - 1) * tt, sy = 1 + (f.vec.y - 1) * tt, sz = 1 + (f.vec.z - 1) * tt;
      factorM = new THREE.Matrix4().makeScale(sx, sy, sz);
    }
    setGlyphMatrix(d.group, new THREE.Matrix4().multiplyMatrices(factorM, base));
    if (u < 1) { d.raf = requestAnimationFrame(tick); }
    else { d.anim = null; d.step = target; setGlyphMatrix(d.group, d.B[target]); renderSVDStep(); }
  };
  d.raf = requestAnimationFrame(tick);
}


const PCA_STEPS = [
  { dim: 3, label: '0 · Full data (3-D)',
    why: 'Nothing dropped yet — the projection is the identity.' },
  { dim: 2, label: '1 · Project onto top 2 PCs — plane (2-D)',
    why: 'P₂ = V₂V₂ᵀ flattens each point onto the best-fit plane: the one ' +
         'that keeps the most variance.' },
  { dim: 1, label: '2 · Project onto top PC — line (1-D)',
    why: 'P₁ = v₁v₁ᵀ collapses the cloud onto the single direction of ' +
         'greatest variance — the same line as the orthogonal fit.' },
  { dim: 0, label: '3 · Collapse to the centroid (0-D)',
    why: 'P₀ = 0 sends every point to the mean. All variance is gone; ' +
         'the retained fraction is 0.' },
];
 
function startPCA() {
  if (!DATA.pts.length) return;
  stopSVD();
 
  const { values, vectors: V } = eigSymmetric3(covariance());
  const total = values.reduce((a, b) => a + Math.max(0, b), 0) || 1;
 
  const projs = [];
  for (let k = 3; k >= 0; k--) {
    const P = new Array(9).fill(0);
    for (let i = 0; i < 3; i++)
      for (let j = 0; j < 3; j++)
        for (let c = 0; c < k; c++)
          P[i*3 + j] += V[i*3 + c] * V[j*3 + c];
    projs.push(P);
  }
  const retained = [3, 2, 1, 0].map(k =>
    values.slice(0, k).reduce((a, b) => a + Math.max(0, b), 0) / total);
 
  DATA.pca = { projs, retained, step: 0, anim: null, raf: 0 };
  document.getElementById('pca-panel').style.display = 'block';
  document.getElementById('btn-pca').textContent = 'Stop PCA';
  applyPCAProjection(projs[0]);
  renderPCAStep();
}
 
function stopPCA() {
  if (!DATA.pca) return;
  cancelAnimationFrame(DATA.pca.raf);
  DATA.pca = null;
  restoreCloudPositions();
  document.getElementById('pca-panel').style.display = 'none';
  document.getElementById('btn-pca').textContent = 'Step-by-step PCA';
}
 
function applyPCAProjection(P) {
  if (!DATA.cloud) return;
  const attr = DATA.cloud.geometry.getAttribute('position');
  for (let i = 0; i < DATA.pts.length; i++) {
    const [x, y, z] = DATA.pts[i];
    attr.setXYZ(i,
      P[0]*x + P[1]*y + P[2]*z,
      P[3]*x + P[4]*y + P[5]*z,
      P[6]*x + P[7]*y + P[8]*z);
  }
  attr.needsUpdate = true;
}
 
function restoreCloudPositions() {
  applyPCAProjection(identity3());
}
 
function pcaGoto(target) {
  const d = DATA.pca;
  if (!d || d.anim) return;
  target = Math.max(0, Math.min(3, target));
  if (target === d.step) return;
 
  if (Math.abs(target - d.step) > 1) {
    d.step = target;
    applyPCAProjection(d.projs[target]);
    renderPCAStep();
    return;
  }
 
  const A = d.projs[d.step], B = d.projs[target];
  const start = performance.now(), dur = 600;
  d.anim = true;
  const tick = now => {
    const u = Math.min(1, (now - start) / dur);
    const t = easeInOut(u);
    const P = A.map((a, i) => a + (B[i] - a) * t);
    applyPCAProjection(P);
    if (u < 1) { d.raf = requestAnimationFrame(tick); }
    else { d.anim = null; d.step = target; applyPCAProjection(B); renderPCAStep(); }
  };
  d.raf = requestAnimationFrame(tick);
}

function setGlyphMatrix(group, m) {
  group.matrix.copy(m);
  group.updateMatrixWorld(true);
}

function mat4From3(m) {
  return new THREE.Matrix4().set(
    m[0], m[1], m[2], 0,
    m[3], m[4], m[5], 0,
    m[6], m[7], m[8], 0,
    0,    0,    0,    1
  );
}

function m4FromMul(A, B) { return new THREE.Matrix4().multiplyMatrices(A, B); }
function quatFromMat4(m) { return new THREE.Quaternion().setFromRotationMatrix(m); }
function easeInOut(t) { return t < 0.5 ? 2*t*t : 1 - Math.pow(-2*t + 2, 2) / 2; }

function clearAnalysis() {
  if (DATA.fitLine) { scene.remove(DATA.fitLine); DATA.fitLine.geometry.dispose(); DATA.fitLine = null; }
  stopSVD();
  if (typeof stopPCA === 'function') stopPCA();
}
 