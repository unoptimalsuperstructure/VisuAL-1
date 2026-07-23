'use strict';

const SUPABASE_URL      = 'https://ywjprydgpjpbdsmcttiz.supabase.co';
const SUPABASE_PUB_KEY = 'sb_publishable_q_h6lV_UzaYJS1IBED0Rug_M8hfb2zv';

const authConfigured =
  SUPABASE_URL.startsWith('https://') && SUPABASE_PUB_KEY.length > 20;

const sb = (authConfigured && typeof supabase !== 'undefined')
  ? supabase.createClient(SUPABASE_URL, SUPABASE_PUB_KEY)
  : null;

async function authSession() {
  if (!sb) return null;
  const { data } = await sb.auth.getSession();
  return data.session ?? null;
}

async function authToken() {
  const s = await authSession();
  return s?.access_token ?? null;
}

async function authSignOut() {
  if (!sb) return;
  try { await sb.auth.signOut({ scope: 'local' }); } catch (_) {}
  try {
    const { data } = await sb.auth.getSession();
    if (data.session)
      for (const k of Object.keys(localStorage))
        if (/^sb-.*-auth-token$/.test(k)) localStorage.removeItem(k);
  } catch (_) {}
  renderAuthButton();
}

async function renderAuthButton() {
  const slot = document.getElementById('auth-slot');
  if (!slot) return;

  const loginHref = slot.dataset.loginHref || '../Login/login.html';
  slot.textContent = '';

  const session = authConfigured ? await authSession() : null;
  if (session) {
    const btn = document.createElement('button');
    btn.className = 'auth-btn';
    btn.id = 'auth-logout';
    btn.textContent = 'Log out';
    btn.addEventListener('click', authSignOut);
    slot.appendChild(btn);
  } else {
    const a = document.createElement('a');
    a.className = 'auth-btn';
    a.href = loginHref;
    a.textContent = 'Log in';
    slot.appendChild(a);
  }
}

if (document.readyState === 'loading')
  document.addEventListener('DOMContentLoaded', renderAuthButton);
else
  renderAuthButton();

sb?.auth.onAuthStateChange(() => renderAuthButton());