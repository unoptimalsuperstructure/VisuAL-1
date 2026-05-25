function matMul4(A, v) {
  return [
    A[0]*v[0]  + A[1]*v[1]  + A[2]*v[2]  + A[3]*v[3],
    A[4]*v[0]  + A[5]*v[1]  + A[6]*v[2]  + A[7]*v[3],
    A[8]*v[0]  + A[9]*v[1]  + A[10]*v[2] + A[11]*v[3],
    A[12]*v[0] + A[13]*v[1] + A[14]*v[2] + A[15]*v[3],
  ];
}

function matMul4x4(A, B) {
  const R = new Float64Array(16);
  for (let r = 0; r < 4; r++)
    for (let c = 0; c < 4; c++) {
      let s = 0;
      for (let k = 0; k < 4; k++) s += A[r*4+k] * B[k*4+c];
      R[r*4+c] = s;
    }
  return Array.from(R);
}

function identity4() {
  return [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1];
}

function translationMatrix(x, y, z) {
  return [1,0,0,x, 0,1,0,y, 0,0,1,z, 0,0,0,1];
}

function reflectPlaneMatrix(a, b, c, d) {
  const n2 = a*a + b*b + c*c;
  return [
    (b*b+c*c-a*a)/n2, -2*a*b/n2,         -2*a*c/n2,         2*a*d/n2,
    -2*a*b/n2,        (a*a+c*c-b*b)/n2,  -2*b*c/n2,         2*b*d/n2,
    -2*a*c/n2,        -2*b*c/n2,         (a*a+b*b-c*c)/n2,  2*c*d/n2,
    0,                0,                 0,                  1,
  ];
}

function reflectLineMatrix(p1, p2, p3, d1, d2, d3) {
  const L = Math.sqrt(d1*d1 + d2*d2 + d3*d3);
  d1/=L; d2/=L; d3/=L;
  const c = p1*d1 + p2*d2 + p3*d3;
  return [
    2*d1*d1-1, 2*d1*d2,   2*d1*d3,   2*(p1-d1*c),
    2*d1*d2,   2*d2*d2-1, 2*d2*d3,   2*(p2-d2*c),
    2*d1*d3,   2*d2*d3,   2*d3*d3-1, 2*(p3-d3*c),
    0,         0,         0,         1,
  ];
}

function invertMatrix4(m) {
  const [m00,m01,m02,m03,m10,m11,m12,m13,m20,m21,m22,m23,m30,m31,m32,m33] = m;
  const b00=m00*m11-m01*m10, b01=m00*m12-m02*m10, b02=m00*m13-m03*m10;
  const b03=m01*m12-m02*m11, b04=m01*m13-m03*m11, b05=m02*m13-m03*m12;
  const b06=m20*m31-m21*m30, b07=m20*m32-m22*m30, b08=m20*m33-m23*m30;
  const b09=m21*m32-m22*m31, b10=m21*m33-m23*m31, b11=m22*m33-m23*m32;
  const det = b00*b11-b01*b10+b02*b09+b03*b08-b04*b07+b05*b06;
  if (!det) return identity4();
  const d = 1/det;
  return [
    (m11*b11-m12*b10+m13*b09)*d, (m02*b10-m01*b11-m03*b09)*d, (m31*b05-m32*b04+m33*b03)*d, (m22*b04-m21*b05-m23*b03)*d,
    (m12*b08-m10*b11-m13*b07)*d, (m00*b11-m02*b08+m03*b07)*d, (m32*b02-m30*b05-m33*b01)*d, (m20*b05-m22*b02+m23*b01)*d,
    (m10*b10-m11*b08+m13*b06)*d, (m01*b08-m00*b10-m03*b06)*d, (m30*b04-m31*b02+m33*b00)*d, (m21*b02-m20*b04-m23*b00)*d,
    (m11*b07-m10*b09-m12*b06)*d, (m00*b09-m01*b07+m02*b06)*d, (m31*b01-m30*b03-m32*b00)*d, (m20*b03-m21*b01+m22*b00)*d,
  ];
}

function applyMatrix(mat, verts, centre) {
  const nv = verts.map(v => {
    const r = matMul4(mat, [v[0], v[1], v[2], 1]);
    return [r[0], r[1], r[2]];
  });
  const rc = matMul4(mat, [centre[0], centre[1], centre[2], 1]);
  return { vertices: nv, centre: [rc[0], rc[1], rc[2]] };
}

const SHAPE_GEOMETRY = {
  UnitCube: {
    vertices: () => {
      const h = 0.5;
      return [[-h,-h,-h],[h,-h,-h],[-h,h,-h],[h,h,-h],[-h,-h,h],[h,-h,h],[-h,h,h],[h,h,h]];
    }
  }
};

let idCounter = 0;

class SceneObj {
  constructor(type = 'UnitCube') {
    this.id = ++idCounter;
    this.type = type;
    this.vertices = this.getBaseVertices(type);
    this.centre = [0, 0, 0];
    this.matrixStack = [[identity4(), 'Identity']];
    this.curMatrix = [identity4(), 'Identity'];
  }

  getBaseVertices(type) {
    const shape = SHAPE_GEOMETRY[type] || SHAPE_GEOMETRY['UnitCube'];
    return shape.vertices();
  }

  applyTransform(mat, name) {
    this.matrixStack.push([mat, name]);
    this.curMatrix = [matMul4x4(mat, this.curMatrix[0]), name];
    const r = applyMatrix(mat, this.vertices, this.centre);
    this.vertices = r.vertices;
    this.centre = r.centre;
  }

  undo() {
    if (this.matrixStack.length <= 1) return false;
    const inv = invertMatrix4(this.matrixStack[this.matrixStack.length - 1][0]);
    const r = applyMatrix(inv, this.vertices, this.centre);
    this.vertices = r.vertices;
    this.centre = r.centre;
    this.matrixStack.pop();
    return true;
  }

  reset() {
    this.vertices = this.getBaseVertices(this.type);
    this.centre = [0, 0, 0];
    this.matrixStack = [[identity4(), 'Identity']];
    this.curMatrix = [identity4(), 'Identity'];
  }
}

let objects = [new SceneObj()];
let activeId = null;
const sectionOpen = { objects: true, transforms: true };

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
      `<span class="card-left"><span class="card-chevron">▾</span><span>${name || '—'}</span></span>` +
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
  translate: {
    title: 'Translate',
    desc: 'Move the object by a vector (x, y, z).',
    fields: [{id:'x',label:'x'},{id:'y',label:'y'},{id:'z',label:'z'}],
    apply(vals, obj) {
      obj.applyTransform(translationMatrix(vals.x, vals.y, vals.z), 'Translation');
    }
  },
  reflectPlane: {
    title: 'Reflect about Plane',
    desc: 'Reflect across the plane ax + by + cz = d.',
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
    fields: [{id:'a1',label:'a1'},{id:'a2',label:'a2'},{id:'a3',label:'a3'},{id:'d1',label:'d1'},{id:'d2',label:'d2'},{id:'d3',label:'d3'}],
    apply(vals, obj) {
      const {a1,a2,a3,d1,d2,d3} = vals;
      if (d1===0 && d2===0 && d3===0) throw new Error('Direction vector cannot be zero');
      obj.applyTransform(reflectLineMatrix(a1,a2,a3,d1,d2,d3), 'Reflection ∥ Line');
    }
  }
};

function openModal(type) {
  const obj = getActive();
  if (!obj) { alert('Please select an object first.'); return; }
  const cfg = MODAL_CONFIGS[type];
  currentModal = type;
  document.getElementById('modal-title').textContent = cfg.title;
  document.getElementById('modal-desc').textContent = cfg.desc;
  document.getElementById('modal-err').textContent = '';
  const fc = document.getElementById('modal-fields');
  fc.innerHTML = '';
  cfg.fields.forEach(f => {
    const row = document.createElement('div');
    row.className = 'field-row';
    row.innerHTML = `<label>${f.label}</label><input id="mf-${f.id}" type="text" value="0" placeholder="0"/>`;
    fc.appendChild(row);
  });
  document.getElementById('modal-bg').style.display = 'flex';
  const first = fc.querySelector('input');
  if (first) { first.focus(); first.select(); }
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
  const obj = getActive();
  if (!obj) { closeModal(); return; }
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
    cfg.apply(vals, obj);
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
];

function buildShapeOptions() {
  const container = document.getElementById('shape-options');
  container.innerHTML = '';
  SHAPE_REGISTRY.forEach(s => {
    const row = document.createElement('div');
    row.className = 'shape-option';
    row.innerHTML =
      `<div class="shape-name">${s.type}</div>` +
      `<div class="shape-desc">${s.desc}</div>`;
    row.onclick = () => { addObject(s.type); toggleAddMenu(false); };
    container.appendChild(row);
  });
}

function toggleAddMenu(force) {
  const menu = document.getElementById('add-menu');
  const open = force !== undefined ? force : menu.style.display === 'none';
  if (open) { buildShapeOptions(); menu.style.display = 'block'; }
  else { menu.style.display = 'none'; }
}

function addObject(type) {
  const obj = new SceneObj(type);
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
