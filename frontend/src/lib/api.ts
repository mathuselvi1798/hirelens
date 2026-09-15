import type {
  AnalysisResult,
  ApiErrorBody,
  Capabilities,
  DocumentSummary,
  ModuleInfo,
} from "./types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ??
  "http://localhost:8000";

/**
 * An error carrying the backend's structured error code.
 *
 * Because the API always returns one error envelope, the UI can branch on
 * `code` instead of parsing message strings.
 */
export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly details: Record<string, unknown>;

  constructor(message: string, code: string, status: number, details = {}) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

async function handle<T>(response: Response): Promise<T> {
  if (response.ok) return (await response.json()) as T;

  let code = "unknown_error";
  let message = `Request failed (${response.status}).`;
  let details: Record<string, unknown> = {};

  try {
    const body = (await response.json()) as Partial<ApiErrorBody>;
    if (body?.error) {
      code = body.error.code ?? code;
      message = body.error.message ?? message;
      details = body.error.details ?? {};
    }
  } catch {
    // Non-JSON error body - keep the generic message.
  }

  throw new ApiError(message, code, response.status, details);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, init);
  } catch {
    // fetch only rejects on network-level failure, which here almost always
    // means the backend is not running. Say that, rather than "failed to fetch".
    throw new ApiError(
      "Cannot reach the NEXA API. Make sure the backend is running on port 8000.",
      "backend_unreachable",
      0,
    );
  }
  return handle<T>(response);
}

export const api = {
  capabilities: () => request<Capabilities>("/api/v1/health/capabilities"),

  modules: () => request<ModuleInfo[]>("/api/v1/analysis/modules"),

  uploadDocument: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<DocumentSummary>("/api/v1/documents", {
      method: "POST",
      body: form,
    });
  },

  runAnalysis: <T>(
    moduleId: string,
    documentId: string,
    jobDescription?: string,
  ) =>
    request<AnalysisResult<T>>(`/api/v1/analysis/${moduleId}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        document_id: documentId,
        job_description: jobDescription?.trim() || null,
      }),
    }),
};
