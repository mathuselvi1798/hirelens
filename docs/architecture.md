# Architecture

## Layers

```
HTTP  →  app/api/v1/routes/     thin: read request, call service, shape response
         app/documents/         ingestion: validate → extract → structure → store
         app/analysis/          registry + service: pick a module, run it
         app/ai/                provider interface, validation, retry, cache
         app/core/              config, logging, exceptions
```

**Dependency direction is one-way.** Routes may import services; services never
import routes. Nothing outside `app/core/config.py` reads environment
variables. Nothing outside `app/ai/` imports a vendor SDK.

## Key decisions and their reasons

### 1. Analysis modules are registered, not routed
Twelve planned analysis types make per-endpoint implementations untenable. A
module registers itself at import time; one generic endpoint serves all of
them, and `GET /analysis/modules` lets the frontend build its UI from whatever
is registered. Cost of module #12 ≈ cost of module #2.

### 2. Parse once into a CanonicalDocument
Extraction is the slowest non-AI step and the biggest source of quality
variance. Doing it once, deterministically, and handing modules labelled
sections and clean bullets produces far more consistent AI output than pasting
raw text into every prompt.

### 3. Structured output via forced tool use
The model must call a tool whose input schema is our Pydantic schema. This
eliminates JSON-scraping bugs entirely. Field descriptions in the schema are
prompt engineering — the model reads them.

### 4. Validation is a gate, not a formality
An invalid response is fed back to the model with its own validation errors
and retried. Only persistent failure becomes an error. The UI can therefore
assume every result it receives is well-formed.

### 5. Cache on content, not on request
Key = `(content hash, module id, prompt version, extra inputs)`. Re-analyzing
an unchanged document is free. Bumping `prompt_version` invalidates that
module's cache automatically while iterating on a prompt.

### 6. Storage behind a protocol
`DocumentStore` is a `Protocol` with an in-memory implementation today.
Phase 4 adds `PostgresDocumentStore` and changes one function. Callers never
learn the difference. This is why the database could safely be deferred until
the result shapes were known rather than guessed.

### 7. Errors are domain objects
Business code raises `NexaError` subclasses; only the API layer turns them
into responses. Services stay usable from workers, CLIs, and tests, and the
frontend gets one predictable error envelope.

## Adding a new analysis module

1. Create `backend/app/analysis/modules/<name>/`
2. `schema.py` — a Pydantic model with tight constraints and rich `description=`
3. `prompt.py` — `SYSTEM` and `build_user_prompt(ctx)`
4. `module.py` — subclass `AnalysisModule`, decorate with `@register`
5. `__init__.py` — import the module class so registration fires
6. Add a renderer in `frontend/src/components/analysis/`

No other file changes.

## Deferred deliberately

Redis, Celery, Docker Compose, and microservices are all real answers to
problems this application does not yet have. Async job processing has a
reserved seam (Phase 9): `run_analysis` is already a pure function of
`(module_id, context)`, so moving it behind a queue does not change its
callers.
