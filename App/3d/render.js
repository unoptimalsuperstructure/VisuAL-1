const CUBE_FACES = [[0,1,3,2],[4,5,7,6],[0,1,5,4],[2,3,7,6],[0,2,6,4],[1,3,7,5]];
const CUBE_EDGES = [[0,1],[0,2],[0,4],[3,1],[3,2],[3,7],[5,1],[5,4],[5,7],[6,2],[6,4],[6,7]];
const FACE_COLORS = [0x777777, 0x777777, 0x777777, 0x777777, 0x777777, 0x777777];

// find out why it makes triangles instead of cubes
function writeQuad(arr, offset, v0, v1, v2, v3) {
  arr.set(v0, offset);
  arr.set(v1, offset + 3);
  arr.set(v2, offset + 6);
  arr.set(v3, offset + 9);
}

const objMeshes = new Map();

function buildCubeMesh(obj) {
  const group = new THREE.Group();
  const faces = [];

  for (let i = 0; i < 6; i++) {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(12), 3));
    const mat = new THREE.MeshPhongMaterial({
      color: FACE_COLORS[i], 
      transparent: true, 
      opacity: 0.6, 
      side: THREE.DoubleSide,
    });
    const mesh = new THREE.Mesh(geo, mat);
    group.add(mesh);
    faces.push(mesh);
  }

  const edgeGeo = new THREE.BufferGeometry();
  edgeGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(CUBE_EDGES.length * 6), 3));
  const edgeLine = new THREE.LineSegments(
    edgeGeo, new THREE.LineBasicMaterial({ color: 0x222222, transparent: true, opacity: 0.8 })
  );
  group.add(edgeLine);

  const shadowFaces = [];
  for (let i = 0; i < 6; i++) {
    const geo2 = new THREE.BufferGeometry();
    geo2.setAttribute('position', new THREE.BufferAttribute(new Float32Array(12), 3));
    const mat2 = new THREE.MeshPhongMaterial({
      color: 0xaaaaaa, 
      transparent: false,
      opacity: 0, 
      side: THREE.DoubleSide,
    });
    shadowFaces.push(new THREE.Mesh(geo2, mat2));
    group.add(shadowFaces[i]);
  }
  const shadowEdgeGeo = new THREE.BufferGeometry();
  shadowEdgeGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(CUBE_EDGES.length * 6), 3));
  const shadowEdge = new THREE.LineSegments(
    shadowEdgeGeo, new THREE.LineBasicMaterial({ color: 0x999999, transparent: true, opacity: 0 })
  );
  group.add(shadowEdge);

  scene.add(group);
  objMeshes.set(obj.id, { group, faces, edgeLine, shadowFaces, shadowEdge, type: 'UnitCube' });
}

function syncCubeMesh(obj) {
  const m = objMeshes.get(obj.id);
  if (!m) return;
  const v = obj.vertices;
  const isActive = obj.id === activeId;

  for (let i = 0; i < 6; i++) {
    const f = CUBE_FACES[i];
    const pos = m.faces[i].geometry.attributes.position;
    writeQuad(pos.array, 0, v[f[0]], v[f[1]], v[f[2]], v[f[3]]);
    pos.needsUpdate = true;
    m.faces[i].geometry.computeVertexNormals();
    m.faces[i].geometry.computeBoundingSphere();
    m.faces[i].material.opacity = isActive ? 0.7 : 0.4;
  }

  const ep = m.edgeLine.geometry.attributes.position;
  for (let i = 0; i < CUBE_EDGES.length; i++) {
    const [a, b] = CUBE_EDGES[i];
    ep.array.set(v[a], i * 6);
    ep.array.set(v[b], i * 6 + 3);
  }
  ep.needsUpdate = true;
  m.edgeLine.material.opacity = isActive ? 1.0 : 0.4;

  if (obj.shadowVerts) {
    const sv = obj.shadowVerts;
    for (let i = 0; i < 6; i++) {
      const f = CUBE_FACES[i];
      const sp = m.shadowFaces[i].geometry.attributes.position;
      writeQuad(sp.array, 0, sv[f[0]], sv[f[1]], sv[f[2]], sv[f[3]]);
      sp.needsUpdate = true;
      m.shadowFaces[i].geometry.computeVertexNormals();
      m.shadowFaces[i].geometry.computeBoundingSphere();
      m.shadowFaces[i].material.opacity = 0.15;
    }
    const sep = m.shadowEdge.geometry.attributes.position;
    for (let i = 0; i < CUBE_EDGES.length; i++) {
      const [a, b] = CUBE_EDGES[i];
      sep.array.set(sv[a], i * 6);
      sep.array.set(sv[b], i * 6 + 3);
    }
    sep.needsUpdate = true;
    m.shadowEdge.material.opacity = 0.3;
  } else {
    m.shadowFaces.forEach(f => { f.material.opacity = 0; });
    m.shadowEdge.material.opacity = 0;
  }
}

function buildPointMesh(obj) {
  const group = new THREE.Group();
  
  const geo = new THREE.SphereGeometry(0.12, 16, 16);
  const mat = new THREE.MeshPhongMaterial({ color: 0x000000 });
  const mesh = new THREE.Mesh(geo, mat);
  group.add(mesh);
  
  // find out why the shadow lies at the origin too

  const shadowGeo = new THREE.SphereGeometry(0.12, 16, 16);
  const shadowMat = new THREE.MeshPhongMaterial({ color: 0xaaaaaa, transparent: false, opacity: 0});
  const shadowMesh = new THREE.Mesh(shadowGeo, shadowMat);
  group.add(shadowMesh);
  
  scene.add(group);
  objMeshes.set(obj.id, { group, mesh, shadowMesh, type: 'Point' });
}

function syncPointMesh(obj) {
  const m = objMeshes.get(obj.id);
  if (!m) return;
  const isActive = obj.id === activeId;
  const [x, y, z] = obj.vertices[0];
  
  m.mesh.position.set(x, y, z);
  m.mesh.material.color.setHex(isActive ? 0xff4444 : 0xcc4444);
  m.mesh.material.opacity = isActive ? 1.0 : 0.6;
  m.mesh.material.transparent = true;

  if (obj.shadowVerts) {
    const [sx, sy, sz] = obj.shadowVerts[0];
    m.shadowMesh.position.set(sx, sy, sz);
    m.shadowMesh.material.opacity = 0.3;
  } else {
    m.shadowMesh.material.opacity = 0;
  }
}

function buildMesh(obj) {
  if (obj.type === 'Point') buildPointMesh(obj);
  else buildCubeMesh(obj);
}

function syncMesh(obj) {
  if (obj.type === 'Point') syncPointMesh(obj);
  else syncCubeMesh(obj);
}

function removeMesh(id) {
  const m = objMeshes.get(id);
  if (m) { scene.remove(m.group); objMeshes.delete(id); }
  removeTransformVis(id);
}

const transformVis = new Map();

function addTransformVis(objId, type, params) {
  const arr = transformVis.get(objId) || [];
  let vis;

  if (type === 'segment') {
    const geo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(...params.from),
      new THREE.Vector3(...params.to),
    ]);
    vis = new THREE.Line(geo, new THREE.LineBasicMaterial({ color: 0x000000, opacity: 0.4, transparent: true }));

  } else if (type === 'line') {
    const [px, py, pz] = params.p;
    const [dx, dy, dz] = params.d;
    const geo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(px - 500*dx, py - 500*dy, pz - 500*dz),
      new THREE.Vector3(px + 500*dx, py + 500*dy, pz + 500*dz),
    ]);
    vis = new THREE.Line(geo, new THREE.LineBasicMaterial({ color: 0x333333, opacity: 0.5, transparent: true }));

  } else if (type === 'plane') {
    const { a, b, c, d } = params;
    const n = new THREE.Vector3(a, b, c).normalize();
    const pt = new THREE.Vector3(a, b, c).multiplyScalar(d / (a*a + b*b + c*c));
    let perp1 = new THREE.Vector3(1, 0, 0);
    if (Math.abs(n.dot(perp1)) > 0.9) perp1 = new THREE.Vector3(0, 1, 0);
    perp1.cross(n).normalize().multiplyScalar(4);
    const perp2 = new THREE.Vector3().crossVectors(n, perp1).normalize().multiplyScalar(4);
    const corners = [
      pt.clone().sub(perp1).sub(perp2),
      pt.clone().sub(perp1).add(perp2),
      pt.clone().add(perp1).add(perp2),
      pt.clone().add(perp1).sub(perp2),
    ];
    const geo = new THREE.BufferGeometry().setFromPoints([...corners, corners[0]]);
    vis = new THREE.Line(geo, new THREE.LineBasicMaterial({ color: 0x555555, opacity: 0.5, transparent: true }));
  }

  if (vis) { scene.add(vis); arr.push(vis); transformVis.set(objId, arr); }
}

function popTransformVis(objId) {
  const arr = transformVis.get(objId) || [];
  if (arr.length) { scene.remove(arr.pop()); transformVis.set(objId, arr); }
}

function removeTransformVis(id) {
  const arr = transformVis.get(id) || [];
  arr.forEach(o => scene.remove(o));
  transformVis.delete(id);
}

function clearTransformVis(objId) {
  removeTransformVis(objId);
}



const origApplyTransform = SceneObj.prototype.applyTransform;
SceneObj.prototype.applyTransform = function(mat, name) {
  this.shadowVerts = this.vertices.map(v => [...v]);
  const prevCentre = [...this.centre];
  origApplyTransform.call(this, mat, name);
  if (name === 'Translation') {
    addTransformVis(this.id, 'segment', { from: [...this.centre], to: prevCentre });
  } else if (name === 'Reflection ∥ Plane') {
    addTransformVis(this.id, 'plane', this.lastPlaneParams || { a:0, b:0, c:1, d:0 });
  } else if (name === 'Reflection ∥ Line') {
    addTransformVis(this.id, 'line', this.lastLineParams || { p:[0,0,0], d:[0,0,1] });
  }
};

const origUndo = SceneObj.prototype.undo;
SceneObj.prototype.undo = function() {
  const result = origUndo.call(this);
  this.shadowVerts = null;
  popTransformVis(this.id);
  return result;
};

const origReset = SceneObj.prototype.reset;
SceneObj.prototype.reset = function() {
  origReset.call(this);
  this.shadowVerts = null;
  clearTransformVis(this.id);
};

const origReflectPlaneApply = MODAL_CONFIGS.reflectPlane.apply;
MODAL_CONFIGS.reflectPlane.apply = function(vals, obj) {
  obj.lastPlaneParams = { a: vals.a, b: vals.b, c: vals.c, d: vals.d };
  origReflectPlaneApply(vals, obj);
};

const origReflectLineApply = MODAL_CONFIGS.reflectLine.apply;
MODAL_CONFIGS.reflectLine.apply = function(vals, obj) {
  obj.lastLineParams = { p: [vals.a1, vals.a2, vals.a3], d: [vals.d1, vals.d2, vals.d3] };
  origReflectLineApply(vals, obj);
};

const origAddObject = addObject;
addObject = function(type = 'UnitCube', args) {
  origAddObject(type, args);
  const obj = objects[objects.length - 1];
  obj.shadowVerts = null;
  buildMesh(obj);
};

const origDoConfirm = doConfirm;
doConfirm = function() {
  const action = pendingAction;
  const obj = getActive();
  if (action === 'delete' && obj) removeMesh(obj.id);
  origDoConfirm();
};

objects.forEach(obj => {
  obj.shadowVerts = null;
  buildMesh(obj);
});

onFrame = () => {
  objects.forEach(obj => syncMesh(obj));
};


const lpMeshes = new Map();
 
function syncLinesPlanes() {
  if (typeof SAVED_LP === 'undefined') return;
  const live = new Set(SAVED_LP.map(o => o.id));
  for (const [id, mesh] of lpMeshes)
    if (!live.has(id)) { scene.remove(mesh); lpMeshes.delete(id); }
 
  for (const o of SAVED_LP) {
    if (lpMeshes.has(o.id)) continue;
    let mesh;
    if (o.kind === 'line') {
      const { a1, a2, a3, d1, d2, d3 } = o.p;
      const L = Math.hypot(d1, d2, d3) || 1;
      const u = [d1 / L, d2 / L, d3 / L], E = 12;
      const geo = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(a1 - u[0]*E, a2 - u[1]*E, a3 - u[2]*E),
        new THREE.Vector3(a1 + u[0]*E, a2 + u[1]*E, a3 + u[2]*E),
      ]);
      mesh = new THREE.Line(geo,
        new THREE.LineDashedMaterial({ color: 0x9b59b6, dashSize: 0.25, gapSize: 0.15 }));
      mesh.computeLineDistances();
    } else {
      const { a, b, c, d } = o.p;
      const n2 = a*a + b*b + c*c || 1;
      const p0 = [a*d/n2, b*d/n2, c*d/n2];
      let t = Math.abs(a) < 0.9 ? [1, 0, 0] : [0, 1, 0];
      let e1 = [b*t[2]-c*t[1], c*t[0]-a*t[2], a*t[1]-b*t[0]];
      const l1 = Math.hypot(...e1); e1 = e1.map(v => v / l1);
      let e2 = [b*e1[2]-c*e1[1], c*e1[0]-a*e1[2], a*e1[1]-b*e1[0]];
      const l2 = Math.hypot(...e2); e2 = e2.map(v => v / l2);
      const S = 5;
      const corners = [[+1,+1],[-1,+1],[-1,-1],[+1,-1]].map(([s1,s2]) =>
        new THREE.Vector3(
          p0[0] + S*(s1*e1[0] + s2*e2[0]),
          p0[1] + S*(s1*e1[1] + s2*e2[1]),
          p0[2] + S*(s1*e1[2] + s2*e2[2])));
      const geo = new THREE.BufferGeometry().setFromPoints(
        [corners[0], corners[1], corners[2], corners[0], corners[2], corners[3]]);
      geo.computeVertexNormals();
      mesh = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({
        color: 0x2ebdbd, transparent: true, opacity: 0.15,
        side: THREE.DoubleSide, depthWrite: false }));
    }
    scene.add(mesh);
    lpMeshes.set(o.id, mesh);
  }
}
 