// Register view: form that submits to apiClient.register() -> POST /auth/register.

export function renderRegisterView(container, { onSubmit, onGoToLogin }) {
  container.innerHTML = `
    <div class="logo-top">
      <div class="logo-box-auth">✦</div>
      <span class="logo-nombre-auth">sclapp</span>
    </div>

    <div class="auth-card">
      <h1 class="auth-card-titulo">Create account</h1>
      <p class="auth-card-subtitulo">Intelligent data for real opportunities</p>

      <div class="error-msg" id="errorMsg"></div>

      <div class="form-group">
        <label>Full name</label>
        <div class="input-wrapper">
          <span class="input-icon">👤</span>
          <input type="text" id="regName" placeholder="Your name" />
        </div>
      </div>

      <div class="form-group">
        <label>Email</label>
        <div class="input-wrapper">
          <span class="input-icon">✉</span>
          <input type="email" id="regEmail" placeholder="you@email.com" />
        </div>
      </div>

      <div class="form-group">
        <label>Password</label>
        <div class="input-wrapper">
          <span class="input-icon">🔒</span>
          <input type="password" id="regPass" placeholder="Minimum 6 characters" />
          <button class="toggle-password" id="togglePass">👁</button>
        </div>
      </div>

      <button class="btn-auth" id="btnRegister">Create account →</button>

      <div class="auth-footer">
        Already have an account?
        <a id="linkLogin">Sign in</a>
      </div>
    </div>
  `;

  const nameInput = document.getElementById('regName');
  const emailInput = document.getElementById('regEmail');
  const passInput = document.getElementById('regPass');
  const btnRegister = document.getElementById('btnRegister');
  const togglePass = document.getElementById('togglePass');
  const errorMsg = document.getElementById('errorMsg');
  const linkLogin = document.getElementById('linkLogin');

  function showError(message) {
    errorMsg.textContent = message;
    errorMsg.classList.add('show');
  }

  function clearError() {
    errorMsg.classList.remove('show');
  }

  function setLoading(isLoading) {
    if (isLoading) {
      btnRegister.textContent = 'Creating account...';
      btnRegister.classList.add('loading');
      btnRegister.disabled = true;
    } else {
      btnRegister.textContent = 'Create account →';
      btnRegister.classList.remove('loading');
      btnRegister.disabled = false;
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

  [nameInput, emailInput, passInput].forEach(function (input) {
    input.addEventListener('input', clearError);
  });

  btnRegister.addEventListener('click', function () {
    const name = nameInput.value.trim();
    const email = emailInput.value.trim();
    const password = passInput.value.trim();

    if (!name || !email || !password) {
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
      onSubmit({ name, email, password, showError, setLoading });
    }
  });

  if (typeof onGoToLogin === 'function') {
    linkLogin.addEventListener('click', onGoToLogin);
  }
}

