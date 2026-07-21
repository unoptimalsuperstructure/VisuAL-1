'use strict';

/* ═══════════════════════════════════════════════════════════════
   api.js — VisuAL-1 data layer, Supabase-only (no Django).

   Load order on any page that saves:
     supabase-js CDN → Shared/auth.js → Shared/api.js

   Every function returns { data, error } where error is a
   human-readable string or null — callers can show it directly.
   Ownership is enforced twice: user_id is set from the session here,
   and row-level security re-checks auth.uid() = user_id in Postgres,
   so even buggy client code cannot touch another user's rows.
   Quotas live in Postgres triggers (see supabase-schema.sql); when
   one fires, its message arrives through `error` below.

   Save payloads are INPUTS ONLY (process + original data) — tools
   re-render on load:
     markov  { mode, nodes, edges, initialDist }
     data    { rows, headers, sel }
     3d      { objects, matrixStacks, savedLP }
     image   { sources, steps }
     numstab { matrix }
   ═══════════════════════════════════════════════════════════════ */

async function apiSession() {
  if (!sb) return { session: null, error: 'Supabase is not configured.' };
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
    .select('id, tool, name, created_at, updated_at')   // no payloads in lists
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

async function updateSave(id, fields) {          // { name? , payload? }
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

// ── share links ───────────────────────────────────────────────────
// The payload is copied INTO the share row at creation, so a link is a
// frozen snapshot: editing the save afterwards never changes the link.

async function createShare(tool, title, payload, saveId = null, expiresAt = null) {
  const { session, error } = await apiSession();
  if (error) return { data: null, error };
  const row = { user_id: session.user.id, tool, title: title || '', payload,
                save_id: saveId };
  if (expiresAt) row.expires_at = expiresAt;
  const { data, error: e } = await sb.from('share_links')
    .insert(row)
    .select('token, tool, title, save_id, created_at')
    .single();
  if (e) return { data: null, error: apiErr(e) };
  return { data: { ...data, url: shareURL(data.token) }, error: null };
}

// live = false = frozen snapshot of the save as it is now.
// live = true  = the link follows the save: future edits appear at the same URL
async function createShareFromSave(saveId, title, live = false, expiresAt = null) {
  const got = await loadSave(saveId);
  if (got.error) return got;
  return createShare(got.data.tool, title ?? got.data.name, got.data.payload,
                     live ? saveId : null, expiresAt);
}

async function fetchShare(token) {
  if (!sb) return { data: null, error: 'Supabase is not configured.' };
  const { data, error: e } = await sb.from('share_links')
    .select('token, tool, title, payload, save_id, created_at')
    .eq('token', token).single();
  return { data, error: e ? 'Unknown or deleted share link.' : null };
}

async function listShares() {
  const { session, error } = await apiSession();
  if (error) return { data: null, error };
  const { data, error: e } = await sb.from('share_links')
    .select('token, tool, title, save_id, created_at')
    .eq('user_id', session.user.id)
    .order('created_at', { ascending: false });
  return { data: data?.map(r => ({ ...r, url: shareURL(r.token) })), error: apiErr(e) };
}

async function deleteShare(token) {
  const { error } = await apiSession();
  if (error) return { data: null, error };
  const { error: e } = await sb.from('share_links').delete().eq('token', token);
  return { data: !e, error: apiErr(e) };
}

function shareURL(token) {
  // share.html lives at the app root, next to Home.html; tool pages sit one
  // folder deeper, so resolve relative to the parent of the current page.
  return new URL('../share.html', location.href).href + '?token=' + token;
}