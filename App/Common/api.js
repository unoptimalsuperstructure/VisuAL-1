'use strict';

async function apiSession() {
  const s = await authSession();
  return s ? { session: s, error: null }
           : { session: null, error: 'Sign in to save your work.' };
}

const apiErr = e => (e && (e.message || String(e))) || null;

async function saveTool(tool, name, payload) {
  const { session, error } = await apiSession();
  if (error) return { data: null, error };
  const { data, error: e } = await sb.from('tool_saves')
    .insert({ user_id: session.user.id, tool, name, payload })
    .select('id, tool, name, created_at, updated_at')
    .single();
  return { data, error: apiErr(e) };
}

async function listSaves(tool) {
  const { session, error } = await apiSession();
  if (error) return { data: null, error };
  let q = sb.from('tool_saves')
    .select('id, tool, name, created_at, updated_at')
    .order('updated_at', { ascending: false });
  if (tool) q = q.eq('tool', tool);
  const { data, error: e } = await q;
  return { data, error: apiErr(e) };
}

async function loadSave(id) {
  const { error } = await apiSession();
  if (error) return { data: null, error };
  const { data, error: e } = await sb.from('tool_saves')
    .select('*').eq('id', id).single();
  return { data, error: apiErr(e) };
}

async function updateSave(id, fields) {
  const { error } = await apiSession();
  if (error) return { data: null, error };
  const { data, error: e } = await sb.from('tool_saves')
    .update(fields).eq('id', id)
    .select('id, tool, name, created_at, updated_at')
    .single();
  return { data, error: apiErr(e) };
}

async function deleteSave(id) {
  const { error } = await apiSession();
  if (error) return { data: null, error };
  const { error: e } = await sb.from('tool_saves').delete().eq('id', id);
  return { data: !e, error: apiErr(e) };
}

async function createShare(tool, title, payload, saveId = null, expiresAt = null) {
  const { session, error } = await apiSession();
  if (error) return { data: null, error };
  const row = { user_id: session.user.id, tool, title: title || '', payload,
                save_id: saveId };

  if (expiresAt === 'never') row.expires_at = null;
  else if (expiresAt) row.expires_at = expiresAt;
  const { data, error: e } = await sb.from('share_links')
    .insert(row)
    .select('token, tool, title, save_id, created_at')
    .single();
  if (e) return { data: null, error: apiErr(e) };
  return { data: { ...data, url: shareURL(data.token, data.tool) }, error: null };
}

async function createShareFromSave(saveId, title, live = false, expiresAt = null) {
  const got = await loadSave(saveId);
  if (got.error) return got;
  return createShare(got.data.tool, title ?? got.data.name, got.data.payload,
                     live ? saveId : null, expiresAt);
}

async function fetchShare(token) {
  const { data, error } = await sb.rpc('open_share', { p_token: token });
  if (!error) {
    const row = Array.isArray(data) ? data[0] : data;
    return row ? { data: row, error: null }
               : { data: null, error: 'This share link has expired or was deleted.' };
  }
  const { data: d2, error: e2 } = await sb.from('share_links')
    .select('token, tool, title, payload, save_id, created_at, expires_at')
    .eq('token', token).single();
  return { data: d2, error: e2 ? 'Unknown or deleted share link.' : null };
}

async function listShares() {
  const { session, error } = await apiSession();
  if (error) return { data: null, error };
  const { data, error: e } = await sb.from('share_links')
    .select('token, tool, title, save_id, created_at, expires_at')
    .eq('user_id', session.user.id)
    .order('created_at', { ascending: false });
  return { data: data?.map(r => ({ ...r, url: shareURL(r.token, r.tool) })), error: apiErr(e) };
}

async function deleteShare(token) {
  const { error } = await apiSession();
  if (error) return { data: null, error };
  const { error: e } = await sb.from('share_links').delete().eq('token', token);
  return { data: !e, error: apiErr(e) };
}

const TOOL_PAGES = {
  markov:  'Markov/markov.html',
  data:    'DataEngineering/data.html',
  '3d':    '3d/3d.html',
  image:   'ImageProcess/image.html',
  numstab: 'NumStability/numstab.html',
};

function shareURL(token, tool) {
  return new URL('../' + TOOL_PAGES[tool], location.href).href +
         '?share=' + token;
}