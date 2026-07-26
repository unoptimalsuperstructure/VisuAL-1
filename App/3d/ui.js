let objects = [new SceneObj()];
let activeId = null;
const sectionOpen = { objects: true, transforms: true, lp: true };

function getActive() { 
  return objects.find(o => o.id === activeId) || null; 
}

function toggleSection(id) {
  sectionOpen[id] = !sectionOpen[id];
  const body = document.getElementById('section-' + id);
  const head = document.getElementById('shead-' + id);
  if (body) body.style.display = sectionOpen[id] ? 'block' : 'none';
  if (head) head.classList.toggle('collapsed', !sectionOpen[id]);
}

function renderObjList() {
  const list = document.getElementById('obj-list');
  list.innerHTML = '';
  if (!objects.length) {
    list.innerHTML = '<div id="no-obj">No objects</div>';
    return;
  }
  objects.forEach(obj => {
    const row = document.createElement('div');
    row.className = 'obj-row' + (obj.id === activeId ? ' active' : '');
    row.innerHTML =
      `<div class="obj-dot"></div>` +
      `<span style="flex:1">${obj.type} #${obj.id}</span>` +
      (obj.id === activeId ? '<span class="tag">active</span>' : '');
    row.onclick = () => {
      activeId = obj.id === activeId ? null : obj.id;
      renderObjList();
      renderStack();
    };
    list.appendChild(row);
  });
  document.getElementById('obj-count-badge').textContent = objects.length;
}

function fmtNum(v) {
  return (v >= 0 ? '+' : '-') + Math.abs(v).toFixed(3);
}

const collapsedCards = new Set();

function renderStack() {
  const container = document.getElementById('stack-content');
  const obj = getActive();
  if (!obj) {
    container.innerHTML = '<div id="no-obj">Select an object to view its matrix stack</div>';
    return;
  }
  container.innerHTML = '';
  [...obj.matrixStack].reverse().forEach((entry, i) => {
    const [mat, name] = entry;
    const idx = obj.matrixStack.length - 1 - i;
    const cardId = `card-${obj.id}-${idx}`;
    const isCollapsed = collapsedCards.has(cardId);

    const card = document.createElement('div');
    card.className = 'matrix-card';

    const head = document.createElement('div');
    head.className = 'matrix-card-head' + (isCollapsed ? ' collapsed' : '');
    head.innerHTML =
      `<span class="card-left"><span class="card-chevron">▾</span><span>${escapeHTML(name || '—')}</span></span>` +
      `<span class="idx">[${idx}]</span>`;
    head.onclick = () => {
      if (collapsedCards.has(cardId)) collapsedCards.delete(cardId);
      else collapsedCards.add(cardId);
      renderStack();
    };

    const pre = document.createElement('pre');
    pre.className = 'matrix';
    pre.style.display = isCollapsed ? 'none' : 'block';
    let rows = '';
    for (let r = 0; r < 4; r++) {
      let rowStr = '[ ';
      for (let c = 0; c < 4; c++) {
        rowStr += fmtNum(mat[r*4+c]) + ' ';
      }
      rows += rowStr + ']\n';
    }
    pre.textContent = rows;

    card.appendChild(head);
    card.appendChild(pre);
    container.appendChild(card);
  });
}

let currentModal = null;

const MODAL_CONFIGS = {
  addPoint: {
    title: 'Add Point',
    desc: 'Add a point at specified coordinates (x, y, z).',
    fields: [{id:'x',label:'x'},{id:'y',label:'y'},{id:'z',label:'z'}],
    apply(vals) {
      addObject('Point', [vals.x, vals.y, vals.z]);
    }
  },
  translate: {
    title: 'Translate',
    desc: 'Move the object by a vector (x, y, z).',
    info: 'Adds a fixed vector to every vertex. Translation is affine, not ' +
          'linear — it moves the origin — which is why it needs the 4th row ' +
          'and column of homogeneous coordinates.',
    matrix: v => translationMatrix(v.x, v.y, v.z),
    fields: [{id:'x',label:'x'},{id:'y',label:'y'},{id:'z',label:'z'}],
    apply(vals, obj) {
      obj.applyTransform(translationMatrix(vals.x, vals.y, vals.z), 'Translation');
    }
  },
  reflectPlane: {
    title: 'Reflect about Plane',
    desc: 'Reflect across the plane ax + by + cz = d.',
    info: 'Mirror image through the plane. An isometry (lengths and angles ' +
          'preserved) with determinant −1: it flips orientation, turning a ' +
          'right-handed object left-handed.',
    matrix: v => (v.a || v.b || v.c) ? reflectPlaneMatrix(v.a, v.b, v.c, v.d) : null,
    fields: [{id:'a',label:'a'},{id:'b',label:'b'},{id:'c',label:'c'},{id:'d',label:'d'}],
    apply(vals, obj) {
      const {a,b,c,d} = vals;
      if (a===0 && b===0 && c===0) throw new Error('Normal vector cannot be zero');
      obj.applyTransform(reflectPlaneMatrix(a,b,c,d), 'Reflection ∥ Plane');
    }
  },
  reflectLine: {
    title: 'Reflect about Line',
    desc: 'Line: r = (a1,a2,a3) + t(d1,d2,d3)',
    info: 'Maps each point to its mirror image through the line — in 3-D ' +
          'this equals a 180° rotation about it, so determinant = +1 and ' +
          'orientation is preserved.',
    matrix: v => (v.d1 || v.d2 || v.d3)
      ? reflectLineMatrix(v.a1, v.a2, v.a3, v.d1, v.d2, v.d3) : null,
    fields: [{id:'a1',label:'a1'},{id:'a2',label:'a2'},{id:'a3',label:'a3'},{id:'d1',label:'d1'},{id:'d2',label:'d2'},{id:'d3',label:'d3'}],

    layout: { lead: 'r =', blocks: [
      { cols: 1, ids: ['a1','a2','a3'] },
      { text: '+ t' },
      { cols: 1, ids: ['d1','d2','d3'] },
    ] },
    apply(vals, obj) {
      const {a1,a2,a3,d1,d2,d3} = vals;
      if (d1===0 && d2===0 && d3===0) throw new Error('Direction vector cannot be zero');
      obj.applyTransform(reflectLineMatrix(a1,a2,a3,d1,d2,d3), 'Reflection ∥ Line');
    }
  },
  rotate: {
    title: 'Rotate about Direction',
    desc: 'Rotate about the direction vector (d1,d2,d3) by angle θ (in degrees).',
    info: 'Rotation about an axis (Rodrigues\u2019 formula). Orthogonal with ' +
          'determinant +1: lengths, angles and orientation are all preserved ' +
          '— the columns form a rotated orthonormal basis.',
    matrix: v => (v.d1 || v.d2 || v.d3)
      ? rotateLineMatrix(v.d1, v.d2, v.d3, v.angle * Math.PI / 180) : null,
    fields: [{id:'d1',label:'d1'},{id:'d2',label:'d2'},{id:'d3',label:'d3'},{id:'angle',label:'Angle (°)'}],
    // Direction as a column vector; the angle stays an ordinary labelled row.
    layout: { lead: 'd =', blocks: [{ cols: 1, ids: ['d1','d2','d3'] }] },
    apply(vals, obj) {
      const {d1,d2,d3,angle} = vals;
      if (d1===0 && d2===0 && d3===0) throw new Error('Direction vector cannot be zero');
      const rad = angle * Math.PI / 180;
      obj.applyTransform(rotateLineMatrix(d1,d2,d3,rad), 'Rotation ∥ Direction');
    }
  },
  project: {
    title: 'Project onto Plane',
    desc: 'Orthogonally project the object onto the plane ax + by + cz = d.',
    info: 'Drops each point perpendicularly onto the plane. Singular ' +
          '(determinant 0) and idempotent — applying it twice changes ' +
          'nothing — and information off the plane is lost, so it has no inverse.',
    matrix: v => (v.a || v.b || v.c) ? projectPlaneMatrix(v.a, v.b, v.c, v.d) : null,
    fields: [{id:'a',label:'a'},{id:'b',label:'b'},{id:'c',label:'c'},{id:'d',label:'d'}],
    apply(vals, obj) {
      const {a,b,c,d} = vals;
      if (a===0 && b===0 && c===0) throw new Error('Plane normal cannot be zero');
      obj.applyTransform(projectPlaneMatrix(a,b,c,d), 'Projection onto Plane');
    }
  },
  scale: {
    title: 'Scale',
    desc: 'Uniformly scale the object about its centre by factor c (c > 0, c ≠ 1).',
    info: 'Multiplies every distance from the object\u2019s centre by c, so ' +
          'volume scales by det = c³. The translation column keeps the ' +
          'centre fixed instead of the origin.',
    matrix(v) {
      const o = getActive();
      if (!o || !(v.c > 0)) return null;
      return scaleMatrix(v.c, o.centre[0], o.centre[1], o.centre[2]);
    },
    fields: [{id:'c',label:'c',default:2}],
    apply(vals, obj) {
      const {c} = vals;
      if (c <= 0) throw new Error('Scale factor must be greater than 0');
      if (c === 1) throw new Error('A scale factor of 1 has no effect');
      const [cx,cy,cz] = obj.centre;
      obj.applyTransform(scaleMatrix(c, cx, cy, cz), 'Scaling');
    }
  },
  shear: {
    title: 'Shear',
    desc: 'Shear by factor k in a direction, fixing an invariant line r = a + t·d.',
    info: 'Slides each point parallel to the shear direction, in proportion ' +
          'to its distance from the invariant line. Determinant = 1, so ' +
          'volume is preserved even though shapes distort.',
    matrix(v) {
      if (!(v.d1 || v.d2 || v.d3) || !(v.c1 || v.c2 || v.c3)) return null;
      const cr = [v.d2*v.c3 - v.d3*v.c2, v.d3*v.c1 - v.d1*v.c3, v.d1*v.c2 - v.d2*v.c1];
      if (Math.hypot(...cr) < 1e-6) return null;
      return shearMatrix(v.a1, v.a2, v.a3, v.d1, v.d2, v.d3, v.c1, v.c2, v.c3, v.k);
    },
    fields: [
      {id:'k',label:'k',default:1},
      {id:'c1',label:'dir x'},{id:'c2',label:'dir y'},{id:'c3',label:'dir z'},
      {id:'a1',label:'line x₀'},{id:'a2',label:'line y₀'},{id:'a3',label:'line z₀'},
      {id:'d1',label:'line dx'},{id:'d2',label:'line dy'},{id:'d3',label:'line dz'},
    ],

    layout: { lead: 'r =', blocks: [
      { cols: 1, ids: ['a1','a2','a3'] },
      { text: '+ t' },
      { cols: 1, ids: ['d1','d2','d3'] },
      { text: '  shear dir' },
      { cols: 1, ids: ['c1','c2','c3'] },
    ] },
    apply(vals, obj) {
      const {k,c1,c2,c3,a1,a2,a3,d1,d2,d3} = vals;
      if (d1===0 && d2===0 && d3===0) throw new Error('Invariant line direction cannot be zero');
      if (c1===0 && c2===0 && c3===0) throw new Error('Shear direction cannot be zero');
      const cr = [d2*c3-d3*c2, d3*c1-d1*c3, d1*c2-d2*c1];
      if (Math.hypot(...cr) < 1e-6) throw new Error('Line and shear direction are parallel');
      obj.applyTransform(shearMatrix(a1,a2,a3,d1,d2,d3,c1,c2,c3,k), 'Shearing');
    }
  },
  custom: {
    title: 'Custom Matrix',
    desc: 'Apply a custom 3×3 linear transformation (row-major).',
    info: 'Any linear map: the columns are the images of the basis vectors ' +
          'i, j, k. The determinant is the volume scale factor — negative ' +
          'means orientation flips, zero means the object collapses.',
    matrix: v => [v.m11, v.m12, v.m13, 0,
                  v.m21, v.m22, v.m23, 0,
                  v.m31, v.m32, v.m33, 0,
                  0, 0, 0, 1],
    fields: [
      {id:'m11',label:'m₁₁',default:1},{id:'m12',label:'m₁₂'},{id:'m13',label:'m₁₃'},
      {id:'m21',label:'m₂₁'},{id:'m22',label:'m₂₂',default:1},{id:'m23',label:'m₂₃'},
      {id:'m31',label:'m₃₁'},{id:'m32',label:'m₃₂'},{id:'m33',label:'m₃₃',default:1},
    ],

    layout: { lead: 'M =', blocks: [
      { cols: 3, ids: ['m11','m12','m13','m21','m22','m23','m31','m32','m33'] },
    ] },
    apply(vals, obj) {
      const m = [vals.m11,vals.m12,vals.m13, vals.m21,vals.m22,vals.m23, vals.m31,vals.m32,vals.m33];
      const I = [1,0,0, 0,1,0, 0,0,1];
      if (m.every((v,i) => v === I[i])) throw new Error('Matrix is the identity (no effect)');
      obj.applyTransform([
        m[0],m[1],m[2],0,
        m[3],m[4],m[5],0,
        m[6],m[7],m[8],0,
        0,   0,   0,   1,
      ], 'Custom');
    }
  },
  repeat: {
    title: 'Repeat last Transformations',
    desc: 'Re-apply the last n transformations, in order. If n exceeds the ' +
          'stack it is rounded down.',
    info: 'Composing maps is matrix multiplication: repeating the last n ' +
          'transformations applies the single product matrix ' +
          'Mₙ · … · M₂ · M₁ shown below.',
    matrix(v) {
      const o = getActive();
      const n = Math.floor(v.n);
      if (!o || !(n >= 1)) return null;
      const avail = o.matrixStack.length - 1;
      const take = Math.min(n, avail);
      if (take < 1) return null;
      let M = identity4();
      for (let i = o.matrixStack.length - take; i < o.matrixStack.length; i++)
        M = matMul4x4(o.matrixStack[i][0], M);
      return M;
    },
    fields: [{id:'n',label:'n',default:1}],
    apply(vals, obj) {
      const n = Math.floor(vals.n);
      if (!(n >= 1)) throw new Error('n must be a positive integer');
      const avail = obj.matrixStack.length - 1;
      if (avail < 1) throw new Error('No transformations to repeat yet');
      const take = Math.min(n, avail);
      const entries = obj.matrixStack.slice(-take).map(([m, name]) => [m, name]);
      entries.forEach(([m, name]) => obj.applyTransform(m, name + ' (rep)'));
    }
  }
};

const SAVED_LP = [];
let lpCounter = 0;

const LP_PICKERS = {
  reflectLine:  { kind: 'line',  map: { a1:'a1', a2:'a2', a3:'a3', d1:'d1', d2:'d2', d3:'d3' } },
  rotate:       { kind: 'line',  map: { d1:'d1', d2:'d2', d3:'d3' } },
  shear:        { kind: 'line',  map: { a1:'a1', a2:'a2', a3:'a3', d1:'d1', d2:'d2', d3:'d3' } },
  reflectPlane: { kind: 'plane', map: { a:'a', b:'b', c:'c', d:'d' } },
  project:      { kind: 'plane', map: { a:'a', b:'b', c:'c', d:'d' } },
};
 
function addSavedLine(p)  { SAVED_LP.push({ id: ++lpCounter, kind: 'line',  name: 'Line '  + lpCounter, p }); afterLPChange(); }
function addSavedPlane(p) { SAVED_LP.push({ id: ++lpCounter, kind: 'plane', name: 'Plane ' + lpCounter, p }); afterLPChange(); }
 
function deleteSavedLP(id) {
  const i = SAVED_LP.findIndex(o => o.id === id);
  if (i >= 0) { SAVED_LP.splice(i, 1); afterLPChange(); }
}
 
function afterLPChange() {
  renderLPList();
  if (typeof syncLinesPlanes === 'function') syncLinesPlanes();
}
 
function renderLPList() {
  const el = document.getElementById('lp-list');
  if (!el) return;
  if (!SAVED_LP.length) { el.innerHTML = '<div class="lp-empty">No saved lines or planes yet.</div>'; return; }
  el.innerHTML = SAVED_LP.map(o => {
    const desc = o.kind === 'line'
      ? `(${o.p.a1}, ${o.p.a2}, ${o.p.a3}) + t·(${o.p.d1}, ${o.p.d2}, ${o.p.d3})`
      : `${o.p.a}x + ${o.p.b}y + ${o.p.c}z = ${o.p.d}`;
    return `<div class="lp-row"><span class="lp-name">${escapeHTML(o.name)}</span>` +
           `<span class="lp-desc">${desc}</span>` +
           `<button class="lp-del" data-tip="Remove this ${o.kind}" onclick="deleteSavedLP(${o.id})">×</button></div>`;
  }).join('');
}
 
function openModal(type) {
  const obj = getActive();
  const NO_OBJECT_NEEDED = ['addPoint', 'addLine', 'addPlane'];
  if (!NO_OBJECT_NEEDED.includes(type) && !obj) { alert('Please select an object first.'); return; }
  const cfg = MODAL_CONFIGS[type];
  currentModal = type;
  document.getElementById('modal-title').textContent = cfg.title;
  document.getElementById('modal-desc').textContent = cfg.desc;
  document.getElementById('modal-err').textContent = '';
  const fc = document.getElementById('modal-fields');
  fc.innerHTML = '';

  const laidOut = new Set();
  if (cfg.layout) {
    const defaults = {};
    cfg.fields.forEach(f => { defaults[f.id] = f.default ?? 0; });

    const wrap = document.createElement('div');
    wrap.className = 'mtx-wrap';
    if (cfg.layout.lead) {
      const lead = document.createElement('span');
      lead.className = 'mtx-lead';
      lead.textContent = cfg.layout.lead;
      wrap.appendChild(lead);
    }
    for (const block of cfg.layout.blocks) {
      if (block.text !== undefined) {
        const t = document.createElement('span');
        t.className = 'mtx-lead';
        t.textContent = block.text;
        wrap.appendChild(t);
        continue;
      }
      const bracket = document.createElement('div');
      bracket.className = 'mtx-bracket';
      const grid = document.createElement('div');
      grid.className = 'mtx-grid';
      grid.style.gridTemplateColumns = `repeat(${block.cols}, auto)`;
      for (const id of block.ids) {
        const inp = document.createElement('input');
        inp.type = 'text';
        inp.id = 'mf-' + id;
        inp.value = defaults[id];
        inp.placeholder = '0';
        inp.setAttribute('aria-label', id);
        grid.appendChild(inp);
        laidOut.add(id);
      }
      bracket.appendChild(grid);
      wrap.appendChild(bracket);
    }
    fc.appendChild(wrap);
  }

  cfg.fields.forEach(f => {
    if (laidOut.has(f.id)) return;
    const row = document.createElement('div');
    row.className = 'field-row';
    row.innerHTML = `<label>${f.label}</label><input id="mf-${f.id}" type="text" value="${f.default ?? 0}" placeholder="0"/>`;
    fc.appendChild(row);
  });
  const picker = LP_PICKERS[type];
  const choices = picker ? SAVED_LP.filter(o => o.kind === picker.kind) : [];
  if (choices.length) {
    const row = document.createElement('div');
    row.className = 'field-row';
    row.innerHTML = `<label>Use saved</label>` +
      `<select id="mf-lp-pick" data-tip="Fill the fields from a saved ${picker.kind}">` +
      `<option value="">— pick a ${picker.kind} —</option>` +
      choices.map(o => `<option value="${o.id}">${escapeHTML(o.name)}</option>`).join('') +
      `</select>`;
    fc.prepend(row);
    row.querySelector('select').addEventListener('change', e => {
      const o = SAVED_LP.find(x => x.id === +e.target.value);
      if (!o) return;
      for (const [src, fid] of Object.entries(picker.map)) {
        const inp = document.getElementById('mf-' + fid);
        if (inp) inp.value = o.p[src];
      }
      updateModalPreview();
    });
  }
 
  const info = document.getElementById('modal-info');
  if (info) {
    info.textContent = cfg.info || '';
    info.style.display = cfg.info ? 'block' : 'none';
  }
  if (!fc.dataset.wired) {
    fc.dataset.wired = '1';
    fc.addEventListener('input', updateModalPreview);
  }
  updateModalPreview();
 
  document.getElementById('modal-bg').style.display = 'flex';
  const first = fc.querySelector('input');
  if (first) { first.focus(); first.select(); }
}

function updateModalPreview() {
  const label = document.getElementById('modal-preview-label');
  const pre = document.getElementById('modal-preview');
  if (!pre || !label) return;
  const cfg = currentModal && MODAL_CONFIGS[currentModal];
  if (!cfg || !cfg.matrix) {
    label.style.display = 'none'; pre.style.display = 'none';
    return;
  }
  label.style.display = 'block'; pre.style.display = 'block';
 
  const vals = {};
  let bad = false;
  cfg.fields.forEach(f => {
    const v = parseFloat(document.getElementById('mf-' + f.id)?.value);
    if (isNaN(v)) bad = true; else vals[f.id] = v;
  });
 
  let m = null;
  if (!bad) { try { m = cfg.matrix(vals); } catch (e) { m = null; } }
  if (!m) { pre.textContent = '(enter valid parameters)'; return; }
 
  const rows = [0, 1, 2, 3].map(r => m.slice(r * 4, r * 4 + 4));
  pre.textContent = (typeof printMatrix === 'function')
    ? printMatrix(rows, 2)
    : rows.map(r => '[' + r.map(v => v.toFixed(2)).join(' ') + ']').join('\n');
}

function closeModal() {
  document.getElementById('modal-bg').style.display = 'none';
  currentModal = null;
}

function closeModalBg(e) {
  if (e.target === document.getElementById('modal-bg')) closeModal();
}

function submitModal() {
  if (!currentModal) return;
  if (!['addPoint', 'addLine', 'addPlane'].includes(currentModal) && !getActive()) { closeModal(); return; }
  
  const cfg = MODAL_CONFIGS[currentModal];
  const vals = {};
  let err = false;
  cfg.fields.forEach(f => {
    const inp = document.getElementById('mf-' + f.id);
    const v = parseFloat(inp.value);
    if (isNaN(v)) { inp.classList.add('err'); err = true; }
    else { inp.classList.remove('err'); vals[f.id] = v; }
  });
  
  if (err) { document.getElementById('modal-err').textContent = 'Please enter valid numbers.'; return; }
  try {
    if (['addPoint', 'addLine', 'addPlane'].includes(currentModal)) {
      cfg.apply(vals);
    } else {
      cfg.apply(vals, getActive());
    }
    closeModal();
    renderStack();
  } catch (e) {
    document.getElementById('modal-err').textContent = e.message;
  }
}

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeModal();
  if (e.key === 'Enter' && currentModal) submitModal();
});

const SHAPE_REGISTRY = [
  { type: 'UnitCube', desc: 'Unit cube centred at origin' },
  { type: 'Point', desc: 'A point at specified coordinates' }
];

MODAL_CONFIGS.addLine = {
  title: 'Add Line', desc: 'Save the line r = (a1,a2,a3) + t·(d1,d2,d3) for reuse in transformations.',
  info: 'Saved lines appear in the sidebar, are drawn in the scene, and can ' +
        'be picked inside Reflect, Rotate and Shear instead of retyping.',
  fields: [{id:'a1',label:'a1'},{id:'a2',label:'a2'},{id:'a3',label:'a3'},
           {id:'d1',label:'d1',default:1},{id:'d2',label:'d2'},{id:'d3',label:'d3'}],
  layout: { lead: 'r =', blocks: [
    { cols: 1, ids: ['a1','a2','a3'] },
    { text: '+ t' },
    { cols: 1, ids: ['d1','d2','d3'] },
  ] },
  apply(v) {
    if (!v.d1 && !v.d2 && !v.d3) throw new Error('Direction cannot be the zero vector');
    addSavedLine(v);
  }
};
MODAL_CONFIGS.addPlane = {
  title: 'Add Plane', desc: 'Save the plane ax + by + cz = d for reuse in transformations.',
  info: 'Saved planes appear in the sidebar, are drawn in the scene, and can ' +
        'be picked inside Reflect-about-Plane and Project instead of retyping.',
  fields: [{id:'a',label:'a'},{id:'b',label:'b'},{id:'c',label:'c',default:1},{id:'d',label:'d'}],
  apply(v) {
    if (!v.a && !v.b && !v.c) throw new Error('Normal cannot be the zero vector');
    addSavedPlane(v);
  }
};

function buildShapeOptions() {
  const container = document.getElementById('shape-options');
  container.innerHTML = '';
  SHAPE_REGISTRY.forEach(s => {
    const row = document.createElement('div');
    row.className = 'shape-option';
    row.innerHTML =
      `<div class="shape-name">${s.type}</div>` +
      `<div class="shape-desc">${s.desc}</div>`;
    row.onclick = () => { 
      if (s.type === 'Point') {
        openModal('addPoint');
      } else {
        addObject(s.type); 
      }
      toggleAddMenu(false);
    };
    container.appendChild(row);
  });
}

function toggleAddMenu(force) {
  const menu = document.getElementById('add-menu');
  const open = force !== undefined ? force : menu.style.display === 'none';
  if (open) { buildShapeOptions(); menu.style.display = 'block'; }
  else { menu.style.display = 'none'; }
}

function addObject(type, args) {
  const obj = new SceneObj(type, args);
  objects.push(obj);
  activeId = obj.id;
  renderObjList();
  renderStack();
}

function undoLast() {
  const obj = getActive();
  if (!obj) return;
  obj.undo();
  renderStack();
}

let pendingAction = null;

function askConfirm(action) {
  const obj = getActive();
  if (!obj) return;
  pendingAction = action;
  document.getElementById('confirm-msg').textContent =
    action === 'reset' ? 'Reset all transforms on this object?' : 'Delete this object permanently?';
  document.getElementById('confirm-bar').style.display = 'block';
}

function cancelConfirm() {
  pendingAction = null;
  document.getElementById('confirm-bar').style.display = 'none';
}

function doConfirm() {
  const action = pendingAction;
  cancelConfirm();
  if (action === 'reset') {
    const obj = getActive();
    if (!obj) return;
    obj.reset();
    renderStack();
  } else if (action === 'delete') {
    const obj = getActive();
    if (!obj) return;
    objects = objects.filter(o => o.id !== obj.id);
    activeId = objects.length ? objects[objects.length - 1].id : null;
    renderObjList();
    renderStack();
  }
}

activeId = objects[0].id;
renderObjList();
renderStack();

document.addEventListener('click', e => {
  const menu = document.getElementById('add-menu');
  const btn = document.getElementById('add-obj-btn');
  if (menu && btn && !menu.contains(e.target) && !btn.contains(e.target)) {
    menu.style.display = 'none';
  }
});
renderLPList();