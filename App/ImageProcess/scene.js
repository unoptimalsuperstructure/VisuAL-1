'use strict';

function getActiveLayer() {
  return IMG.layers.find(l => l.id === IMG.activeId) ?? null;
}

function selectLayer(id) {
  IMG.activeId = id;
  refreshLayerList();
  refreshStepsList();
  renderFrame();
}

function addLayer(layer) {
  IMG.layers.push(layer);
  if (IMG.activeId === null) IMG.activeId = layer.id;
  refreshLayerList();
  refreshStepsList();
  renderFrame();
}

function removeActiveLayer() {
  if (IMG.activeId === null) return;
  const idx = IMG.layers.findIndex(l => l.id === IMG.activeId);
  if (idx === -1) return;
  IMG.layers.splice(idx, 1);
  IMG.activeId = IMG.layers.length
    ? IMG.layers[Math.min(idx, IMG.layers.length - 1)].id
    : null;
  refreshLayerList();
  refreshStepsList();
  renderFrame();
}

function undoActiveLayer() {
  const l = getActiveLayer();
  if (!l) return warn('Select an image first.');
  if (!l.gotoStep(l.step - 1)) return warn('Already at the original image.');
  refreshStepsList();
  renderFrame();
}

function gotoLayerStep(i) {
  const l = getActiveLayer();
  if (!l) return;
  l.gotoStep(i);
  refreshStepsList();
  renderFrame();
}

function removeLayerOp(k) {
  const l = getActiveLayer();
  if (!l) return;
  l.removeOp(k);
  refreshStepsList();
  renderFrame();
}

function moveLayerOp(from, to) {
  const l = getActiveLayer();
  if (!l) return;
  l.moveOp(from, to);
  refreshStepsList();
  renderFrame();
}