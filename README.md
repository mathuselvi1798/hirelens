# Hirelens

See your resume the way recruiters and applicant tracking systems do.

Upload a CV and Hirelens returns a structured, schema-validated analysis:
a scored quality review, a match score against a specific job posting, an
ATS-readiness assessment, and a realistic career roadmap.

Runs on a free API tier. No paid account required.

> **Status:** Phase 3 of 10. The backend analysis engine is complete and tested.
> The Next.js frontend and PostgreSQL persistence follow.

---

## Why the architecture looks like this

The product's defining requirement is that new AI analysis types can be added
without rewriting the application. So an analysis is a **registered module**,
not an endpoint:

```
Upload → parse once → CanonicalDocument → [ module registry ] → validated result → render
```

A module declares five things and nothing more:

| Declares | Where |
|---|---|
| identity (`id`, `version`, `title`) | `module.py` |
| input contract (needs a job description?) | `module.py` |
| output schema (a Pydantic model) | `schema.py` |
| prompt (versioned) | `prompt.py` |
| frontend renderer | `frontend/src/components/analysis/` |

Everything else — calling the model, enforcing the schema, retrying on
invalid output, caching, error handling, logging — lives once in shared
infrastructure. Adding "Interview Questions" later means adding one package
under `backend/app/analysis/modules/`. No route, no database migration, no
change to the AI layer.

Two supporting rules keep that true:

- **Parse once.** Files become a `CanonicalDocument` (text + detected sections
  + bullets + contact). Modules consume that structure, never the raw upload.
  Ten analyses of one resume cost one parse.
- **AI output is untrusted input.** Every response is validated against a
  Pydantic schema before it can reach the UI. Invalid output triggers an
  informed retry; persistently invalid output becomes a handled error, never a
  broken dashboard.

## Project structure

```
hirelens/
├── backend/
│   ├── app/
│   │   ├── main.py               app factory
│   │   ├── core/                 config, logging, exceptions
│   │   ├── api/v1/routes/        thin HTTP layer, no business logic
│   │   ├── schemas/              API contracts (≠ future DB models)
│   │   ├── documents/            extraction, structure detection, store
│   │   ├── ai/                   provider interface, client, cache
│   │   └── analysis/             base, registry, service, modules/
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── frontend/                     Next.js + TypeScript + Tailwind (Phase 5)
└── docs/architecture.md
```

## Running the backend

Requires **Python 3.11+**.

```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1      # Windows PowerShell
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
copy .env.example .env          # Windows;  cp .env.example .env elsewhere
uvicorn app.main:app --reload --port 8000
```

- API root: <http://localhost:8000>
- Interactive docs: <http://localhost:8000/docs>
- Health: <http://localhost:8000/api/v1/health>

The server runs **without an API key**. Uploading and parsing work fully; only
AI-backed analysis returns a clear `503` until a key is set.

### Enabling AI analysis

1. Get a key from the Anthropic Console.
2. Put it in `backend/.env` as `ANTHROPIC_API_KEY=sk-ant-...`.
3. Restart the server. `GET /api/v1/health/capabilities` should now report
   `"ai_enabled": true`.

## Tests

```bash
cd backend
pytest -v
```

The suite runs with no API key and makes no network calls — the AI provider
interface is replaced with a fake, so the full analysis engine (validation,
retry, caching) is exercised for free.

## API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/health` | Liveness |
| `GET` | `/api/v1/health/capabilities` | What this server can do |
| `POST` | `/api/v1/documents` | Upload a resume (PDF/DOCX/TXT) |
| `GET` | `/api/v1/documents` | Recent documents |
| `GET` | `/api/v1/documents/{id}` | One document |
| `GET` | `/api/v1/analysis/modules` | Every registered module |
| `POST` | `/api/v1/analysis/{module_id}/run` | Run an analysis |

Errors always use one envelope:

```json
{ "error": { "code": "unsupported_file_type", "message": "...", "details": {} } }
```

## Security

- Secrets live only in `.env`, which is git-ignored. Nothing is hardcoded.
- Uploads are validated for extension and size before any parsing happens.
- The API key never reaches the frontend; all model calls are server-side.
- Unhandled exceptions return a generic message; details go to logs only.
- `/docs` is disabled automatically when `ENVIRONMENT=production`.

## Roadmap

| Phase | Scope | Status |
|---|---|---|
| 1 | Core config, logging, errors | done |
| 2 | Document pipeline | done |
| 3 | Module registry, AI layer, Resume Analysis | done |
| 4 | PostgreSQL + Alembic | next |
| 5 | Next.js frontend foundation | next |
| 6 | Upload → analyze → render vertical slice | |
| 7 | Job Match, ATS, Career Intelligence modules | |
| 8 | Authentication, per-user history | |
| 9 | Async jobs, rate limiting | |
| 10 | Hardening, deployment | |
