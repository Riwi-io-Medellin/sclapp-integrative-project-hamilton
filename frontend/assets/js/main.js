// SPA entry: checks session via GET /auth/me (cookies), then shows login or app shell.
// App shell: sidebar (Dashboard, Companies), topbar with avatar menu (Profile, Log out), main content area.
// Hash-based routing: dashboard, companies, emails, profile. No localStorage for session.

import { initRouter, navigateTo } from './router.js';
import { apiClient, setSessionExpiredHandler } from './apiClient.js';
import { renderLoginView } from './login.js';
import { renderRegisterView } from './register.js';
import { renderDashboardView } from './dashboard.js';
import { renderCompaniesView } from './companies.js';
import { renderEmailsView } from './emails.js';
import { renderProfileView } from './profile.js';

const appRoot = document.getElementById('app');

export function showLoginScreen() {
  document.body.className = 'auth-body';
  appRoot.className = '';
  renderLoginView(appRoot, {
    onSubmit: handleLoginSubmit,
    onGoToRegister: showRegisterScreen,
  });
}

export function showRegisterScreen() {
  document.body.className = 'auth-body';
  appRoot.className = '';
  renderRegisterView(appRoot, {
    onSubmit: handleRegisterSubmit,
    onGoToLogin: showLoginScreen,
  });
}

function showAppShell(user) {
  document.body.className = '';
  appRoot.className = 'spa-body';

  const displayName = user?.full_name || user?.user_name || 'sclapp';
  const initials = displayName
    .split(' ')
    .map((p) => p[0])
    .join('')
    .toUpperCase()
    .slice(0, 2) || 'SC';

  appRoot.innerHTML = `
    <aside id="sidebar">
      <div class="sidebar-logo">
        <div class="logo-box">✦</div>
        <span class="logo-nombre">sclapp</span>
      </div>
      <nav class="sidebar-nav">
        <button class="nav-item" data-view="dashboard">
          <span class="nav-icono">⊞</span>
          <span>Dashboard</span>
        </button>
        <button class="nav-item" data-view="companies">
          <span class="nav-icono">🏢</span>
          <span>Companies</span>
        </button>
      </nav>
      <div class="sidebar-bottom">
        <button class="btn-cerrar-sesion" id="btnLogout">
          <span>↪</span>
          <span>Log out</span>
        </button>
        <div class="sidebar-user">
          <div class="avatar-small" id="sidebarAvatar">${initials}</div>
          <div>
            <span class="sidebar-user-nombre" id="sidebarUserName">${displayName}</span>
            <span class="sidebar-user-version">v1.0.0 MVP</span>
          </div>
        </div>
      </div>
    </aside>
    <div id="sidebar-backdrop" class="sidebar-backdrop" aria-hidden="true"></div>
    <div id="app-wrapper">
      <div id="topbar">
        <button type="button" id="btnSidebarToggle" class="topbar-hamburger" aria-label="Open menu">☰</button>
        <div class="topbar-search">
          <span style="color:#475569;font-size:13px;">🔍</span>
          <input type="text" placeholder="Search companies..." />
        </div>
        <div class="topbar-right">
          <button class="topbar-ico-btn">🔔</button>
          <div class="avatar-dropdown-wrap" style="position:relative;">
            <button type="button" class="avatar-usuario avatar-usuario-btn" id="topbarAvatarBtn" title="Account menu" aria-haspopup="true" aria-expanded="false">${initials}</button>
            <div class="avatar-dropdown" id="avatarDropdown" role="menu" aria-hidden="true" style="display:none;">
              <button type="button" class="avatar-dropdown-item" data-action="profile" role="menuitem">Profile</button>
              <button type="button" class="avatar-dropdown-item" data-action="logout" role="menuitem">Log out</button>
            </div>
          </div>
        </div>
      </div>
      <main id="main-content"></main>
      <footer id="footer">
        <span>sclapp v1.0.0 — Tech Talent Lead Finder</span>
        <span>Last update: 2 minutes ago</span>
      </footer>
    </div>
  `;

  const mainContent = document.getElementById('main-content');
  initRouter({
    mainElement: mainContent,
    routes: {
      dashboard: renderDashboardView,
      companies: renderCompaniesView,
      emails: renderEmailsView,
      profile: renderProfileView,
    },
  });

  function closeSidebar() {
    document.body.classList.remove('sidebar-open');
    const backdrop = document.getElementById('sidebar-backdrop');
    if (backdrop) {
      backdrop.setAttribute('aria-hidden', 'true');
    }
  }

  function openSidebar() {
    document.body.classList.add('sidebar-open');
    const backdrop = document.getElementById('sidebar-backdrop');
    if (backdrop) {
      backdrop.setAttribute('aria-hidden', 'false');
    }
  }

  const btnSidebarToggle = document.getElementById('btnSidebarToggle');
  if (btnSidebarToggle) {
    btnSidebarToggle.addEventListener('click', () => {
      if (document.body.classList.contains('sidebar-open')) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });
  }

  const sidebarBackdrop = document.getElementById('sidebar-backdrop');
  if (sidebarBackdrop) {
    sidebarBackdrop.addEventListener('click', closeSidebar);
  }

  document.querySelectorAll('#sidebar .nav-item').forEach((btn) => {
    btn.addEventListener('click', () => {
      const view = btn.dataset.view;
      setActiveNav(view);
      navigateTo(view);
      window.location.hash = view;
      closeSidebar();
    });
  });

  const logoutButton = document.getElementById('btnLogout');
  if (logoutButton) {
    logoutButton.addEventListener('click', async () => {
      const confirmed = window.confirm('Are you sure you want to log out?');
      if (confirmed) {
        try {
          await apiClient.logout();
        } catch (_) {}
        showLoginScreen();
      }
    });
  }

  const avatarBtn = document.getElementById('topbarAvatarBtn');
  const avatarDropdown = document.getElementById('avatarDropdown');
  function closeAvatarDropdown() {
    if (avatarDropdown) {
      avatarDropdown.style.display = 'none';
      avatarDropdown.setAttribute('aria-hidden', 'true');
      if (avatarBtn) avatarBtn.setAttribute('aria-expanded', 'false');
    }
  }
  if (avatarBtn && avatarDropdown) {
    avatarBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = avatarDropdown.style.display === 'block';
      avatarDropdown.style.display = isOpen ? 'none' : 'block';
      avatarDropdown.setAttribute('aria-hidden', isOpen ? 'true' : 'false');
      avatarBtn.setAttribute('aria-expanded', isOpen ? 'false' : 'true');
    });
    avatarDropdown.querySelectorAll('.avatar-dropdown-item').forEach((item) => {
      item.addEventListener('click', (e) => {
        e.stopPropagation();
        closeAvatarDropdown();
        if (item.dataset.action === 'profile') {
          setActiveNav('profile');
          navigateTo('profile');
          window.location.hash = 'profile';
        } else if (item.dataset.action === 'logout') {
          (async () => {
            const confirmed = window.confirm('Are you sure you want to log out?');
            if (confirmed) {
              try {
                await apiClient.logout();
              } catch (_) {}
              showLoginScreen();
            }
          })();
        }
      });
    });
    document.addEventListener('click', closeAvatarDropdown);
  }

  const initialView = window.location.hash.replace('#', '') || 'dashboard';
  setActiveNav(initialView);
  navigateTo(initialView);
}

function setActiveNav(view) {
  document.querySelectorAll('#sidebar .nav-item').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.view === view);
  });
}

async function handleLoginSubmit({ email, password, showError, setLoading }) {
  setLoading(true);
  try {
    const response = await apiClient.login({ email, password });
    if (response?.user) {
      showAppShell(response.user);
      return;
    }
    showError('Invalid email or password.');
  } catch (err) {
    if (err?.message?.includes('401')) {
      showError('Invalid email or password.');
    } else {
      showError('Unable to reach the server. Please try again.');
    }
  } finally {
    setLoading(false);
  }
}

async function handleRegisterSubmit({ name, email, password, showError, setLoading }) {
  setLoading(true);
  try {
    await apiClient.register({ full_name: name, email, password });
    window.alert('Account created successfully. Please log in.');
    showLoginScreen();
  } catch (err) {
    showError(err?.message?.includes('409') ? 'Email already registered.' : 'Unable to create account. Please try again.');
  } finally {
    setLoading(false);
  }
}

setSessionExpiredHandler(() => showLoginScreen());

(async () => {
  try {
    const data = await apiClient.me();
    if (data?.user) {
      showAppShell(data.user);
      return;
    }
  } catch (_) {}
  showLoginScreen();
})();
