'use strict';

function escapeHTML(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

const TIP_DELAY_MS = 200;

let tipEl = null;
let tipTimer = null;
let tipTarget = null;

function tipBubble() {
  if (tipEl) return tipEl;
  tipEl = document.createElement('div');
  tipEl.className = 'tooltip-bubble';
  tipEl.id = 'shared-tooltip';
  tipEl.setAttribute('role', 'tooltip');
  tipEl.style.display = 'none';
  document.body.appendChild(tipEl);
  return tipEl;
}

function showTip(target) {
  const text = target.getAttribute('data-tip');
  if (!text) return;
  const el = tipBubble();
  el.textContent = text;
  el.style.display = 'block';
  el.style.visibility = 'hidden';
  el.style.left = '0px'; el.style.top = '0px';

  const r = target.getBoundingClientRect();
  const b = el.getBoundingClientRect();
  const margin = 8;

  let left = r.left + r.width / 2 - b.width / 2;
  left = Math.max(margin, Math.min(left, window.innerWidth - b.width - margin));

  let top = r.top - b.height - margin;
  el.classList.toggle('below', top < margin);
  if (top < margin) top = r.bottom + margin;

  el.style.left = left + 'px';
  el.style.top = top + 'px';
  el.style.visibility = 'visible';

  tipTarget = target;
  target.setAttribute('aria-describedby', 'shared-tooltip');
}

function hideTip() {
  clearTimeout(tipTimer);
  tipTimer = null;
  if (tipEl) tipEl.style.display = 'none';
  if (tipTarget) { tipTarget.removeAttribute('aria-describedby'); tipTarget = null; }
}

document.addEventListener('mouseover', e => {
  const t = e.target.closest?.('[data-tip]');
  if (!t || t === tipTarget) return;
  hideTip();
  tipTimer = setTimeout(() => showTip(t), TIP_DELAY_MS);
});

document.addEventListener('mouseout', e => {
  const t = e.target.closest?.('[data-tip]');
  if (t && (!e.relatedTarget || !t.contains(e.relatedTarget))) hideTip();
});

document.addEventListener('focusin', e => {
  const t = e.target.closest?.('[data-tip]');
  if (t) { hideTip(); showTip(t); }
});

document.addEventListener('focusout', hideTip);
document.addEventListener('keydown', e => { if (e.key === 'Escape') hideTip(); });
window.addEventListener('scroll', hideTip, true);