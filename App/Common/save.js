'use strict';

let TS = null;

let tsActiveSaveId = null;
let tsLiveSaveIds = new Set();
let tsWatch = null, tsLastFp = null, tsLastPush = 0, tsFails = 0;

function tsSetActive(id) { tsActiveSaveId = id; tsSyncWatch(); }

async function tsLoadLiveSet() {
  const { data } = await listShares();
  tsLiveSaveIds = new Set((data || [])
    .filter(r => r.save_id && r.tool === TS.tool)
    .map(r => r.save_id));
  tsSyncWatch();
}

function tsSyncWatch() {
  const want = tsActiveSaveId && tsLiveSaveIds.has(tsActiveSaveId);
  if (want && !tsWatch) {
    tsLastFp = null; tsFails = 0;
    tsWatch = setInterval(tsAutoPush, 4000);
  } else if (!want && tsWatch) {
    clearInterval(tsWatch); tsWatch = null;
  }
}

async function tsAutoPush() {
  try {
    if (TS.empty && TS.empty()) return;
    const fp = TS.fingerprint ? TS.fingerprint()
                              : JSON.stringify(TS.serialise());
    if (fp === tsLastFp) return;
    if (Date.now() - tsLastPush < 8000) return;
    const r = await updateSave(tsActiveSaveId, { payload: TS.serialise() });
    if (r.error) {
      if (++tsFails >= 3) {
        clearInterval(tsWatch); tsWatch = null;
        console.warn('Live sync stopped:', r.error);
      }
      return;
    }
    tsFails = 0; tsLastFp = fp; tsLastPush = Date.now();
  } catch (_) {}
}

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
  const heads = document.querySelectorAll('.ts-sect');
  if (error) {
    rowEl.style.display = 'none';
    heads.forEach(h => { h.style.display = 'none'; });
    const ex = document.querySelector('.ts-exprow');
    if (ex) ex.style.display = 'none';
    document.getElementById('ts-share-list').textContent = '';
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
  heads.forEach(h => { h.style.display = ''; });
  const exRow = document.querySelector('.ts-exprow');
  if (exRow) exRow.style.display = '';
  tsMsg('');
  tsRefreshList();
  tsRefreshShares();
  tsLoadLiveSet();
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
      tsSetActive(row.id);
      tsMsg(`Loaded "${row.name}".`);
      document.getElementById('ts-modal').style.display = 'none';
    });
    mk('Update', async () => {
      const why = TS.empty ? TS.empty() : false;
      if (why) return tsMsg(typeof why === 'string' ? why : 'Nothing to save yet.', true);
      const r = await updateSave(row.id, { payload: TS.serialise() });
      if (r.error) return tsMsg(r.error, true);
      tsSetActive(row.id);
      tsMsg(`Updated "${row.name}" with the current state — live links now show it.`);
      tsRefreshList();
    });
    mk('Share snapshot', async () =>
      tsShareResult(await createShareFromSave(row.id, row.name, false, tsExpiry())));
    mk('Share live', async () =>
      tsShareResult(await createShareFromSave(row.id, row.name, true, tsExpiry())));
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
        (r.data.save_id ? '(live: it follows this save — and your edits now sync to it automatically).' : '(frozen snapshot).'));
  tsRefreshShares();
  tsLoadLiveSet();
}

function tsExpiry() {
  const v = document.getElementById('ts-exp')?.value || '7';
  if (v === 'never') return 'never';
  if (v === '30') return new Date(Date.now() + 30 * 864e5).toISOString();
  return null;
}

async function tsRefreshShares() {
  const listEl = document.getElementById('ts-share-list');
  if (!listEl) return;
  const { data, error } = await listShares();
  if (error) { listEl.textContent = ''; return tsMsg(error, true); }
  const mine = data.filter(r => r.tool === TS.tool);
  listEl.textContent = '';
  if (!mine.length) { listEl.textContent = 'No share links yet.'; return; }

  for (const row of mine) {
    const item = document.createElement('div');
    item.className = 'ts-item';

    const name = document.createElement('span');
    name.className = 'ts-name';
    name.textContent = row.title || '(untitled)';
    name.title = 'created ' + new Date(row.created_at).toLocaleString() +
      (row.expires_at ? ' · expires ' + new Date(row.expires_at).toLocaleString() : '');
    item.appendChild(name);

    if (row.save_id) {
      const b = document.createElement('span');
      b.className = 'ts-live';
      b.textContent = 'live';
      item.appendChild(b);
    }
    const exp = document.createElement('span');
    exp.className = 'ts-exp-tag';
    if (row.expires_at) {
      const days = Math.max(0, Math.ceil((new Date(row.expires_at) - Date.now()) / 864e5));
      exp.textContent = days + 'd';
      exp.title = 'Expires ' + new Date(row.expires_at).toLocaleString() +
                  ' — each visit extends it by 7 days.';
    } else {
      exp.textContent = '\u221e';
      exp.title = 'Never expires.';
    }
    item.appendChild(exp);

    const mk = (label, fn, danger) => {
      const b = document.createElement('button');
      b.className = 'btn ts-btn' + (danger ? ' danger' : '');
      b.textContent = label;
      b.addEventListener('click', fn);
      item.appendChild(b);
    };
    mk('Copy link', () => {
      const out = document.getElementById('ts-url');
      out.style.display = 'block';
      out.value = row.url;
      out.select();
      try { navigator.clipboard?.writeText(row.url); } catch (_) {}
      tsMsg('Link copied.');
    });
    mk('Delete', async () => {
      const r = await deleteShare(row.token);
      if (r.error) return tsMsg(r.error, true);
      tsMsg('Share link deleted — the URL no longer works.');
      tsRefreshShares();
      tsLoadLiveSet();
    }, true);

    listEl.appendChild(item);
  }
}

async function tsSaveCurrent() {
  const nameEl = document.getElementById('ts-name');
  const name = nameEl.value.trim();
  if (!name) return tsMsg('Give the save a name first.', true);
  const emptyWhy = TS.empty ? TS.empty() : false;
  if (emptyWhy) return tsMsg(typeof emptyWhy === 'string'
      ? emptyWhy : 'Nothing to save yet.', true);
  const { data, error } = await saveTool(TS.tool, name, TS.serialise());
  if (error) return tsMsg(error, true);
  nameEl.value = '';
  tsSetActive(data.id);
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

  const savesHead = document.createElement('div');
  savesHead.className = 'ts-sect'; savesHead.textContent = 'Saves';
  const list = document.createElement('div');
  list.className = 'ts-list'; list.id = 'ts-list';
  const sharesHead = document.createElement('div');
  sharesHead.className = 'ts-sect'; sharesHead.textContent = 'Share links';
  const expRow = document.createElement('div');
  expRow.className = 'ts-exprow';
  const expLab = document.createElement('label');
  expLab.textContent = 'New links expire:';
  const expSel = document.createElement('select');
  expSel.id = 'ts-exp';
  for (const [val, label] of [['7', '7 days after the last visit'],
                              ['30', '30 days after the last visit'],
                              ['never', 'never']]) {
    const o = document.createElement('option');
    o.value = val; o.textContent = label;
    expSel.appendChild(o);
  }
  expRow.append(expLab, expSel);
  const shareList = document.createElement('div');
  shareList.className = 'ts-list'; shareList.id = 'ts-share-list';
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

  modal.append(h3, rowEl, savesHead, list, sharesHead, expRow, shareList,
               url, msg, actions);
  bg.appendChild(modal);
  document.body.appendChild(bg);
}

const TOOL_LABELS = { markov: 'Markov chain', data: 'dataset',
                      '3d': '3D scene', image: 'image project',
                      numstab: 'matrix' };

function tsBanner() {
  let el = document.getElementById('ts-banner');
  if (el) { el.textContent = ''; return el; }
  el = document.createElement('div');
  el.id = 'ts-banner';
  el.className = 'ts-banner';
  const bar = document.getElementById('topbar');
  if (bar && bar.parentNode) bar.parentNode.insertBefore(el, bar.nextSibling);
  else document.body.insertBefore(el, document.body.firstChild);
  return el;
}

function tsBannerError(text) {
  const el = tsBanner();
  el.classList.add('ts-banner-err');
  el.appendChild(document.createTextNode(text));
}

function tsBannerOk(data, token) {
  const el = tsBanner();
  el.classList.remove('ts-banner-err');

  const tag = document.createElement('span');
  tag.className = 'ts-banner-tag';
  tag.textContent = 'Shared';
  el.appendChild(tag);

  const title = document.createElement('strong');
  title.textContent = data.title || TOOL_LABELS[data.tool] || 'shared work';
  el.appendChild(title);

  if (data.save_id) {
    const live = document.createElement('span');
    live.className = 'ts-live';
    live.textContent = 'live';
    el.appendChild(live);
  }

  const note = document.createElement('span');
  note.className = 'ts-banner-note';
  note.textContent = data.save_id
    ? 'Follows the owner\u2019s saved copy. Explore freely \u2014 your changes stay on this screen.'
    : 'A snapshot. Explore freely \u2014 your changes stay on this screen.';
  el.appendChild(note);

  if (data.save_id) {
    const refresh = document.createElement('button');
    refresh.className = 'btn ts-btn';
    refresh.textContent = 'Get latest';
    refresh.addEventListener('click', () => tsLoadShare(token, true));
    el.appendChild(refresh);
  }

  const blank = document.createElement('a');
  blank.className = 'btn ts-btn';
  blank.href = location.pathname;
  blank.textContent = 'Start my own';
  el.appendChild(blank);
}

async function tsLoadShare(token, quiet) {
  const { data, error } = await fetchShare(token);
  if (error) return tsBannerError('This shared link could not be opened: ' + error);
  if (data.tool !== TS.tool) {
    const page = TOOL_PAGES[data.tool];
    if (page)
      return location.replace(
        new URL('../' + page, location.href).href + '?share=' + token);
    return tsBannerError('This link is for a tool that no longer exists.');
  }
  const bad = await TS.restore(data.payload);
  if (bad) return tsBannerError('This shared link could not be opened: ' + bad);
  tsBannerOk(data, token);
  if (quiet) {
    const el = document.getElementById('ts-banner');
    el.classList.add('ts-banner-flash');
    setTimeout(() => el.classList.remove('ts-banner-flash'), 700);
  }
}

function tsShareInit() {
  const token = new URLSearchParams(location.search).get('share');
  if (token) tsLoadShare(token, false);
}

function initToolSave(cfg) {
  TS = cfg;
  if (!TS.serialize && TS.serialise) TS.serialize = TS.serialise;
  if (!TS.fingerprint && TS.fingerPrint) TS.fingerprint = TS.fingerPrint;
  if (typeof TS.serialize !== 'function' || typeof TS.restore !== 'function')
    console.error('initToolSave: needs both a serialize (or serialise) and a ' +
                  'restore function — saving will not work for tool "' +
                  TS.tool + '".');
  const boot = () => { tsBuildUI(); tsShareInit(); };
  if (document.readyState === 'loading')
    document.addEventListener('DOMContentLoaded', boot);
  else
    boot();
}