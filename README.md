# Ajaia Docs

A lightweight collaborative document editor inspired by Google Docs. Create and format documents in the browser, import existing files, and share them with teammates as viewers or editors.

**Live demo:** _add your Render URL here_ (free tier: the first request after ~15 min idle takes up to a minute while the instance wakes up)

| Demo account | Password | What you'll see |
|---|---|---|
| `alice@example.com` | `password123` | Owns *Product Launch Plan* (shared with Bob as editor, Charlie as viewer) and *Kickoff Meeting Notes*; has view access to Bob's checklist |
| `bob@example.com` | `password123` | Owns *Design Review Checklist*; can **edit** Alice's launch plan |
| `charlie@example.com` | `password123` | Can **view** Alice's launch plan (read-only) |

The login page has one-click buttons for each account. Use two browser profiles (or a private window) to be signed in as two users at once.

---

## Features

| Area | What's included |
|---|---|
| **Documents** | Create, rename (click the title), edit, delete (owner only, with confirmation). Dashboard with text previews and "edited 5m ago" times. |
| **Rich text** | Headings 1–3, **bold**, *italic*, <u>underline</u>, ~~strikethrough~~, bulleted and numbered lists, quotes, undo/redo, keyboard shortcuts. |
| **Saving** | Auto-save 1.5 s after you stop typing, plus <kbd>Ctrl/⌘ + S</kbd>. Status shows *Unsaved changes → Saving… → Saved*, with **Retry** if a save fails. The browser warns before closing a tab with unsaved work. |
| **File import** | Turn a **`.txt`, `.md` or `.docx`** file (max **5 MB**) into a new editable document. Headings, bold/italic/underline/strikethrough, lists, quotes and code blocks are kept. Links keep their text; images are dropped; table rows become `cell | cell` lines. Other file types are rejected with a clear message. |
| **Sharing** | The owner shares with any user as **Viewer** or **Editor**, changes access later, or removes it. The dashboard separates **My documents** from **Shared with me**, and each card shows who shared it and your access level. Viewers get a read-only editor with an explanation. |
| **Edit conflicts** | If two people edit the same document, the second save is rejected instead of silently overwriting the first. That user chooses **Load latest** or **Keep mine**. |
| **Persistence** | SQLite via SQLAlchemy. Content is stored as TipTap JSON, so formatting round-trips exactly. |

## Tech stack

**Frontend:** React 18, TypeScript (strict), Vite, TipTap 2 (ProseMirror), Tailwind CSS 4, React Router, Axios, Vitest + Testing Library
**Backend:** Python 3.11+, FastAPI, Pydantic 2, SQLAlchemy 2, SQLite, bcrypt + PyJWT, `markdown` and `mammoth` for imports, pytest
**Deploy:** one Docker image; FastAPI serves both `/api/*` and the built React app. Render blueprint included.

---

## Run locally

Prerequisites: **Python 3.11+** and **Node 18.18+**.

### 1. Backend (http://localhost:8000)

```bash
cd server
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:application --reload
```

On first start it creates `server/ajaia_docs.db` and seeds the demo users and documents. Delete that file to reset the data. Interactive API docs are at http://localhost:8000/docs.

Optional: copy `.env.example` to `server/.env` to override settings (JWT secret, database URL, upload limit). Defaults work for local development.

### 2. Frontend (http://localhost:5173)

In a second terminal:

```bash
cd client
npm install
npm run dev
```

Open **http://localhost:5173**. Vite proxies `/api` to the backend, so no CORS setup is needed.

### Production-style run (single process)

```bash
cd client && npm run build      # outputs client/dist
cd ../server && uvicorn app.main:application --port 8000
```

FastAPI detects `client/dist` and serves the app at http://localhost:8000. Or use Docker:

```bash
docker build -t ajaia-docs .
docker run -p 8000:8000 -e JWT_SECRET=change-me ajaia-docs
```

---

## Tests

```bash
cd server && pytest            # 60 API + unit tests
cd client && npm test          # 14 component / page / hook tests
cd client && npm run typecheck # TypeScript strict mode
```

What the tests cover:

- **Auth:** login, bad credentials, missing or invalid tokens → 401, case-insensitive email.
- **Documents:** CRUD; owners vs editors vs viewers vs strangers (403); input validation (blank or overlong titles, invalid editor JSON, empty updates).
- **Sharing:** grant, list, change permission, revoke; self-share and duplicates rejected; a downgrade takes effect immediately.
- **Edit conflicts:** a stale save gets 409 and nothing is overwritten.
- **Import:** `.md` and `.docx` formatting is preserved; empty, oversized (413), corrupt and unsupported files get clean 4xx errors; raw uploads aren't publicly served.
- **Frontend:**
  - the dashboard's owned vs shared tabs and the create and import flows
  - client-side rejection of unsupported files
  - the auto-save hook: debouncing, version chaining, the conflict path, retry after failure, and no saves for viewers

---

## Deploy to Render

1. **Push to GitHub** (from the `ajaia-docs` folder):
   ```bash
   git init -b main
   git add .
   git commit -m "Ajaia Docs: collaborative document editor"
   # Create an empty repo on github.com, then:
   git remote add origin https://github.com/<your-username>/ajaia-docs.git
   git push -u origin main
   ```
2. On **render.com**: **New → Blueprint**, connect the repo, then **Apply**. Render reads `render.yaml`, builds the `Dockerfile`, generates a random `JWT_SECRET`, and health-checks `/api/health`.
3. When the deploy is live (about 5 minutes), open the `https://<service>.onrender.com` URL and add it to the top of this README.

> **Free-tier note:** Render's free instances have an ephemeral disk, so the SQLite database resets on every deploy or restart and the demo data is re-seeded. For durable data, use a paid instance with a disk mounted at `/app/data`, or point `DATABASE_URL` at Postgres. The code doesn't change.

---

## Project structure

```
ajaia-docs/
├── Dockerfile · render.yaml · .env.example
├── docs/
│   ├── ARCHITECTURE.md        # what was prioritised and why
│   └── AI_USAGE.md            # how AI tools were used and verified
├── server/                    # FastAPI
│   ├── app/
│   │   ├── main.py            # app, CORS, error handler, SPA serving
│   │   ├── config.py · database.py · models.py · seed.py
│   │   ├── auth/ users/ documents/ shares/ upload/   # router · schemas · service
│   │   └── utils/             # HTTP errors, UTC timestamps
│   └── tests/                 # pytest (in-memory SQLite)
└── client/                    # React + Vite
    ├── src/
    │   ├── api/               # typed API calls (Axios)
    │   ├── contexts/ hooks/   # auth, data loading, useAutoSave
    │   ├── pages/             # Login, Dashboard, Editor
    │   └── components/        # layout, dashboard, editor, sharing, ui
    └── tests/                 # Vitest + Testing Library
```

## API

| Method | Endpoint | Who | Purpose |
|---|---|---|---|
| `POST` | `/api/auth/login` | anyone | Email + password → JWT |
| `GET` | `/api/auth/me` | signed in | Current user |
| `GET` | `/api/users` | signed in | Users for the share picker |
| `GET` | `/api/documents` | signed in | Owned and shared documents, each with your `role` |
| `POST` | `/api/documents` | signed in | Create |
| `GET` | `/api/documents/{id}` | owner, editor, viewer | Read |
| `PUT` | `/api/documents/{id}` | owner, editor | Update title/content; optional `expected_updated_at` → 409 if stale |
| `DELETE` | `/api/documents/{id}` | owner | Delete (and its shares) |
| `GET` / `POST` | `/api/documents/{id}/shares` | owner | List / grant access |
| `PATCH` / `DELETE` | `/api/documents/{id}/shares/{share_id}` | owner | Change / revoke access |
| `POST` | `/api/upload` | signed in | Import `.txt` / `.md` / `.docx` (≤ 5 MB) as a new document |
| `GET` | `/api/health` | anyone | Liveness probe |

## Known limitations

- **No live co-editing.** Changes from others appear when you reopen the document; simultaneous edits are caught by the conflict check rather than merged. See `docs/ARCHITECTURE.md` for the path to real-time.
- **Import fidelity.** Images, tables and hyperlinks aren't supported by the editor yet, so they're reduced to text on import.
- **Demo-grade auth.** Seeded accounts and no sign-up. The JWT is kept in `localStorage` for simplicity.
- **SQLite.** Fine for a demo and a single instance. Use Postgres for multiple instances.

## More

- [Architecture & prioritisation](docs/ARCHITECTURE.md)
- [AI-native workflow note](docs/AI_USAGE.md)
