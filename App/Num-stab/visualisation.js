'use strict';

const NSVIZ = { yaw: 0.55, pitch: 0.35, wired: false, wheelWired: false, zoomK: 1 };
const NSVIZ_COLORS = ['#d6455c', '#2f9e44', '#3b7dd8'];

function nsVizDiffRow(prev, cur) {
  for (let r = 0; r < cur.length; r++)
    for (let c = 0; c < cur[r].length; c++)
      if (Math.abs(prev[r][c] - cur[r][c]) > 1e-15) return r;
  return -1;
}

const nsVizTo3 = v => [v[0] ?? 0, v[1] ?? 0, v[2] ?? 0];

function nsVizProject(p, W, H, zoom, is3d) {
  return is3d
    ? orthoProject(p, NSVIZ.yaw, NSVIZ.pitch, W, H, zoom)
    : [W / 2 + p[0] * zoom, H / 2 - p[1] * zoom, 0];
}

function nsVizArrow(g, a, b, color, width, dash) {
  g.strokeStyle = color; g.lineWidth = width;
  g.setLineDash(dash || []);
  g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke();
  const ang = Math.atan2(b[1] - a[1], b[0] - a[0]);
  const hl = 4 + 1.6 * width;
  g.setLineDash([]);
  g.beginPath();
  g.moveTo(b[0], b[1]);
  g.lineTo(b[0] - hl * Math.cos(ang - 0.42), b[1] - hl * Math.sin(ang - 0.42));
  g.moveTo(b[0], b[1]);
  g.lineTo(b[0] - hl * Math.cos(ang + 0.42), b[1] - hl * Math.sin(ang + 0.42));
  g.stroke();
}

function nsVizRender() {
  const cv = document.getElementById('ns-viz');
  const note = document.getElementById('ns-viz-note');
  if (!cv || !note) return;

  const isGS = NS.hist.length > 0 && NS.asMatrix === false;
  const V0 = NS.gsVectors || NS.matrix;
  const cols = V0 ? V0[0].length : 0;
  const rows = V0 ? V0.length : 0;
  const drawable = isGS && (cols === 2 || cols === 3) && rows <= 3;

  cv.style.display = drawable ? 'block' : 'none';
  note.style.display = isGS && !drawable ? 'block' : 'none';
  if (isGS && !drawable)
    note.textContent = 'Vector picture available for 2-D or 3-D vectors (a matrix with 2–3 columns and up to 3 rows).';
  if (!drawable) return;

  const is3d = cols === 3;
  const dpr = window.devicePixelRatio || 1;
  const W = cv.width = cv.clientWidth * dpr;
  const H = cv.height = cv.clientHeight * dpr;
  const g = cv.getContext('2d');
  g.clearRect(0, 0, W, H);

  const cur = NS.hist[NS.page].m;
  const prev = NS.page > 0 ? NS.hist[NS.page - 1].m : null;

  let maxN = 1;
  for (const m of [V0, cur, prev].filter(Boolean))
    for (const row of m) maxN = Math.max(maxN, Math.hypot(...row));
  const zoom = NSVIZ.zoomK * 0.42 * Math.min(W, H) / maxN;
  const P = p => nsVizProject(nsVizTo3(p), W, H, zoom, is3d);
  const O = P([0, 0, 0]);

  const muted = getComputedStyle(document.body).getPropertyValue('--muted') || '#999';

  g.globalAlpha = 0.45;
  const axes = is3d
    ? [[[maxN, 0, 0], 'x'], [[0, maxN, 0], 'y'], [[0, 0, maxN], 'z']]
    : [[[maxN, 0, 0], 'x'], [[0, maxN, 0], 'y']];
  g.font = `${10 * dpr}px sans-serif`; g.textAlign = 'center';
  for (const [d, name] of axes) {
    const a = P(d.map(v => -v)), b = P(d);
    g.strokeStyle = muted; g.lineWidth = dpr * 0.7; g.setLineDash([]);
    g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke();
    g.fillStyle = muted; g.fillText(name, b[0], b[1] - 4 * dpr);
  }

  g.strokeStyle = muted; g.lineWidth = dpr * 0.7;
  const rings = is3d ? [[0, 1], [0, 2], [1, 2]] : [[0, 1]];
  for (const pl of rings) {
    g.beginPath();
    for (let a = 0; a <= 48; a++) {
      const t = (a / 48) * Math.PI * 2;
      const u = [0, 0, 0];
      u[pl[0]] = Math.cos(t); u[pl[1]] = Math.sin(t);
      const q = nsVizProject(u, W, H, zoom, is3d);
      a === 0 ? g.moveTo(q[0], q[1]) : g.lineTo(q[0], q[1]);
    }
    g.stroke();
  }
  g.globalAlpha = 1;

  g.font = `${11 * dpr}px sans-serif`;
  V0.forEach((row, i) => {
    const tip = P(row);
    nsVizArrow(g, O, tip, muted, dpr * 1.1);
    g.fillStyle = muted;
    g.fillText('v' + (i + 1), tip[0] + 10 * dpr, tip[1] - 4 * dpr);
  });

  const changed = prev ? nsVizDiffRow(prev, cur) : -1;
  if (changed >= 0) {
    const before = P(prev[changed]), after = P(cur[changed]);
    nsVizArrow(g, O, before, NSVIZ_COLORS[changed] + '66', dpr * 1.4, [5 * dpr, 4 * dpr]);
    nsVizArrow(g, after, before, '#996fd6', dpr * 1.4, [3 * dpr, 3 * dpr]);
    const mid = [(after[0] + before[0]) / 2, (after[1] + before[1]) / 2];
    g.fillStyle = '#996fd6';
    g.fillText('proj', mid[0] + 8 * dpr, mid[1]);
  }

  cur.forEach((row, i) => {
    if (Math.hypot(...row) < 1e-12) return;
    const tip = P(row);
    nsVizArrow(g, O, tip, NSVIZ_COLORS[i] || '#333', dpr * 2);
    g.fillStyle = NSVIZ_COLORS[i] || '#333';
    g.fillText('u' + (i + 1), tip[0] + 10 * dpr, tip[1] + 10 * dpr);
  });

  g.fillStyle = muted; g.textAlign = 'left';
  g.fillText(is3d ? 'drag to orbit · scroll to zoom' : 'scroll to zoom',
             8 * dpr, H - 8 * dpr);
  if (is3d && !NSVIZ.wired) { NSVIZ.wired = true; attachOrbit(cv, NSVIZ, nsVizRender); }
  if (!NSVIZ.wheelWired) {
    NSVIZ.wheelWired = true;
    cv.addEventListener('wheel', e => {
      e.preventDefault();
      NSVIZ.zoomK = Math.min(8, Math.max(0.3,
        NSVIZ.zoomK * (e.deltaY < 0 ? 1.15 : 1 / 1.15)));
      nsVizRender();
    }, { passive: false });
  }
}

window.addEventListener('resize', () => nsVizRender());