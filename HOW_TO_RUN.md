# How to run SCLAPP

Step-by-step guide to run the backend (FastAPI), database (PostgreSQL), and frontend.

---

## 1. Project requirements

- **Python 3.10+** installed and on your PATH.
- **PostgreSQL** installed and running (default port 5432).
- A terminal or editor at the **project root** (the folder that contains `backend/` and `frontend/`).

---

## 2. Clone the repository

Clone or open the project and go to its root:

```bash
cd path/to/Sclapp
```

The root must contain the `backend` and `frontend` folders.

---

## 3. Create the database in PostgreSQL

1. Open **pgAdmin**, **psql**, or any PostgreSQL client.
2. Create a new database (for example `sclapp`):

   ```sql
   CREATE DATABASE sclapp;
   ```

3. Connect to that database and run the schema script:

   - File: `backend/db/schema.sql`
   - In psql: `\i full/path/to/backend/db/schema.sql`
   - Or copy and paste the file contents into the SQL console.

4. (Optional) To test login with a sample user, insert a user (adjust `password_hash` if you use real verification later):

   ```sql
   INSERT INTO users (full_name, doc_num, user_name, password_hash, email, id_role)
   VALUES ('Admin', '123', 'admin', 'hash_here', 'admin@sclapp.com', 1)
   ON CONFLICT (email) DO NOTHING;
   ```

   If you do not create users, the frontend test login (fake user) may still be used for demo.

---

## 4. Environment variables (.env)

1. In the **project root** (or inside `backend/`) create a file named `.env`.

2. Add at least these variables (adjust for your PostgreSQL setup):

   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=sclapp
   DB_USER=postgres
   DB_PASSWORD=your_postgres_password
   ```

3. Optional: if you serve the frontend on another port (e.g. Live Server on 5500):

   ```env
   CORS_ORIGINS=http://localhost:5500,http://127.0.0.1:5500,http://localhost:3000
   ```

4. For authentication and optional features, you can add (see `.env.example` for more):

   ```env
   SECRET_KEY=your_secret_key_here
   OPENAI_API_KEY=your_openai_key_here
   ```

Save the file. Do not commit `.env` to Git (it should be in `.gitignore`).

---

## 5. Virtual environment and dependencies (backend)

1. Open a terminal at the **project root**.

2. Create the virtual environment:

   ```bash
   python -m venv venv
   ```

3. Activate it:

   - **Windows (CMD):**  
     `venv\Scripts\activate`
   - **Windows (PowerShell):**  
     `venv\Scripts\Activate.ps1`
   - **Linux / macOS:**  
     `source venv/bin/activate`

   You should see `(venv)` at the start of the line.

4. Install backend dependencies:

   ```bash
   pip install -r backend/requirements.txt
   ```

---

## 6. Start the server

With the virtual environment active and from the **project root**:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

- **Success:** you should see something like `Uvicorn running on http://0.0.0.0:8000`.
- **Single URL:** open **http://localhost:8000** in your browser — the app (frontend + API) is served there.
- **API:** **http://localhost:8000/api**
- **Interactive docs:** **http://localhost:8000/docs**

Keep this terminal open while you use the app. The same server serves the frontend (HTML, CSS, JS) and the API; you do not need another terminal or port.

---

## 7. Use the application

1. With the server running, open in your browser: **http://localhost:8000**
2. You should see the SCLAPP login screen.
3. Use your registered user, or the test user if you inserted one (e.g. email: `admin@sclapp.com`, password: as set in DB).
4. Go to the dashboard and navigate to Companies, Profile, etc.

---

## Quick summary

| What              | Where to run     | Command |
|-------------------|------------------|--------|
| All (API + frontend) | Project root | `uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000` |

Then open **http://localhost:8000** in your browser.

---

## Common issues

- **Database:** If the backend fails to start, check that PostgreSQL is running, that the `sclapp` database exists, and that `DB_*` in `.env` are correct.
- **Modules not found:** Run `uvicorn` from the **project root** (where the `backend/` folder is), not from inside `backend/`.
- **Blank frontend:** Open **http://localhost:8000** in the browser, not the `index.html` file with double-click (`file://`).
- **CORS:** If you serve the frontend on another port later, add that URL to `CORS_ORIGINS` in your `.env`.
