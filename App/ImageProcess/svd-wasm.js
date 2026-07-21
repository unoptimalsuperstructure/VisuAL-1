'use strict';

let svdk = null;

(function initSVDKernel() {
  if (typeof WebAssembly === 'undefined' || typeof fetch === 'undefined') return;
  fetch('./WASM-Files/svd-kernel.wasm')
    .then(res => {
      if (!res.ok) throw new Error('http ' + res.status);
      return WebAssembly.instantiateStreaming(res.clone(), {})
        .catch(() => res.arrayBuffer().then(b => WebAssembly.instantiate(b, {})));
    })
    .then(r => { svdk = r.instance.exports; })
    .catch(() => { svdk = null; });
})();

function svdWasmRankK(A, h, w, k, iters, V, orth) {
  if (!svdk) return null;
  try {
    const aP = 0, vP = h * w, avP = vP + w * k, wP = avP + h * k, bP = wP + w * k;
    const need = (bP + h * w) * 8;
    const mem = svdk.mem;
    if (mem.buffer.byteLength < need)
      mem.grow(Math.ceil((need - mem.buffer.byteLength) / 65536));
    const F = new Float64Array(mem.buffer);
    F.set(A, aP);
    F.set(V, vP);
    for (let it = 0; it < iters; it++) {
      svdk.av(aP * 8, vP * 8, avP * 8, h, w, k);
      svdk.atav(aP * 8, avP * 8, wP * 8, h, w, k);
      const Wv = F.slice(wP, wP + w * k);
      orth(Wv);
      F.set(Wv, vP);
    }
    svdk.av(aP * 8, vP * 8, avP * 8, h, w, k);  
    svdk.project(aP * 8, vP * 8, avP * 8, bP * 8, h, w, k);
    return F.slice(bP, bP + h * w);
  } catch (_) {
    return null;
  }
}