'use strict';

// Add more colour if anyone asks for more

const CAT_PALETTE = [
  '#e05555', '#4a90d9', '#50b86c', '#e09c30',
  '#9b59b6', '#e07030', '#2ebdbd', '#c0396b',
  '#7f8c8d', '#16a085',
];

const POINT_SIZE   = 0.07;
const VIEW_SPREAD  = 4.0;
const STD_SCALE    = 2.0;

const DATA = {
  headers:    [],
  rows:       [],
  numericIdx: [],

  pts:        [],
  cats:       null,
  catColors:  null,
  sel:        null,

  cloud:      null,
  fitLine:    null,
  svd:        null,
};

//  CSV Pasing ────────────────────────────────────────────── 

function parseCSV(text) {
  const rows = [];
  let row = [], field = '', inQuotes = false;
  text = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (inQuotes) {
      if (ch === '"') {
        if (text[i+1] === '"') { field += '"'; i++; }
        else inQuotes = false;
      } else field += ch;
    } else if (ch === '"') {
      inQuotes = true;
    } else if (ch === ',') {
      row.push(field); field = '';
    } else if (ch === '\n') {
      row.push(field); rows.push(row); row = []; field = '';
    } else field += ch;
  }
  if (field.length || row.length) { row.push(field); rows.push(row); }
  // drop fully-empty trailing rows
  return rows.filter(r => r.some(c => c.trim() !== ''));
}

function isNumericColumn(rows, col) {
  let seen = 0;
  for (const r of rows) {
    const v = (r[col] ?? '').trim();
    if (v === '') continue;
    seen++;
    if (!isFinite(parseFloat(v))) return false;
  }
  return seen > 0;
}

// Data processing by z score or just to fit in the grid ────────────────────────────────────────────── 

function preprocess(raw, standardise) {
  const n = raw.length;
  const mean = [0,0,0];
  for (const p of raw) for (let k = 0; k < 3; k++) mean[k] += p[k] / n;
  const cen = raw.map(p => [p[0]-mean[0], p[1]-mean[1], p[2]-mean[2]]);

  if (standardise) {
    const std = [0,0,0];
    for (const p of cen) for (let k = 0; k < 3; k++) std[k] += p[k]*p[k] / n;
    for (let k = 0; k < 3; k++) std[k] = Math.sqrt(std[k]) || 1;
    return cen.map(p => [p[0]/std[0], p[1]/std[1], p[2]/std[2]]);
  }
  
  let maxAbs = 0;
  for (const p of cen) for (let k = 0; k < 3; k++) maxAbs = Math.max(maxAbs, Math.abs(p[k]));
  const f = maxAbs ? VIEW_SPREAD / maxAbs : 1;
  return cen.map(p => [p[0]*f, p[1]*f, p[2]*f]);
}

function covariance() {
  const n = DATA.pts.length;
  const C = new Array(9).fill(0);
  for (const p of DATA.pts) {
    C[0]+=p[0]*p[0]; C[1]+=p[0]*p[1]; C[2]+=p[0]*p[2];
    C[4]+=p[1]*p[1]; C[5]+=p[1]*p[2]; C[8]+=p[2]*p[2];
  }
  const d = Math.max(1, n - 1);
  C[0]/=d; C[1]/=d; C[2]/=d; C[4]/=d; C[5]/=d; C[8]/=d;
  C[3]=C[1]; C[6]=C[2]; C[7]=C[5];
  return C;
}