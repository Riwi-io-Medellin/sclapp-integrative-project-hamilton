# Authentication with HttpOnly cookies and refresh token

## 1. Modified / created files

### Backend
- **backend/db/schema.sql** – Added `refresh_tokens` table.
- **backend/db/migrations/0002_refresh_tokens.sql** – Optional migration for existing DB.
- **backend/core/config.py** – `refresh_secret_key`, `cookie_secure`.
- **backend/core/security.py** – Rewritten: JWT access/refresh (generate + verify), cookies by name, `get_current_user_from_cookie`.
- **backend/modules/auth/auth_service.py** – Register with werkzeug; login generates access+refresh, stores refresh hash in DB; `store_refresh_token`, `revoke_refresh_token`, `get_user_id_by_refresh_token`.
- **backend/api/v1/auth.py** – Endpoints: register, login (sets cookies), refresh, me, logout (revokes and clears cookies).
- **backend/api/v1/profile.py** – `GET /profile/me` and `PUT /profile/me` use `get_current_user_from_cookie`.
- **backend/requirements.txt** – `werkzeug`, `PyJWT` (replace bcrypt for auth).

### Frontend
- **frontend/assets/js/apiClient.js** – All requests with `credentials: 'include'`; on 401 tries `POST /auth/refresh` and retries once; `setSessionExpiredHandler` to redirect to login.
- **frontend/assets/js/main.js** – Startup with `GET /auth/me`; no localStorage; login/logout call the API; `showAppShell(user)` receives user to show name/initials.

### Config
- **.env.example** – Comments for `REFRESH_SECRET_KEY` and `COOKIE_SECURE`.

---

## 2. Summary of changes

- **Login:** After validating credentials, access token (15 min) and refresh token (7 days) are generated. The refresh is stored hashed in `refresh_tokens`. Both are sent in HttpOnly cookies (`sclapp_access_token`, `sclapp_refresh_token`). The JSON response only includes `message` and `user` (no tokens in the body).
- **Refresh:** `POST /auth/refresh` reads the refresh token from the cookie, validates it (JWT + existence in DB not revoked), revokes the previous one, issues new access and refresh and sends them in cookies.
- **Me:** `GET /auth/me` reads the access token from the cookie and returns the current user.
- **Logout:** `POST /auth/logout` revokes the refresh token in DB and clears auth cookies.
- **Frontend:** No localStorage/sessionStorage for session; all requests with `credentials: 'include'`; on load calls `/auth/me`; if a request returns 401 it tries refresh and retries once; if refresh fails it redirects to login.

---

## 3. Auth flow

```
[App load]
  → GET /auth/me (cookie access_token)
  → 200: showAppShell(user)
  → 401: showLoginScreen()

[Login]
  → POST /auth/login { email, password }
  → 200: Set-Cookie access_token, refresh_token; body { message, user }
  → Frontend: showAppShell(user)

[Request with expired token]
  → Any GET/POST returns 401
  → Frontend: POST /auth/refresh (cookie refresh_token)
  → 200: Set-Cookie new access and refresh; retry original request
  → 401: onSessionExpired() → showLoginScreen()

[Logout]
  → POST /auth/logout (cookie refresh_token)
  → Backend: revokes refresh in DB, Clear-Site-Data / delete cookies
  → Frontend: showLoginScreen()
```

---

## 4. SQL (refresh_tokens table)

If the database already existed before adding the table in `schema.sql`, run the migration:

**backend/db/migrations/0002_refresh_tokens.sql**

```sql
create table if not exists refresh_tokens (
  id_refresh int generated always as identity primary key,
  id_user int not null,
  token_hash varchar(255) not null,
  expires_at timestamptz not null,
  created_at timestamptz not null default current_timestamp,
  revoked_at timestamptz,
  constraint fk_refresh_user foreign key (id_user) references users(id_user) on update cascade on delete cascade
);
create index if not exists idx_refresh_tokens_id_user on refresh_tokens (id_user);
create index if not exists idx_refresh_tokens_token_hash on refresh_tokens (token_hash);
create index if not exists idx_refresh_tokens_expires_at on refresh_tokens (expires_at);
```

---

## 5. Test examples

### Register
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Julio Ramirez","email":"julio@email.com","password":"123456"}'
```
Expected response: `201` and `{"message":"User registered successfully"}`.

### Login (save cookies to file for later calls)
```bash
curl -c cookies.txt -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"julio@email.com","password":"123456"}'
```
Response: `200` and `{"message":"Login successful","user":{...}}`; cookies `sclapp_access_token` and `sclapp_refresh_token` in `cookies.txt`.

### Me
```bash
curl -b cookies.txt http://localhost:8000/api/auth/me
```
Response: `200` and `{"user":{"id_user":1,"full_name":"Julio Ramirez","email":"julio@email.com"}}`.

### Refresh
```bash
curl -b cookies.txt -c cookies.txt -X POST http://localhost:8000/api/auth/refresh
```
Response: `200` and `{"message":"Token refreshed"}`; new cookies sent.

### Logout
```bash
curl -b cookies.txt -X POST http://localhost:8000/api/auth/logout
```
Response: `200` and `{"message":"Logout successful"}`; auth cookies removed.

---

## 6. Pending / second phase

- **Refresh rotation:** The previous refresh is already revoked and a new one is issued on each refresh; optionally limit to one valid refresh token per user.
- **Cleanup of expired tokens:** Periodic job to delete rows from `refresh_tokens` with `expires_at < now()` or old `revoked_at`.
- **Secure in production:** Set `COOKIE_SECURE=true` when the app is served over HTTPS.
- **Same origin:** The app is designed for same origin (API and SPA on the same host). If the frontend is served on another domain, CORS and possibly SameSite for cookies would need to be configured.
