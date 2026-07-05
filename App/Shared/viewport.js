const canvas = document.getElementById('gl');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setClearColor(0xf5f5f5);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(60, 1, 0.05, 200);

scene.add(new THREE.AmbientLight(0xffffff, 0.7));
const dirLight = new THREE.DirectionalLight(0xffffff, 0.6);
dirLight.position.set(5, 5, 8);
scene.add(dirLight);

function makeAxis(from, to, color) {
  const geo = new THREE.BufferGeometry().setFromPoints([
    new THREE.Vector3(...from),
    new THREE.Vector3(...to),
  ]);
  return new THREE.Line(geo, new THREE.LineBasicMaterial({ color }));
}

// x and y axis not colored, might be due to the grid helper since z axis is not affected
scene.add(makeAxis([-10,0,0], [10,0,0], 0xcc0000));
scene.add(makeAxis([0,-10,0], [0,10,0], 0x00aa00));
scene.add(makeAxis([0,0,-10], [0,0,10], 0x0000cc));

const grid = new THREE.GridHelper(20, 20, 0xcccccc, 0xdddddd);
grid.rotation.x = Math.PI / 2;
scene.add(grid);

let camRadius = 6, camTheta = Math.PI / 4, camPhi = Math.PI / 3;

function resetCamera() {
  camRadius = 6; camTheta = Math.PI / 4; camPhi = Math.PI / 3;
  updateCamera();
}

function updateCamera() {
  const x = camRadius * Math.sin(camPhi) * Math.cos(camTheta);
  const y = camRadius * Math.sin(camPhi) * Math.sin(camTheta);
  const z = camRadius * Math.cos(camPhi);
  camera.position.set(x, y, z);
  camera.up.set(0, 0, 1);
  camera.lookAt(0, 0, 0);
}
resetCamera();

let isDragging = false, lastMx = 0, lastMy = 0;

canvas.addEventListener('mousedown', e => {
  if (e.button === 0) { isDragging = true; lastMx = e.clientX; lastMy = e.clientY; }
  if (e.button === 1) { e.preventDefault(); resetCamera(); }
});
window.addEventListener('mouseup', () => { isDragging = false; });
window.addEventListener('mousemove', e => {
  if (!isDragging) return;
  camTheta -= (e.clientX - lastMx) * 0.006;
  camPhi = Math.max(0.05, Math.min(Math.PI - 0.05, camPhi + (e.clientY - lastMy) * 0.006));
  lastMx = e.clientX; lastMy = e.clientY;
  updateCamera();
});
canvas.addEventListener('wheel', e => {
  camRadius = Math.max(1.5, Math.min(40, camRadius + e.deltaY * 0.01));
  updateCamera();
}, { passive: true });
canvas.addEventListener('contextmenu', e => e.preventDefault());

const keysDown = new Set();
 
function cameraKeysBlocked() {
  const ae = document.activeElement;
  if (ae && /^(INPUT|SELECT|TEXTAREA)$/.test(ae.tagName)) return true;
  for (const m of document.querySelectorAll('.modal-bg'))
    if (m.style.display !== 'none') return true;
  return false;
}
 
window.addEventListener('keydown', e => {
  if (cameraKeysBlocked()) return;
  keysDown.add(e.key.toLowerCase());
});
window.addEventListener('keyup', e => keysDown.delete(e.key.toLowerCase()));
 
function processKeys() {
  const speed = 0.05;
  if (keysDown.has('w') || keysDown.has('arrowup'))    camRadius = Math.max(1.5, camRadius - speed * 3);
  if (keysDown.has('s') || keysDown.has('arrowdown'))  camRadius = Math.min(40,  camRadius + speed * 3);
  if (keysDown.has('a') || keysDown.has('arrowleft'))  camTheta -= speed * 0.5;
  if (keysDown.has('d') || keysDown.has('arrowright')) camTheta += speed * 0.5;
  if (keysDown.has(' '))     camPhi = Math.max(0.05, camPhi - speed * 0.5);
  if (keysDown.has('shift')) camPhi = Math.min(Math.PI - 0.05, camPhi + speed * 0.5);
  if (keysDown.size) updateCamera();
}

let onFrame = null;
 
function resizeIfNeeded() {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  if (canvas.width !== w || canvas.height !== h) {
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
}
 
function animate() {
  requestAnimationFrame(animate);
  resizeIfNeeded();
  processKeys();
  if (onFrame) onFrame();
  renderer.render(scene, camera);
}
animate();