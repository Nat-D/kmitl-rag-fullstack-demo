# KMITL RAG demo — a full-stack Retrieval-Augmented Generation app

A small, **readable** RAG application you can run end to end and read top to
bottom. It's the companion to **Lecture 6 (Retrieval-Augmented Generation)** of
*Building LLM-Powered Applications*, built to show what it actually takes to wire
the pieces together:

- **Postgres + [pgvector](https://github.com/pgvector/pgvector)** as the vector store
- **FastAPI** backend in the course's `router → service → repository` layering, with **SQLAlchemy** (async) doing the data access
- **Alembic** for the schema (the `vector(1024)` column + an HNSW index)
- **SvelteKit** frontend with two pages:
  1. **Ingest** — upload a file and *watch how it gets chunked* before it's embedded and stored
  2. **Ask** — see a question get embedded, retrieved (ranked chunks), augmented into the system prompt, and answered

It talks to the class LLM proxy for both embeddings (`bge-m3`, 1024-dim) and chat
(`gemma-4-E4B-it`). This is a teaching reference, not a homework answer.

```
┌───────────┐  upload   ┌──────────────────────────────┐  embed   ┌──────────────┐
│  Svelte   │ ───────►  │  FastAPI: ingest service     │ ───────► │  LLM proxy   │
│  Ingest   │           │  chunk → embed → store        │          │  bge-m3      │
└───────────┘           └──────────────┬───────────────┘          └──────────────┘
                                        │ SQLAlchemy
                                        ▼
┌───────────┐  question ┌──────────────────────────────┐  search  ┌──────────────┐
│  Svelte   │ ───────►  │  FastAPI: retrieval + chat    │ ───────► │  Postgres    │
│   Ask     │ ◄───────  │  retrieve → augment → answer  │ ◄─────── │  + pgvector  │
└───────────┘  answer   └──────────────┬───────────────┘  chunks   └──────────────┘
                                        │ chat (grounded)
                                        ▼  gemma-4-E4B-it
```

---

## Part 1 — Setup (step by step)

### Prerequisites
- **Docker** + **Docker Compose** (that's it — Postgres, Python, and Node all run in containers).
- Your **personal LLM key** from the course portal: **Profile → API key → Copy**.

### 1. Get the code and your key in place
```bash
git clone https://github.com/Nat-D/kmitl-rag-fullstack-demo.git
cd kmitl-rag-fullstack-demo
cp .env.example .env
```
Open `.env` and paste your key into `OPENAI_API_KEY`. Leave `OPENAI_BASE_URL` as
`https://llm.nat-d.uk/v1`. **Never commit `.env`** — it's git-ignored.

### 2. Start everything
```bash
docker compose up --build
```
This builds three things and starts two services:
- **db** — Postgres 16 with pgvector (our `docker/postgres` image; enables the
  `vector` extension on first boot).
- **backend** — builds the Svelte SPA, then starts FastAPI. On start it runs
  `alembic upgrade head` to create the tables, then serves **both** the API and
  the web app.

When you see `Uvicorn running on http://0.0.0.0:8000`, open **<http://localhost:8000>**.

> First build downloads the Node + Python images and installs deps — a few
> minutes. Re-runs are cached and fast.

### 3. Ingest a document
Go to the **Ingest** page. Upload one of the files in [`sample-docs/`](sample-docs)
(or any `.txt` / `.md`). You'll see it broken into overlapping **chunks** — the
highlighted text is the overlap shared with the previous chunk — then stored.

### 4. Ask a question
Go to the **Ask** page and ask something answerable from what you ingested, e.g.
*"What embedding model does the course use and how many dimensions?"* You'll see:
1. the **retrieved chunks**, ranked by cosine similarity, each with its score;
2. the **augmented system prompt** (click to expand) — the chunks pasted in as context;
3. the **answer**, grounded in that context.

Then try an off-topic question (*"What's the capital of France?"*) — nothing
clears the `min_score` floor, so the app says it doesn't know instead of guessing.
That floor is the whole point of honest retrieval.

### Verify from the terminal (optional)
```bash
curl localhost:8000/api/health                       # {"status":"ok"}
curl localhost:8000/api/config                        # the retrieval knobs
curl -F "file=@sample-docs/pgvector-notes.md" localhost:8000/api/ingest
curl -s localhost:8000/api/ask -H 'Content-Type: application/json' \
  -d '{"question":"Which pgvector operator is cosine distance?"}' | python3 -m json.tool
```

### Tuning
All retrieval knobs live in one place — `backend/app/config.py`
(`top_k`, `min_score`, `chunk_size`, `chunk_overlap`). Change one, restart the
backend (`docker compose restart backend`), re-ingest, and watch the behaviour
change.

### Reset the database
```bash
docker compose down -v      # -v also drops the pgdata volume
```

---

## Part 2 — Local development (recommended while coding)

For day-to-day development you don't want to rebuild a Docker image on every edit.
The comfortable setup is: **run only Postgres in Docker, run the backend and
frontend on your machine with hot reload.** Three terminals.

```
┌─ terminal 1 ─────────┐   ┌─ terminal 2 ──────────────┐   ┌─ terminal 3 ─────────────┐
│ Postgres + pgvector  │   │ FastAPI  (uvicorn --reload)│   │ Svelte  (vite dev)        │
│ docker compose up db │   │ :8000, reloads on save     │   │ :5173, proxies /api → 8000│
└──────────────────────┘   └────────────────────────────┘   └──────────────────────────┘
```

**One-time prerequisites:** [`uv`](https://docs.astral.sh/uv/) (Python) and
Node.js. And a `.env` in the repo root with your key (`cp .env.example .env`) —
the backend reads it even when run from `backend/`.

### Terminal 1 — the database only
```bash
docker compose up db          # just Postgres+pgvector, published on localhost:5433
```
Leave it running. (Add `-d` to detach.) Nothing else in Docker.

### Terminal 2 — the backend, with reload
```bash
cd backend
uv sync                       # create the venv + install deps (first time only)
uv run alembic upgrade head   # create the tables in the Docker DB
uv run uvicorn app.main:app --reload
```
- `--reload` restarts the server on every save.
- No connection string needed: the default `database_url` in `app/config.py`
  already points at `localhost:5433` (the port Docker publishes), and your key
  comes from the root `.env`.
- The API is at **<http://localhost:8000>** (e.g. `curl localhost:8000/api/health`).

### Terminal 3 — the frontend, with hot reload
```bash
cd frontend
npm install                   # first time only
npm run dev
```
Open **<http://localhost:5173>**. Vite hot-reloads on save and **proxies `/api`**
to the backend on `:8000` (see `frontend/vite.config.js`), so the two talk to
each other with no CORS setup.

### The everyday loop
Edit backend code → uvicorn reloads → refresh. Edit a Svelte page → the browser
updates instantly. Change a retrieval knob in `app/config.py` (`top_k`,
`min_score`, `chunk_size`) → uvicorn reloads → re-ingest and see the effect.

### Handy commands
```bash
docker compose logs -f db     # watch the database
docker compose down           # stop the DB (keeps data)
docker compose down -v        # stop the DB and wipe it (fresh start)
cd backend && uv run pytest   # run the unit tests (no DB/network needed)
cd backend && uv run ruff check app   # lint
```

> **Schema change?** Edit `app/models.py`, then
> `cd backend && uv run alembic revision --autogenerate -m "what changed"`,
> review the generated file in `alembic/versions/`, and
> `uv run alembic upgrade head`.

> **Windows:** run the same commands in PowerShell. Because the backend reads the
> root `.env`, you don't need to `set`/`export` anything. Docker Desktop must be
> running for terminal 1.

---

## Part 3 — Reading guide (which files, in what order)

The code is meant to be read. Follow this order and you'll trace one document from
upload to grounded answer. Each file is short and commented.

### The data model (start here)
1. **`backend/app/config.py`** — every setting in one place: the proxy URL, the
   models, the embedding dimension (1024), and the retrieval knobs.
2. **`backend/app/models.py`** — the two SQLAlchemy tables: `Document` and
   `Chunk`. Note the `embedding` column is a pgvector `Vector(1024)`.
3. **`backend/alembic/versions/0001_initial_schema.py`** — the same schema as a
   migration: `CREATE EXTENSION vector`, the tables, and the HNSW cosine index.

### Indexing — how a file becomes searchable vectors
4. **`backend/app/chunking.py`** — split text into overlapping windows (with
   offsets, so the UI can visualise it).
5. **`backend/app/llm.py`** — the one wrapper around the proxy: `embed_texts` and
   `chat`.
6. **`backend/app/services/ingest_service.py`** — the indexing pipeline in one
   function: decode → chunk → embed → store.
7. **`backend/app/repositories/document_repository.py`** — the only file that
   touches SQL. Read `add_document` (write) now; you'll come back for
   `search_chunks`.

### Query time — retrieve, augment, answer
8. **`backend/app/repositories/document_repository.py` → `search_chunks`** — the
   retrieval query: rank chunks by pgvector cosine distance, return the top-k.
9. **`backend/app/services/retrieval_service.py`** — embed the question, search,
   and drop anything below `min_score`.
10. **`backend/app/services/chat_service.py`** — the RAG "agent":
    `build_system_prompt` pastes the chunks in as context, then it calls the model.
    **This is the heart of RAG.**

### The edges — HTTP and UI
11. **`backend/app/routers/deps.py`** — how a request session becomes a
    repository → service graph (dependency injection).
12. **`backend/app/routers/documents.py`** and **`chat.py`** — thin HTTP handlers
    over the services.
13. **`backend/app/main.py`** — wires the routers, `/api/health`, `/api/config`,
    and serves the SPA.
14. **`frontend/src/routes/+page.svelte`** — the ingest page + chunk
    visualisation.
15. **`frontend/src/routes/ask/+page.svelte`** — the ask page: it renders the
    same three steps (retrieve → augment → answer) the backend performed.

### How it all runs
16. **`docker-compose.yml`**, **`docker/postgres/Dockerfile`**,
    **`backend/Dockerfile`**, **`backend/entrypoint.sh`** — the infrastructure:
    pgvector image, multi-stage build, migrate-then-serve.

### Tests
`backend/tests/test_pipeline.py` covers the deterministic pieces (chunking +
prompt building) — no DB or network needed. Run from `backend/`: `uv run pytest`.

---

## Layering, in one sentence
`router` (HTTP only) → `service` (business logic: chunk/embed/retrieve/augment) →
`repository` (SQLAlchemy data access). Adding a feature means adding one method at
each layer — the same shape as the main course app.
