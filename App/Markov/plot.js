'use strict';

function renderPlot() {
  const canvas = document.getElementById('mk-plot-canvas');
  if (!canvas) return;

  const ctx  = canvas.getContext('2d');
  const dpr  = window.devicePixelRatio || 1;

  const cssW = 240, cssH = 150;
  canvas.style.width  = cssW + 'px';
  canvas.style.height = cssH + 'px';
  if (canvas.width !== cssW * dpr || canvas.height !== cssH * dpr) {
    canvas.width  = cssW * dpr;
    canvas.height = cssH * dpr;
  }
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, cssW, cssH);

  const placeholder = msg => {
    ctx.fillStyle    = '#666';
    ctx.textAlign    = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(msg, cssW / 2, cssH / 2);
  };

  if (!state.nodes.length) return placeholder('No nodes yet');
  if (!state.prob)         return placeholder('Set a distribution to plot');

  const curStep = Number.isInteger(state.step) ? state.step : 0;
  let data, firstStep;

  if (Array.isArray(state.fullHistory) && state.fullHistory.length) {
    data      = state.fullHistory.slice(0, curStep + 1);
    firstStep = 0;
  } else if (Array.isArray(state.history) && state.history.length) {
    data      = state.history;
    firstStep = curStep - (data.length - 1);
  } else if (state.prob) {
    data      = [state.prob];
    firstStep = curStep;
  } else {
    return placeholder('Step forward to plot');
  }
  if (!data.length || !data[0]) return placeholder('Step forward to plot');

  const padL = 24, padR = 8, padT = 8, padB = 16;
  const plotW = cssW - padL - padR;
  const plotH = cssH - padT - padB;
  const lastIdx  = data.length - 1;
  const lastStep = firstStep + lastIdx;
  const xAt = i => padL + (lastIdx === 0 ? plotW / 2 : (i / lastIdx) * plotW);
  const yAt = p => padT + (1 - p) * plotH;

  ctx.fillStyle    = '#000000';
  ctx.font         = '9px arial';
  ctx.textAlign    = 'right';
  ctx.textBaseline = 'middle';
  [0, 0.5, 1].forEach(p => {
    const y = yAt(p);
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth   = 1;
    ctx.beginPath();
    ctx.moveTo(padL, y);
    ctx.lineTo(cssW - padR, y);
    ctx.stroke();
    ctx.fillText(p.toFixed(1), padL - 4, y);
  });

  ctx.strokeStyle = '#000';
  ctx.lineWidth   = 1.25;
  ctx.beginPath();
  ctx.moveTo(padL, padT);
  ctx.lineTo(padL, padT + plotH);
  ctx.lineTo(cssW - padR, padT + plotH);
  ctx.stroke();

  ctx.fillStyle    = '#000';
  ctx.textBaseline = 'top';
  ctx.textAlign    = 'left';
  ctx.fillText(String(firstStep), padL, cssH - padB + 3);
  if (lastIdx > 0) {
    ctx.textAlign = 'right';
    ctx.fillText(String(lastStep), cssW - padR, cssH - padB + 3);
  }

  state.nodes.forEach((nd, i) => {
    ctx.strokeStyle = nd.color;
    ctx.lineWidth   = 2;
    ctx.beginPath();
    data.forEach((dist, idx) => {
      const x = xAt(idx), y = yAt(dist[i] ?? 0);
      if (idx === 0) ctx.moveTo(x, y);
      else           ctx.lineTo(x, y);
    });
    ctx.stroke();

    const lp = data[lastIdx][i] ?? 0;
    ctx.fillStyle = nd.color;
    ctx.beginPath();
    ctx.arc(xAt(lastIdx), yAt(lp), 3, 0, Math.PI * 2);
    ctx.fill();
  });
}