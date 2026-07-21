'use strict';

initToolSave({
  tool: 'numstab',
  serialise: () => ({ matrix: NS.matrix }),
  restore: p => {
    const m = p?.matrix;
    if (!Array.isArray(m) || !m.length || !Array.isArray(m[0]))
      return 'This save does not look like a matrix.';
    const w = m[0].length;
    if (m.some(r => !Array.isArray(r) || r.length !== w ||
                    r.some(v => !isFinite(+v))))
      return 'Saved matrix has invalid entries.';
    nsSetMatrix(m.map(r => r.map(Number)));
    return null;
  },
  empty: () => NS.matrix ? false : 'Import or generate a matrix first.',
});