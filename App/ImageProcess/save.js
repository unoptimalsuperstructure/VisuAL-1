'use strict';

function layerOriginalDataURL(l) {
  const c = document.createElement('canvas');
  c.width = l.width; c.height = l.height;
  c.getContext('2d').putImageData(l.snaps[0], 0, 0);
  return c.toDataURL('image/jpeg', 0.92);
}

function serialiseImage() {
  return {
    layers: IMG.layers.map(l => ({
      name: l.name,
      src: layerOriginalDataURL(l),
      ops: l.ops.map(op => ({ type: op.type, params: op.params })),
      step: l.step,
    })),
  };
}

function restoreImage(p) {
  if (!p || !Array.isArray(p.layers) || !p.layers.length)
    return Promise.resolve('This save does not look like an image project.');
  for (const L of p.layers) {
    if (typeof L.src !== 'string' || !L.src.startsWith('data:image/'))
      return Promise.resolve('A saved layer has no valid image data.');
    for (const op of (L.ops || []))
      if (typeof FX[op.type] !== 'function' || !Array.isArray(op.params))
        return Promise.resolve(`Unknown filter "${String(op.type)}" in this save.`);
  }
  const loads = p.layers.map(L => new Promise(res => {
    const img = new Image();
    img.onload = () => res({ L, img });
    img.onerror = () => res(null);
    img.src = L.src;
  }));
  return Promise.all(loads).then(pairs => {
    if (pairs.some(x => !x)) return 'A saved image failed to decode.';
    IMG.layers.length = 0;
    for (const { L, img } of pairs) {
      const layer = new Layer(String(L.name ?? 'layer'), img);
      layer.ops = L.ops.map(op => ({ type: op.type, params: op.params }));
      const step = Number.isInteger(L.step)
        ? Math.max(0, Math.min(L.step, layer.ops.length)) : layer.ops.length;
      layer.gotoStep(step);
      IMG.layers.push(layer);
    }
    IMG.activeId = IMG.layers[0].id;
    refreshLayerList();
    refreshStepsList();
    renderFrame();
    return null;
  });
}

initToolSave({
  tool: 'image',
  serialise: serialiseImage,
  restore: restoreImage,
  empty: () => IMG.layers.length ? false : 'Add an image first.',
});