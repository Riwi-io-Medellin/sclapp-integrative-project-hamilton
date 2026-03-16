// Login view: form that submits to apiClient.login() -> POST /auth/login (cookies set by backend).

export function renderLoginView(container, { onSubmit, onGoToRegister }) {
  container.innerHTML = `
    <div class="logo-top">
      <div class="logo-box-auth">✦</div>
      <span class="logo-nombre-auth">sclapp</span>
    </div>

    <div class="auth-card">
      <h1 class="auth-card-titulo">Welcome back</h1>
      <p class="auth-card-subtitulo">Sign in to continue</p>

      <div class="error-msg" id="errorMsg"></div>

      <div class="form-group">
        <label>Email</label>
        <div class="input-wrapper">
          <span class="input-icon">✉</span>
          <input type="email" id="loginEmail" placeholder="you@email.com" />
        </div>
      </div>

      <div class="form-group">
        <label>Password</label>
        <div class="input-wrapper">
          <span class="input-icon">🔒</span>
          <input type="password" id="loginPass" placeholder="••••••••" />
          <button class="toggle-password" id="togglePass">👁</button>
        </div>
      </div>

      <button class="btn-auth" id="btnLogin">Sign in →</button>

      <div class="auth-footer">
        Don’t have an account?
        <a id="linkRegister">Create account</a>
      </div>
    </div>
  `;

  const emailInput = document.getElementById('loginEmail');
  const passInput = document.getElementById('loginPass');
  const btnLogin = document.getElementById('btnLogin');
  const togglePass = document.getElementById('togglePass');
  const errorMsg = document.getElementById('errorMsg');
  const linkRegister = document.getElementById('linkRegister');

  function showError(message) {
    errorMsg.textContent = message;
    errorMsg.classList.add('show');
  }

  function clearError() {
    errorMsg.classList.remove('show');
  }

  function setLoading(isLoading) {
    if (isLoading) {
      btnLogin.textContent = 'Signing in...';
      btnLogin.classList.add('loading');
      btnLogin.disabled = true;
    } else {
      btnLogin.textContent = 'Sign in →';
      btnLogin.classList.remove('loading');
      btnLogin.disabled = false;
    }
  }

  togglePass.addEventListener('click', function () {
    if (passInput.type === 'password') {
      passInput.type = 'text';
      togglePass.textContent = '🙈';
    } else {
      passInput.type = 'password';
      togglePass.textContent = '👁';
    }
  });

  emailInput.addEventListener('input', clearError);
  passInput.addEventListener('input', clearError);

  btnLogin.addEventListener('click', function () {
    const email = emailInput.value.trim();
    const password = passInput.value.trim();

    if (!email || !password) {
      showError('Please complete all fields.');
      return;
    }

    if (!email.includes('@')) {
      showError('Please enter a valid email address.');
      return;
    }

    if (password.length < 6) {
      showError('Password must be at least 6 characters.');
      return;
    }

    if (typeof onSubmit === 'function') {
      onSubmit({ email, password, showError, setLoading });
    }
  });

  document.addEventListener('keydown', function handler(e) {
    if (e.key === 'Enter') {
      btnLogin.click();
      document.removeEventListener('keydown', handler);
    }
  });

  if (typeof onGoToRegister === 'function') {
    linkRegister.addEventListener('click', onGoToRegister);
  }
}

