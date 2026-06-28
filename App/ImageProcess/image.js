'use strict';
 
const IMG = {
  layers:   [],        // Layer[], index 0 = bottom of stack
  activeId: null,
  nextId:  1,
};
 
// ── Layer ─────────────────────────────────────────────────────────
 
class Layer {
  constructor(name, imgEl) {
    this.id     = IMG.nextId++;          
    this.name   = name;
    this.x      = 0;
    this.y      = 0;

    this.canvas        = document.createElement('canvas');
    this.canvas.width  = imgEl.naturalWidth  || imgEl.width  || 1;
    this.canvas.height = imgEl.naturalHeight || imgEl.height || 1;
    this.ctx          = this.canvas.getContext('2d', { willReadFrequently: true });
    this.ctx.drawImage(imgEl, 0, 0);

    this.ops    = [];
    this.snaps = [this.getImageData()];
    this.step   = 0;
  }

  get width()     { return this.canvas.width;  }
  get height()    { return this.canvas.height; }
  get stepCount() { return this.ops.length + 1; }
  getCtx()        { return this.ctx;           }
  getImageData()  { return this.ctx.getImageData(0, 0, this.width, this.height); }
  putImageData(d) { this.ctx.putImageData(d, 0, 0); }

  ensureSnap(i) {
    while (this.snaps.length <= i) {
      const k = this.snaps.length;
      this.putImageData(this.snaps[k - 1]);
      const op = this.ops[k - 1];
      FX[op.type](this, ...op.params);
      this.snaps.push(this.getImageData());
    }
  }

  gotoStep(i) {
    if (i < 0 || i >= this.stepCount) return false;
    this.ensureSnap(i);
    this.step = i;
    this.putImageData(this.snaps[i]);
    return true;
  }

  addOp(type, params, label, detail = '') {
    this.ops.push({ type, params, label, detail });
    this.gotoStep(this.ops.length);
  }

  removeOp(k) {
    if (k < 0 || k >= this.ops.length) return;
    this.ops.splice(k, 1);
    this.snaps.length = k + 1;
    this.step = Math.min(this.step, this.stepCount - 1);
    this.gotoStep(this.step);
  }

  moveOp(from, to) {
    if (from === to || from < 0 || to < 0
        || from >= this.ops.length || to >= this.ops.length) return;
    const [op] = this.ops.splice(from, 1);
    this.ops.splice(to, 0, op);
    this.snaps.length = Math.min(from, to) + 1;
    this.gotoStep(this.step);
  }
}

// ── Colour Adjustment ──────────────────────────────────────────────
 
function fxColour(layer, relR, relG, relB, absR, absG, absB) {
  const id = layer.getImageData();
  const d  = id.data;
  for (let i = 0; i < d.length; i += 4) {
    d[i]   = Math.min(255, Math.max(0, d[i]   * relR + absR));
    d[i+1] = Math.min(255, Math.max(0, d[i+1] * relG + absG));
    d[i+2] = Math.min(255, Math.max(0, d[i+2] * relB + absB));
  }
  layer.putImageData(id);
}
 
// ── Sepia ──────────────────────────────────────────────────────────
 
function fxSepia(layer) {
  const id = layer.getImageData();
  const d  = id.data;
  for (let i = 0; i < d.length; i += 4) {
    const r = d[i], g = d[i+1], b = d[i+2];
    d[i]   = Math.min(255, 0.393*r + 0.769*g + 0.189*b);
    d[i+1] = Math.min(255, 0.349*r + 0.686*g + 0.168*b);
    d[i+2] = Math.min(255, 0.272*r + 0.534*g + 0.131*b);
  }
  layer.putImageData(id);
}
 
// ── Gaussian Blur ──────────────────────────────────────────────────

function fxGaussianBlur(layer, sd) {
  const tmp    = document.createElement('canvas');
  tmp.width    = layer.width;
  tmp.height   = layer.height;
  const tc     = tmp.getContext('2d');
  tc.filter    = `blur(${sd}px)`;
  tc.drawImage(layer.canvas, 0, 0);
  tc.filter    = 'none';
  const ctx    = layer.getCtx();
  ctx.clearRect(0, 0, layer.width, layer.height);
  ctx.drawImage(tmp, 0, 0);
}
 
// ── Median Blur ────────────────────────────────────────────────────
// Will lag
 
function fxMedianBlur(layer, r) {
  const id   = layer.getImageData();
  const w    = layer.width, h = layer.height;
  const src  = id.data;
  const out  = new Uint8ClampedArray(src.length);
  const n    = (2*r + 1) ** 2;
  const mid  = Math.floor(n / 2);
 
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const rs = [], gs = [], bs = [];
      for (let ky = -r; ky <= r; ky++) {
        for (let kx = -r; kx <= r; kx++) {
          const sy  = Math.min(h-1, Math.max(0, y + ky));
          const sx  = Math.min(w-1, Math.max(0, x + kx));
          const idx = (sy*w + sx) * 4;
          rs.push(src[idx]);
          gs.push(src[idx+1]);
          bs.push(src[idx+2]);
        }
      }
      rs.sort((a, b) => a-b);
      gs.sort((a, b) => a-b);
      bs.sort((a, b) => a-b);
      const oi    = (y*w + x) * 4;
      out[oi]     = rs[mid];
      out[oi + 1] = gs[mid];
      out[oi + 2] = bs[mid];
      out[oi + 3] = src[oi + 3];
    }
  }
  layer.putImageData(new ImageData(out, w, h));
}
 
// ── Sobel Edge Detection ───────────────────────────────────────────
 
function fxSobelEdge(layer) {
  const id   = layer.getImageData();
  const w    = layer.width, h = layer.height;
  const src  = id.data;
  const gray = new Float32Array(w * h);
 
  for (let i = 0; i < w * h; i++)
    gray[i] = 0.299*src[i*4] + 0.587*src[i*4+1] + 0.114*src[i*4+2];
 
  const Kx  = [-1, 0, 1,  -2, 0, 2,  -1, 0, 1];
  const Ky  = [-1,-2,-1,   0, 0, 0,   1, 2, 1];
  const out = new Uint8ClampedArray(src.length);
 
  for (let y = 1; y < h-1; y++) {
    for (let x = 1; x < w-1; x++) {
      let gx = 0, gy = 0;
      for (let ky = -1; ky <= 1; ky++) {
        for (let kx = -1; kx <= 1; kx++) {
          const g  = gray[(y+ky)*w + (x+kx)];
          const ki = (ky+1)*3 + (kx+1);
          gx += Kx[ki]*g;
          gy += Ky[ki]*g;
        }
      }
      const oi  = (y*w + x) * 4;
      const mag = Math.min(255, Math.hypot(gx, gy));
      out[oi] = out[oi+1] = out[oi+2] = mag;
      out[oi + 3] = 255;
    }
  }
  layer.putImageData(new ImageData(out, w, h));
}
 
const FX = {
  colour:   fxColour,
  sepia:    fxSepia,
  gaussian: fxGaussianBlur,
  median:   fxMedianBlur,
  sobel:    fxSobelEdge,
};
 
// API ──────────────────────────────────────────────

function applyColourFilter(layer, relR, relG, relB, absR, absG, absB) {
  layer.addOp('colour', [relR, relG, relB, absR, absG, absB],
    'Colour adjustment',
    `R ×${relR.toFixed(2)} ${absR >= 0 ? '+' : ''}${absR} · ` +
    `G ×${relG.toFixed(2)} ${absG >= 0 ? '+' : ''}${absG} · ` +
    `B ×${relB.toFixed(2)} ${absB >= 0 ? '+' : ''}${absB}`);
}
 
function applySepiaFilter(layer) {
  layer.addOp('sepia', [], 'Sepia', 'Standard sepia channel-mix matrix');
}
 
function applyGaussianBlur(layer, sd) {
  layer.addOp('gaussian', [sd], `Gaussian blur (σ = ${sd})`,
    'GPU-accelerated via CSS filter');
}
 
function applyMedianBlur(layer, r) {
  layer.addOp('median', [r], `Median blur (r = ${r})`,
    `(2r+1)² = ${(2*r+1)**2}-pixel neighbourhood median`);
}
 
function applySobelEdge(layer) {
  layer.addOp('sobel', [], 'Sobel edges',
    'Greyscale → Kx, Ky kernels → gradient magnitude');
}
 
// ── I/O ───────────────────────────────────────────────────────────
 
function layerFromFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = e => {
      const img = new Image();
      img.onload  = () => resolve(new Layer(file.name, img));
      img.onerror = () => reject(new Error('Could not decode image: ' + file.name));
      img.src = e.target.result;   // data URL — no revocation needed
    };
    reader.onerror = () => reject(new Error('Could not read file: ' + file.name));
    reader.readAsDataURL(file);
  });
}
 
function saveLayer(layer) {
  const dot  = layer.name.lastIndexOf('.');
  const base = dot >= 0 ? layer.name.slice(0, dot) : layer.name;
  const a    = document.createElement('a');
  a.download = base + '-out.png';
  a.href     = layer.canvas.toDataURL('image/png');
  a.click();
}