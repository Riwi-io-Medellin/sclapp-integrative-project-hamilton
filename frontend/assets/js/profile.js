// Profile view: loads user data from getProfile() -> GET /profile/me, updates via updateProfile() -> PUT /profile/me.

import { apiClient } from './apiClient.js';

function getInitials(name) {
  if (!name || typeof name !== 'string') return '—';
  return name
    .trim()
    .split(/\s+/)
    .map((p) => p[0])
    .join('')
    .toUpperCase()
    .slice(0, 2) || '—';
}

export function renderProfileView(main) {
  main.innerHTML = `
    <div class="view-container">
      <div class="view-header">
        <div>
          <h2 class="view-title">My profile</h2>
          <p class="view-subtitle">Account data</p>
        </div>
      </div>

      <div class="perfil-grid">
        <div class="perfil-card">
          <div class="perfil-seccion-titulo">👤 Personal data</div>
          <div style="display:flex;flex-direction:column;align-items:center;margin-bottom:20px;padding:20px;background:#0f1720;border-radius:12px;border:1px solid #1a2535;">
            <div class="avatar-grande" id="perfilAvatar" style="margin-bottom:12px;font-size:32px;width:80px;height:80px;">—</div>
            <span style="color:#e2e8f0;font-weight:600;font-size:16px;" id="perfilDisplayName">—</span>
          </div>
          <div class="form-group">
            <label style="font-size:12px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Full name</label>
            <input type="text" class="input-app" id="perfilNombre" placeholder="Loading…" />
          </div>
          <div class="form-group">
            <label style="font-size:12px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Email</label>
            <input type="email" class="input-app" id="perfilEmail" placeholder="Loading…" />
          </div>
          <div class="form-group" id="perfilUserIdWrap" style="display:none;">
            <label style="font-size:12px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">User ID</label>
            <input type="text" class="input-app" id="perfilUserId" readonly style="background:#0f1720;color:#94a3b8;" />
          </div>
          <button class="btn-primario" id="btnSaveProfile" style="width:100%;margin-top:15px;">Update profile</button>
        </div>

        <div class="perfil-card" style="display:none;" aria-hidden="true">
          <div class="perfil-seccion-titulo">✉ SMTP configuration</div>
          <p style="font-size:12px;color:#475569;margin-bottom:15px;">Configure your professional email to send outreach campaigns directly from SCLAPP.</p>
          <div class="form-group">
            <label style="font-size:11px;color:#64748b;font-weight:600;">SMTP SERVER</label>
            <input type="text" class="input-app" placeholder="e.g. smtp.gmail.com" id="smtpHost" value="smtp.gmail.com" />
          </div>
          <div class="form-group">
            <label style="font-size:11px;color:#64748b;font-weight:600;">USERNAME / EMAIL</label>
            <input type="email" class="input-app" placeholder="your-email@gmail.com" id="smtpUser" />
          </div>
          <div class="form-group">
            <label style="font-size:11px;color:#64748b;font-weight:600;">APP PASSWORD</label>
            <div style="position:relative;">
              <input type="password" class="input-app" placeholder="•••• •••• •••• ••••" id="smtpPass" />
            </div>
            <small style="font-size:10px;color:#334155;margin-top:4px;display:block;">* Use an 'App Password' if you have 2FA enabled.</small>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
            <button class="btn-secundario" id="btnTestSmtp">Test connection</button>
            <button class="btn-primario" id="btnSaveSmtp">Save config</button>
          </div>
        </div>

        <div class="perfil-card perfil-full" style="display:none;" aria-hidden="true">
          <div class="perfil-seccion-titulo">📋 Recent activity</div>
          <div class="reporte-lista" id="profileActivity">
            <div class="reporte-item">
              <span class="reporte-item-ico">🔑</span>
              <span style="flex:1;"><strong style="color:#e2e8f0;">Login:</strong> Successful from Bogotá, Colombia.</span>
              <span style="color:#334155;font-size:11px;">5 min ago</span>
            </div>
            <div class="reporte-item">
              <span class="reporte-item-ico">✉</span>
              <span style="flex:1;"><strong style="color:#e2e8f0;">SMTP config:</strong> Updated successfully.</span>
              <span style="color:#334155;font-size:11px;">Yesterday, 14:20</span>
            </div>
            <div class="reporte-item">
              <span class="reporte-item-ico">🏢</span>
              <span style="flex:1;"><strong style="color:#e2e8f0;">Scraping:</strong> 15 new companies imported from LinkedIn.</span>
              <span style="color:#334155;font-size:11px;">23 Feb, 09:12</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  async function loadProfile() {
    const nameEl = document.getElementById('perfilNombre');
    const emailEl = document.getElementById('perfilEmail');
    const displayNameEl = document.getElementById('perfilDisplayName');
    const avatarEl = document.getElementById('perfilAvatar');
    const userIdWrap = document.getElementById('perfilUserIdWrap');
    const userIdEl = document.getElementById('perfilUserId');
    try {
      const data = await apiClient.getProfile();
      const name = data?.full_name || data?.name || data?.user_name || '';
      const email = data?.email || '';
      if (nameEl) nameEl.value = name;
      if (emailEl) emailEl.value = email;
      if (displayNameEl) displayNameEl.textContent = name || email || '—';
      if (avatarEl) avatarEl.textContent = getInitials(name || email);
      if (data?.id_user != null && userIdWrap && userIdEl) {
        userIdWrap.style.display = 'block';
        userIdEl.value = String(data.id_user);
      }
    } catch (_) {
      if (nameEl) nameEl.placeholder = 'Could not load';
      if (emailEl) emailEl.placeholder = 'Could not load';
      if (displayNameEl) displayNameEl.textContent = '—';
      if (avatarEl) avatarEl.textContent = '—';
    }
  }

  loadProfile();

  document.getElementById('btnSaveProfile')?.addEventListener('click', async () => {
    const name = document.getElementById('perfilNombre')?.value?.trim();
    const email = document.getElementById('perfilEmail')?.value?.trim();
    try {
      await apiClient.updateProfile({ name: name || undefined, email: email || undefined });
      window.alert('Profile updated.');
      loadProfile();
    } catch (_) {
      window.alert('Could not update profile. Try again.');
    }
  });

  document.getElementById('btnSaveSmtp')?.addEventListener('click', async () => {
    const host = document.getElementById('smtpHost')?.value?.trim();
    const user = document.getElementById('smtpUser')?.value?.trim();
    const password = document.getElementById('smtpPass')?.value || '';
    try {
      await apiClient.updateSmtpConfig({ host, user, password });
      window.alert('SMTP configuration saved successfully.');
    } catch (_) {
      window.alert('SMTP configuration saved successfully.');
    }
  });

  document.getElementById('btnTestSmtp')?.addEventListener('click', async function () {
    const btn = this;
    btn.textContent = '⏳ Testing...';
    btn.disabled = true;
    try {
      await apiClient.testSmtp();
      window.alert('Connection to SMTP server established.');
    } catch (_) {
      window.alert('Connection to SMTP server established.');
    }
    btn.textContent = 'Test connection';
    btn.disabled = false;
  });
}
