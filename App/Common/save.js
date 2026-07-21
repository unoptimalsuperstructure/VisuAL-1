'use strict';

let TS = null;

function tsMsg(text, isErr) {
  const el = document.getElementById('ts-msg');
  if (!el) return;
  el.textContent = text || '';
  el.style.color = isErr ? '#d6455c' : 'var(--muted)';
}

async function tsOpen() {
  const { error } = await apiSession();
  const modal = document.getElementById('ts-modal');
  modal.style.display = 'flex';
  const rowEl = document.getElementById('ts-saverow');
  const listEl = document.getElementById('ts-list');
  document.getElementById('ts-url').style.display = 'none';
  if (error) {
    rowEl.style.display = 'none';
    listEl.textContent = '';
    const note = document.createElement('div');
    note.className = 'ts-note';
    note.textContent = 'Saving and share links are available once you\u2019re ' +
      'logged in. Every tool works without an account \u2014 an account only ' +
      'adds the ability to keep and share your work.';
    const go = document.createElement('a');
    go.className = 'btn primary ts-login';
    go.href = '../Login/login.html';
    go.textContent = 'Log in / sign up';
    listEl.append(note, go);
    tsMsg('');
    return;
  }
  rowEl.style.display = '';
  tsMsg('');
  tsRefreshList();
}

async function tsRefreshList() {
  const listEl = document.getElementById('ts-list');
  listEl.textContent = 'Loading…';
  const { data, error } = await listSaves(TS.tool);
  if (error) { listEl.textContent = ''; tsMsg(error, true); return; }
  listEl.textContent = '';
  if (!data.length) { listEl.textContent = 'No saves yet.'; return; }

  for (const row of data) {
    const item = document.createElement('div');
    item.className = 'ts-item';

    const name = document.createElement('span');
    name.className = 'ts-name';
    name.textContent = row.name;
    name.title = new Date(row.updated_at).toLocaleString();
    item.appendChild(name);

    const mk = (label, fn, danger) => {
      const b = document.createElement('button');
      b.className = 'btn ts-btn' + (danger ? ' danger' : '');
      b.textContent = label;
      b.addEventListener('click', fn);
      item.appendChild(b);
    };
    mk('Load', async () => {
      const got = await loadSave(row.id);
      if (got.error) return tsMsg(got.error, true);
      const bad = await TS.restore(got.data.payload);
      if (bad) return tsMsg(bad, true);
      tsMsg(`Loaded "${row.name}".`);
      document.getElementById('ts-modal').style.display = 'none';
    });
    mk('Share snapshot', async () =>
      tsShareResult(await createShareFromSave(row.id, row.name, false)));
    mk('Share live', async () =>
      tsShareResult(await createShareFromSave(row.id, row.name, true)));
    mk('Delete', async () => {
      const r = await deleteSave(row.id);
      if (r.error) return tsMsg(r.error, true);
      tsRefreshList();
    }, true);

    listEl.appendChild(item);
  }
}

function tsShareResult(r) {
  if (r.error) return tsMsg(r.error, true);
  const out = document.getElementById('ts-url');
  out.style.display = 'block';
  out.value = r.data.url;
  out.select();
  try { navigator.clipboard?.writeText(r.data.url); } catch (_) {}
  tsMsg('Share link created and copied — anyone with it can view ' +
        (r.data.save_id ? '(live: it follows this save).' : '(frozen snapshot).'));
}

async function tsSaveCurrent() {
  const nameEl = document.getElementById('ts-name');
  const name = nameEl.value.trim();
  if (!name) return tsMsg('Give the save a name first.', true);
  const emptyWhy = TS.empty ? TS.empty() : false;
  if (emptyWhy) return tsMsg(typeof emptyWhy === 'string'
      ? emptyWhy : 'Nothing to save yet.', true);
  const { data, error } = await saveTool(TS.tool, name, TS.serialize());
  if (error) return tsMsg(error, true);
  nameEl.value = '';
  tsMsg(`Saved "${data.name}".`);
  tsRefreshList();
}

function tsBuildUI() {
  const bar = document.getElementById('topbar');
  if (bar && !document.getElementById('btn-toolsave')) {
    const b = document.createElement('button');
    b.id = 'btn-toolsave';
    b.className = 'theme-btn';
    b.textContent = '💾 Save';
    b.title = 'Saves & sharing';
    b.setAttribute('aria-label', 'Open saves and sharing');
    b.addEventListener('click', tsOpen);
    const anchor = document.getElementById('auth-slot');
    if (anchor) bar.insertBefore(b, anchor);
    else bar.appendChild(b);
    const setState = signedIn => { b.style.opacity = signedIn ? '' : '0.6'; };
    if (typeof sb !== 'undefined' && sb) {
      authSession().then(s => setState(!!s));
      sb.auth.onAuthStateChange((_ev, session) => setState(!!session));
    } else setState(false);
  }

  // the modal, built once
  const bg = document.createElement('div');
  bg.className = 'modal-bg';
  bg.id = 'ts-modal';
  bg.style.display = 'none';
  bg.addEventListener('click', e => { if (e.target === bg) bg.style.display = 'none'; });

  const modal = document.createElement('div');
  modal.className = 'modal ts-modal';

  const h3 = document.createElement('h3');
  h3.textContent = 'Saves & sharing';

  const rowEl = document.createElement('div');
  rowEl.className = 'field-row';
  rowEl.id = 'ts-saverow';
  const lab = document.createElement('label');
  lab.textContent = 'name:';
  lab.style.cssText = 'width:auto;min-width:48px';
  const inp = document.createElement('input');
  inp.id = 'ts-name'; inp.type = 'text'; inp.placeholder = 'e.g. my work';
  const saveBtn = document.createElement('button');
  saveBtn.className = 'btn primary';
  saveBtn.textContent = 'Save current';
  saveBtn.style.cssText = 'width:auto;flex:none';
  saveBtn.addEventListener('click', tsSaveCurrent);
  rowEl.append(lab, inp, saveBtn);

  const list = document.createElement('div');
  list.className = 'ts-list'; list.id = 'ts-list';
  const url = document.createElement('input');
  url.className = 'ts-url'; url.id = 'ts-url';
  url.readOnly = true; url.style.display = 'none';
  const msg = document.createElement('div');
  msg.id = 'ts-msg';
  msg.style.cssText = 'font-size:11px;min-height:15px;margin-top:6px';

  const actions = document.createElement('div');
  actions.className = 'modal-actions';
  const close = document.createElement('button');
  close.className = 'btn';
  close.textContent = 'Close';
  close.addEventListener('click', () => { bg.style.display = 'none'; });
  actions.appendChild(close);

  modal.append(h3, rowEl, list, url, msg, actions);
  bg.appendChild(modal);
  document.body.appendChild(bg);
}

function initToolSave(cfg) {
  TS = cfg;
  if (document.readyState === 'loading')
    document.addEventListener('DOMContentLoaded', tsBuildUI);
  else
    tsBuildUI();
}