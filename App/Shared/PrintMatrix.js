'use strict';

function formatMatrix(rows, acc = 3) {
  const strs = rows.map(r => r.map(v => (v >= 0 ? '+' : '-') + Math.abs(v).toFixed(acc)));
  const w = Math.max(0, ...strs.flat().map(s => s.length));
  return strs.map(r => r.map(s => s.padStart(w)));
}

function displayAsMatrix(rows, augcol = 0) {
  return rows.map(line => {
    let s = '[', j = 0;
    for (const entry of line) {
      s += entry; j++;
      s += j < line.length ? (j + augcol === line.length ? ' | ' : ' ') : ']';
    }
    return s;
  }).join('\n');
}

function displayAsBasis(rows) {
  const out = [];
  for (let i = 0; i < rows[0].length; i++) {
    let s = '[';
    for (let j = 0; j < rows.length; j++)
      s += rows[j][i] + (j < rows.length - 1 ? '] [' : ']');
    out.push(s);
  }
  return out.join('\n');
}

function concat(mats) {
  const n = mats[0].length;
  for (const m of mats)
    if (m.length !== n || m[0].length !== n)
      return 'Error: This operation only works on square matrices of the same size';
  const lines = [];
  for (let i = 0; i < n; i++)
    lines.push(mats.map(m => m[i].join(' ')).join('   '));
  return lines.join('\n');
}

function printMatrix(rows, acc = 3, augcol = 0) {
  return displayAsMatrix(formatMatrix(rows, acc), augcol);
}