# Hirelens frontend — Phase 5

Next.js 15 (App Router) + TypeScript + Tailwind v4. No UI-kit dependency: the
component layer is owned by this project, so the visual language can evolve
without fighting a vendor's defaults.

## Setup (Windows)

1. Make sure this `frontend` folder sits next to `backend` inside
   `nexa-ai-analyzer`.
2. Double-click **`setup-frontend.bat`** — installs dependencies, then
   typechecks.
3. Double-click **`run-frontend.bat`** — starts the app on
   <http://localhost:3000>.

The **backend must also be running** (`run-backend.bat`), because the app asks
it what it can do on load.

## What it does without an API key

Upload and parsing work fully — you'll see word count, detected sections,
bullet count, and contact detection. The "Run analysis" button returns a clear
message telling you the key is missing, rather than failing silently.

## Structure

```
src/
├── app/
│   ├── layout.tsx        root shell
│   ├── page.tsx          dashboard
│   └── globals.css       design tokens (light + dark)
├── lib/
│   ├── api.ts            typed client; one error envelope
│   ├── types.ts          mirrors the backend Pydantic schemas
│   └── cn.ts             class merging
└── components/
    ├── Analyzer.tsx      orchestration + all UI states
    ├── UploadPanel.tsx   drag & drop, parse summary
    ├── ui/               Button, Card, Badge, Score, States
    └── analysis/
        ├── registry.tsx  module id -> renderer  (the extension point)
        └── ResumeAnalysisView.tsx
```

## Adding a module's view later

1. Create `components/analysis/<Name>View.tsx`
2. Add its result type to `lib/types.ts`
3. Add one line to `RENDERERS` in `registry.tsx`

Until you do, any new backend module still works — the registry falls back to
showing its raw validated result.

## Notes

- Dark mode follows the OS setting; no toggle, no flash.
- Loading, empty, and error states were built first, not bolted on.
- `NEXT_PUBLIC_API_BASE_URL` defaults to `http://localhost:8000`. Anything
  prefixed `NEXT_PUBLIC_` is visible in the browser — never put a secret there.
