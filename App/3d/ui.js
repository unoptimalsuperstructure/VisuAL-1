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
  },
  rotate: {
    title: 'Rotate about Direction',
    desc: 'Rotate about the direction vector (d1,d2,d3) by angle θ (in degrees).',
    fields: [{id:'d1',label:'d1'},{id:'d2',label:'d2'},{id:'d3',label:'d3'},{id:'angle',label:'Angle (°)'}],
    apply(vals, obj) {
      const {d1,d2,d3,angle} = vals;
      if (d1===0 && d2===0 && d3===0) throw new Error('Direction vector cannot be zero');
      const rad = angle * Math.PI / 180;
      obj.applyTransform(rotateLineMatrix(d1,d2,d3,rad), 'Rotation ∥ Direction');
    }
  }
};

function openModal(type) {
  const obj = getActive();
  if (type !== 'addPoint' && !obj) { alert('Please select an object first.'); return; }
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
  if (currentModal !== 'addPoint' && !getActive()) { closeModal(); return; }
  
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
    if (currentModal === 'addPoint') {
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
