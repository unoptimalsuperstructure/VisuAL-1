'use strict';

const isMat16 = m => Array.isArray(m) && m.length === 16 && m.every(v => isFinite(+v));

function serialise3D() {
  return {
    objects: objects.map(o => ({
      type: o.type,
      initArgs: o.initArgs,
      stack: o.matrixStack.slice(1).map(([m, n]) => [m, String(n)]),
    })),
    savedLP: SAVED_LP.map(({ kind, name, p }) => ({ kind, name, p })),
  };
}

function restore3D(p) {
  if (!p || !Array.isArray(p.objects))
    return 'This save does not look like a 3D scene.';
  for (const o of p.objects) {
    if (!SHAPE_GEOMETRY[o.type]) return `Unknown shape "${String(o.type)}".`;
    if (o.stack && o.stack.some(s => !Array.isArray(s) || !isMat16(s[0])))
      return 'A saved transform matrix is malformed.';
  }
  objects.length = 0;
  for (const o of p.objects) {
    const obj = new SceneObj(o.type, o.initArgs ?? null);
    for (const [m, n] of (o.stack || []))
      obj.applyTransform(m.map(Number), String(n));
    objects.push(obj);
  }
  activeId = objects.length ? objects[objects.length - 1].id : null;

  SAVED_LP.length = 0;
  for (const lp of (Array.isArray(p.savedLP) ? p.savedLP : [])) {
    if ((lp.kind === 'line' || lp.kind === 'plane') && lp.p)
      SAVED_LP.push({ id: SAVED_LP.length + 1, kind: lp.kind,
                      name: String(lp.name ?? lp.kind), p: lp.p });
  }
  lpCounter = SAVED_LP.length;

  renderObjList();
  renderStack();
  afterLPChange();
  return null;
}

initToolSave({
  tool: '3d',
  serialise: serialise3D,
  restore: restore3D,
  empty: () => objects.length ? false : 'Add an object to the scene first.',
});