"use client";

import { useEffect, useState } from "react";
import { renderAnalysis } from "@/components/analysis/registry";
import { UploadPanel } from "@/components/UploadPanel";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { EmptyState, ErrorState, LoadingAnalysis } from "@/components/ui/States";
import { api, ApiError } from "@/lib/api";
import type {
  AnalysisResult,
  Capabilities,
  DocumentSummary,
  ModuleInfo,
} from "@/lib/types";

type Phase = "idle" | "uploading" | "analyzing" | "done";

export function Analyzer() {
  const [caps, setCaps] = useState<Capabilities | null>(null);
  const [modules, setModules] = useState<ModuleInfo[]>([]);
  const [bootError, setBootError] = useState<string | null>(null);

  const [file, setFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [moduleId, setModuleId] = useState("resume_analysis");

  const [doc, setDoc] = useState<DocumentSummary | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [error, setError] = useState<{ message: string; hint?: string } | null>(
    null,
  );

  // Ask the backend what it can do, rather than assuming. If the AI key is
  // missing we can say so up front instead of failing at the last click.
  useEffect(() => {
    let cancelled = false;
    Promise.all([api.capabilities(), api.modules()])
      .then(([capabilities, moduleList]) => {
        if (cancelled) return;
        setCaps(capabilities);
        setModules(moduleList);
        if (moduleList[0]) setModuleId(moduleList[0].id);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setBootError(
          err instanceof ApiError
            ? err.message
            : "Could not reach the Hirelens API.",
        );
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const activeModule = modules.find((m) => m.id === moduleId) ?? null;
  const needsJob = activeModule?.requires_job_description ?? false;
  const busy = phase === "uploading" || phase === "analyzing";
  const canRun =
    !!file && !busy && (!needsJob || jobDescription.trim().length > 0);

  async function run() {
    if (!file) return;
    setError(null);
    setResult(null);

    try {
      setPhase("uploading");
      const uploaded = await api.uploadDocument(file);
      setDoc(uploaded);

      setPhase("analyzing");
      const analysis = await api.runAnalysis(
        moduleId,
        uploaded.id,
        jobDescription,
      );
      setResult(analysis);
      setPhase("done");
    } catch (err: unknown) {
      setPhase("idle");
      if (err instanceof ApiError) {
        setError({ message: err.message, hint: hintFor(err.code, caps?.ai_provider) });
      } else {
        setError({ message: "An unexpected error occurred." });
      }
    }
  }

  if (bootError) {
    return (
      <ErrorState
        title="Backend not reachable"
        message={bootError}
        hint="Start the API by double-clicking run-backend.bat, then reload this page."
      />
    );
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,22rem)_minmax(0,1fr)] lg:items-start">
      {/* Controls ---------------------------------------------------------- */}
      <div className="space-y-4">
        <UploadPanel
          file={file}
          onFile={(next) => {
            setFile(next);
            setDoc(null);
            setResult(null);
            setPhase("idle");
            setError(null);
          }}
          document={doc}
          maxUploadMb={caps?.max_upload_mb ?? 10}
          allowedExtensions={caps?.allowed_extensions ?? [".pdf", ".docx", ".txt"]}
          disabled={busy}
        />

        <Card>
          <CardHeader
            title="Analysis"
            description={activeModule?.description}
          />
          <CardBody className="space-y-4">
            <div>
              <label
                htmlFor="module"
                className="mb-1.5 block text-xs font-medium text-muted"
              >
                Module
              </label>
              <select
                id="module"
                value={moduleId}
                disabled={busy || modules.length === 0}
                onChange={(e) => setModuleId(e.target.value)}
                className="w-full rounded-lg border bg-surface px-3 py-2 text-sm"
              >
                {modules.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.title}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label
                htmlFor="jd"
                className="mb-1.5 block text-xs font-medium text-muted"
              >
                Job description{" "}
                <span className="text-subtle">
                  {needsJob ? "(required)" : "(optional)"}
                </span>
              </label>
              <textarea
                id="jd"
                value={jobDescription}
                disabled={busy}
                onChange={(e) => setJobDescription(e.target.value)}
                rows={5}
                placeholder="Paste the job posting to sharpen the analysis."
                className="w-full resize-y rounded-lg border bg-surface px-3 py-2 text-sm placeholder:text-subtle"
              />
            </div>

            {caps && !caps.ai_enabled && (
              <p className="rounded-lg border border-warning/30 bg-warning/[0.07] px-3 py-2 text-sm text-muted">
                AI analysis is switched off on the server. Add{" "}
                <code className="text-xs">ANTHROPIC_API_KEY</code> to{" "}
                <code className="text-xs">backend/.env</code> and restart it.
                Uploading and parsing still work.
              </p>
            )}

            <Button
              onClick={run}
              disabled={!canRun}
              loading={busy}
              className="w-full"
            >
              {phase === "uploading"
                ? "Uploading…"
                : phase === "analyzing"
                  ? "Analyzing…"
                  : "Run analysis"}
            </Button>
          </CardBody>
        </Card>
      </div>

      {/* Results ----------------------------------------------------------- */}
      <div className="min-w-0 space-y-4">
        {error && (
          <ErrorState message={error.message} hint={error.hint} onRetry={run} />
        )}

        {phase === "analyzing" && (
          <LoadingAnalysis moduleTitle={activeModule?.title ?? "analysis"} />
        )}

        {phase === "done" && result && (
          <>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-subtle">
              <span>{activeModule?.title}</span>
              <span aria-hidden>·</span>
              <span>{(result.duration_ms / 1000).toFixed(1)}s</span>
              {result.cached && (
                <>
                  <span aria-hidden>·</span>
                  <span>served from cache</span>
                </>
              )}
            </div>
            {renderAnalysis(result.module_id, result.data)}
          </>
        )}

        {phase === "idle" && !error && (
          <Card>
            <EmptyState
              title="No analysis yet"
              description="Upload a resume and run an analysis. Results appear here."
            />
          </Card>
        )}
      </div>
    </div>
  );
}

/** Turn a backend error code into something the user can act on.
 *
 * The hint names the provider that is actually configured. Telling someone to
 * check their Anthropic billing while they are running on Gemini is worse than
 * saying nothing.
 */
function hintFor(code: string, provider?: string): string | undefined {
  const gemini = provider === "gemini";

  switch (code) {
    case "ai_unavailable":
      return gemini
        ? "Run set-gemini-key.bat to install a key, then restart the backend."
        : "Run set-api-key.bat to install a key, then restart the backend.";
    case "ai_credit_exhausted":
      return gemini
        ? "Check your quota at aistudio.google.com. Uploading and parsing keep working without it."
        : "Add credit at console.anthropic.com under Billing, then try again. Uploading and parsing keep working without it.";
    case "ai_auth_failed":
      return gemini
        ? "Run set-gemini-key.bat to install a fresh key, then restart the backend."
        : "Run set-api-key.bat to install a fresh key, then restart the backend.";
    case "ai_rate_limited":
      return gemini
        ? "The free tier has per-minute limits. Wait a minute and try again."
        : "Wait a few seconds and try again.";
    case "ai_overloaded":
      return "This is on the AI provider's side, not yours. It already retried a few times — try again in a moment.";
    case "ai_response_invalid":
      return "The AI's answer did not fit the expected shape, even after retries. Try again, or check the backend window for detail.";
    case "module_input_error":
      return "This analysis needs a job description. Paste one into the box on the left.";
    case "unsupported_file_type":
      return "Export your resume as a PDF, DOCX, or TXT file.";
    case "empty_document":
      return "Scanned or image-only PDFs have no extractable text. Export a text-based file instead.";
    case "file_too_large":
      return "Try compressing the PDF or exporting it without embedded images.";
    case "backend_unreachable":
      return "Double-click start-hirelens.bat, then try again.";
    default:
      return undefined;
  }
}
