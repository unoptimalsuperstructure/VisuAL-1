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
  if (sb) await sb.auth.signOut();
  renderAuthButton();
}

async function renderAuthButton() {
  const slot = document.getElementById('auth-slot');
  if (!slot) return;

  const loginHref = slot.dataset.loginHref || 'login.html';

  const session = await authSession();
  if (session) {
    const email = session.user?.email ?? 'account';
    slot.innerHTML =
      `<span class="auth-email" title="${email}">${email}</span>` +
      `<button class="auth-btn" id="auth-logout">Log out</button>`;
    document.getElementById('auth-logout')
      ?.addEventListener('click', authSignOut);
  } else {
    slot.innerHTML = `<a class="auth-btn" href="${loginHref}">Log in</a>`;
  }
}

if (document.readyState === 'loading')
  document.addEventListener('DOMContentLoaded', renderAuthButton);
else
  renderAuthButton();

sb?.auth.onAuthStateChange(() => renderAuthButton());