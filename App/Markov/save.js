'use strict';

function serialiseMarkov() {
  return {
    mode: state.mode,
    nodes: state.nodes.map(n => ({ id: n.id, label: n.label, x: n.x, y: n.y, color: n.color })),
    edges: state.edges.map(e => ({ from: e.from, to: e.to, weight: e.weight })),
    initialDist: state.prob ? Array.from(state.prob) : null,
  };
}

function restoreMarkov(p) {
  if (!p || !Array.isArray(p.nodes) || !Array.isArray(p.edges))
    return 'This save does not look like a Markov chain.';
  state.nodes = p.nodes.map(n => ({ id: +n.id, label: String(n.label ?? '?'),
    x: +n.x || 0, y: +n.y || 0,
    color: /^#[0-9a-fA-F]{3,8}$/.test(n.color ?? '') ? n.color
           : COLORS[(+n.id - 1) % COLORS.length] }));
  state.edges = p.edges
    .filter(e => state.nodes.some(n => n.id === +e.from) &&
                 state.nodes.some(n => n.id === +e.to))
    .map(e => ({ from: +e.from, to: +e.to, weight: Math.max(0, +e.weight || 0) }));
  nodeIdCtr = state.nodes.reduce((m, n) => Math.max(m, n.id), 0);

  const mode = p.mode === 'ctmc' ? 'ctmc' : 'dtmc';
  state.mode = mode;
  document.getElementById('btn-chain-dtmc')?.classList.toggle('active', mode === 'dtmc');
  document.getElementById('btn-chain-ctmc')?.classList.toggle('active', mode === 'ctmc');

  simReset();
  const n = state.nodes.length;
  if (Array.isArray(p.initialDist) && p.initialDist.length === n && n > 0) {
    let v = p.initialDist.map(x => Math.max(0, +x || 0));
    const sum = v.reduce((a, b) => a + b, 0);
    if (sum > 1e-12) {
      state.prob = Float64Array.from(v.map(x => x / sum));
      state.history = [state.prob.slice()];
      state.histFull = [{ t: 0, p: Array.from(state.prob) }];
    }
  }
  renderSidebar();
  renderMatrixPanel();
  renderDistPanel();
  updateStepBadge();
  render();
  return null;
}

initToolSave({
  tool: 'markov',
  serialise: serialiseMarkov,
  restore: restoreMarkov,
  empty: () => state.nodes.length ? false : 'The canvas is empty — add some states first.',
});