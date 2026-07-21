'use strict';
 
// REMINDER TO MYSELF: USE COLOR NOT COLOUR!!!

const IMG = {
  layers:   [],
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

// ── color Adjustment ──────────────────────────────────────────────
 
function fxColor(layer, relR, relG, relB, absR, absG, absB) {
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
// Testing huang algo lol
 
function fxMedianBlur(layer, r) {
  const id  = layer.getImageData();
  const w   = layer.width, h = layer.height;
  const src = id.data;
  const out = new Uint8ClampedArray(src.length);
  const half = Math.floor(((2*r + 1) ** 2) / 2);
  const hist = [new Uint32Array(256), new Uint32Array(256), new Uint32Array(256)];
  const clampY = y => y < 0 ? 0 : y >= h ? h - 1 : y;
  const clampX = x => x < 0 ? 0 : x >= w ? w - 1 : x;
 
  for (let y = 0; y < h; y++) {
    hist[0].fill(0); hist[1].fill(0); hist[2].fill(0);
    for (let ky = -r; ky <= r; ky++)               // seed the window at x = 0
      for (let kx = -r; kx <= r; kx++) {
        const idx = (clampY(y + ky) * w + clampX(kx)) * 4;
        hist[0][src[idx]]++; hist[1][src[idx + 1]]++; hist[2][src[idx + 2]]++;
      }
    for (let x = 0; x < w; x++) {
      const oi = (y * w + x) * 4;
      for (let c = 0; c < 3; c++) {                // median = first bin past half
        let acc = 0, v = 0;
        const H = hist[c];
        while (acc + H[v] <= half) acc += H[v++];
        out[oi + c] = v;
      }
      out[oi + 3] = src[oi + 3];
      if (x < w - 1) {                             // slide: drop col x−r, add col x+r+1
        const xr = clampX(x - r), xa = clampX(x + r + 1);
        for (let ky = -r; ky <= r; ky++) {
          const row = clampY(y + ky) * w;
          const ri = (row + xr) * 4, ai = (row + xa) * 4;
          hist[0][src[ri]]--; hist[1][src[ri + 1]]--; hist[2][src[ri + 2]]--;
          hist[0][src[ai]]++; hist[1][src[ai + 1]]++; hist[2][src[ai + 2]]++;
        }
      }
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


// ── Grayscale ──────────────────────────────────────────────────────

function fxGrayscale(layer, v) {
  const id = layer.getImageData(), d = id.data;
  for (let i = 0; i < d.length; i += 4) {
    const luma = 0.2126*d[i] + 0.7152*d[i+1] + 0.0722*d[i+2];
    d[i]   = d[i]   * (1 - v) + luma * v;
    d[i+1] = d[i+1] * (1 - v) + luma * v;
    d[i+2] = d[i+2] * (1 - v) + luma * v;
  }
  layer.putImageData(id);
}

// ── Inversion ──────────────────────────────────────────────────────

function fxInversion(layer, v) {
  const id = layer.getImageData(), d = id.data;
  for (let i = 0; i < d.length; i += 4) {
    d[i]   = d[i]   * (1 - v) + (255 - d[i])   * v;
    d[i+1] = d[i+1] * (1 - v) + (255 - d[i+1]) * v;
    d[i+2] = d[i+2] * (1 - v) + (255 - d[i+2]) * v;
  }
  layer.putImageData(id);
}

// ── Coloor Rotation ────────────────────────────────────────────────

const COLOR_ROTATIONS = {
  RGB: [0, 1, 2], RBG: [1, 0, 2], GRB: [0, 2, 1],
  GBR: [2, 0, 1], BRG: [1, 2, 0], BGR: [2, 1, 0],
};

function fxColorRotation(layer, rotation) {
  const [ri, gi, bi] = COLOR_ROTATIONS[rotation] || [0, 1, 2];
  const id = layer.getImageData(), d = id.data;
  for (let i = 0; i < d.length; i += 4) {
    const c = [d[i], d[i+1], d[i+2]];
    d[i] = c[ri]; d[i+1] = c[gi]; d[i+2] = c[bi];
  }
  layer.putImageData(id);
}

// ── Box Blur ───────────────────────────────────────────────────────

function fxBoxBlur(layer, r) {
  const w = layer.width, h = layer.height;
  const src = layer.getImageData().data;
  const tmp = new Float32Array(src.length);
  const out = new Uint8ClampedArray(src.length);
  const n = 2*r + 1;

  for (let y = 0; y < h; y++)
    for (let x = 0; x < w; x++) {
      let sr=0, sg=0, sb=0, sa=0;
      for (let k = -r; k <= r; k++) {
        const sx = Math.min(w-1, Math.max(0, x+k)), idx = (y*w + sx)*4;
        sr+=src[idx]; sg+=src[idx+1]; sb+=src[idx+2]; sa+=src[idx+3];
      }
      const o = (y*w + x)*4;
      tmp[o]=sr/n; tmp[o+1]=sg/n; tmp[o+2]=sb/n; tmp[o+3]=sa/n;
    }
  for (let y = 0; y < h; y++)
    for (let x = 0; x < w; x++) {
      let sr=0, sg=0, sb=0, sa=0;
      for (let k = -r; k <= r; k++) {
        const sy = Math.min(h-1, Math.max(0, y+k)), idx = (sy*w + x)*4;
        sr+=tmp[idx]; sg+=tmp[idx+1]; sb+=tmp[idx+2]; sa+=tmp[idx+3];
      }
      const o = (y*w + x)*4;
      out[o]=sr/n; out[o+1]=sg/n; out[o+2]=sb/n; out[o+3]=sa/n;
    }
  layer.putImageData(new ImageData(out, w, h));
}

// ── Pixelate ───────────────────────────────────────────────────────

function fxPixelate(layer, v) {
  const w = layer.width, h = layer.height;
  const size = Math.max(1, Math.floor(Math.max(w, h) / v));
  const small = document.createElement('canvas');
  small.width = size; small.height = size;
  small.getContext('2d').drawImage(layer.canvas, 0, 0, size, size);
  const ctx = layer.getCtx();
  ctx.imageSmoothingEnabled = false;
  ctx.clearRect(0, 0, w, h);
  ctx.drawImage(small, 0, 0, size, size, 0, 0, w, h);
  ctx.imageSmoothingEnabled = true;
}

// ── Sharpen ────────────────────────────────────────────────────────

function fxSharpen(layer, v) {
  const w = layer.width, h = layer.height;
  const blur = document.createElement('canvas');
  blur.width = w; blur.height = h;
  const bc = blur.getContext('2d', { willReadFrequently: true });
  bc.filter = 'blur(1px)';                 // ≈ GaussianBlur(7×7, σ=1)
  bc.drawImage(layer.canvas, 0, 0);
  bc.filter = 'none';
  const bd = bc.getImageData(0, 0, w, h).data;
  const id = layer.getImageData(), d = id.data;
  for (let i = 0; i < d.length; i += 4) {
    d[i]   = d[i]   * (v + 1) - bd[i]   * v;   // Uint8ClampedArray clamps
    d[i+1] = d[i+1] * (v + 1) - bd[i+1] * v;
    d[i+2] = d[i+2] * (v + 1) - bd[i+2] * v;
  }
  layer.putImageData(id);
}

function makeOrth(w, k) {
  return M => {
    for (let c = 0; c < k; c++) {
      for (let attempt = 0; attempt < 3; attempt++) {
        let before = 0;
        for (let r = 0; r < w; r++) before += M[r*k+c] ** 2;
        for (let pass = 0; pass < 2; pass++)
          for (let p = 0; p < c; p++) {
            let dot = 0;
            for (let r = 0; r < w; r++) dot += M[r*k+c] * M[r*k+p];
            for (let r = 0; r < w; r++) M[r*k+c] -= dot * M[r*k+p];
          }
        let n = 0;
        for (let r = 0; r < w; r++) n += M[r*k+c] ** 2;
        if (n > 1e-20 * (before || 1)) {
          n = Math.sqrt(n);
          for (let r = 0; r < w; r++) M[r*k+c] /= n;
          break;
        }
        for (let r = 0; r < w; r++) M[r*k+c] = Math.random() - 0.5;
      }
    }
  };
}
 
function rankKApprox(A, h, w, k, iters = 4) {
  k = Math.min(k, w, h);
  const orth = makeOrth(w, k);
  let V = new Float64Array(w * k);
  for (let i = 0; i < V.length; i++) V[i] = Math.random() - 0.5;
  orth(V);

  if (typeof svdWasmRankK === 'function') {
    const B = svdWasmRankK(A, h, w, k, iters, V, orth);
    if (B) return B;
  }
  // IN CASE WASM DOESNT WORK!!
  const AV = new Float64Array(h * k), W = new Float64Array(w * k);
  for (let it = 0; it < iters; it++) {
    AV.fill(0);
    for (let r = 0; r < h; r++)
      for (let c = 0; c < w; c++) {
        const a = A[r*w+c]; if (!a) continue;
        for (let j = 0; j < k; j++) AV[r*k+j] += a * V[c*k+j];
      }
    W.fill(0);
    for (let r = 0; r < h; r++)
      for (let c = 0; c < w; c++) {
        const a = A[r*w+c];
        for (let j = 0; j < k; j++) W[c*k+j] += a * AV[r*k+j];
      }
    V.set(W); orth(V);
  }
 
  AV.fill(0);
  for (let r = 0; r < h; r++)
    for (let c = 0; c < w; c++) {
      const a = A[r*w+c];
      for (let j = 0; j < k; j++) AV[r*k+j] += a * V[c*k+j];
    }
  const B = new Float64Array(h * w);
  for (let r = 0; r < h; r++)
    for (let c = 0; c < w; c++) {
      let sum = 0;
      for (let j = 0; j < k; j++) sum += AV[r*k+j] * V[c*k+j];
      B[r*w+c] = sum;
    }
  return B;
}
 
function fxCompress(layer, k) {
  const w = layer.width, h = layer.height;
  const id = layer.getImageData(), d = id.data;
  const ch = [new Float64Array(h*w), new Float64Array(h*w), new Float64Array(h*w)];
  for (let i = 0, p = 0; i < d.length; i += 4, p++) {
    ch[0][p] = d[i]; ch[1][p] = d[i+1]; ch[2][p] = d[i+2];
  }
  const out = ch.map(A => rankKApprox(A, h, w, k));
  for (let i = 0, p = 0; i < d.length; i += 4, p++) {
    d[i]   = out[0][p];
    d[i+1] = out[1][p];
    d[i+2] = out[2][p];
  }
  layer.putImageData(id);
}
 
const FX = {
  color:     fxColor,
  sepia:     fxSepia,
  gaussian:  fxGaussianBlur,
  median:    fxMedianBlur,
  sobel:     fxSobelEdge,
  grayscale: fxGrayscale,
  inversion: fxInversion,
  rotate:    fxColorRotation,
  box:       fxBoxBlur,
  pixelate:  fxPixelate,
  sharpen:   fxSharpen,
  compress:  fxCompress
};
 
// API ──────────────────────────────────────────────

function applyColorFilter(layer, relR, relG, relB, absR, absG, absB) {
  layer.addOp('color', [relR, relG, relB, absR, absG, absB],
    'color adjustment',
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

function applyGrayscale(layer, v) {
  layer.addOp('grayscale', [v], `Grayscale (${Math.round(v*100)}%)`,
    'Rec.709 luma blended by strength');
}

function applyInversion(layer, v) {
  layer.addOp('inversion', [v], `Inversion (${Math.round(v*100)}%)`,
    'Per-channel 255 − value, blended by strength');
}

function applyColorRotation(layer, rotation) {
  layer.addOp('rotate', [rotation], `Color rotation (${rotation})`,
    'R/G/B channel permutation');
}

function applyBoxBlur(layer, r) {
  layer.addOp('box', [r], `Box blur (r = ${r})`,
    `Uniform (2r+1)² = ${(2*r+1)**2}-pixel average`);
}

function applyPixelate(layer, v) {
  layer.addOp('pixelate', [v], `Pixelate (${v})`,
    'Downscale then nearest-neighbour upscale');
}

function applyCompress(layer, k) {
  layer.addOp('compress', [k], `Compress (rank ${k})`,
    'Keeps the top-k singular components: A ≈ UₖΣₖVₖᵀ per channel');
}

function applySharpen(layer, v) {
  layer.addOp('sharpen', [v], `Sharpen (${v})`,
    'Unsharp mask: img·(v+1) − blur·v');
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