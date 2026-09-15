import { ATSAnalysisView } from "./ATSAnalysisView";
import { CareerIntelligenceView } from "./CareerIntelligenceView";
import { JobMatchView } from "./JobMatchView";
import { ResumeAnalysisView } from "./ResumeAnalysisView";
import type {
  ATSAnalysis,
  CareerIntelligence,
  JobMatch,
  ResumeAnalysis,
} from "@/lib/types";

/**
 * The frontend half of the module registry.
 *
 * The backend decides which analyses exist; this maps each module id to the
 * component that renders its result. Adding a module means adding one view
 * file and one line here - no change to the page, the API client, or the
 * layout.
 *
 * The `any` below is deliberate and contained: at this exact point the data
 * genuinely is of unknown shape, because the module id is only known at
 * runtime. Each renderer immediately narrows it to its own typed model, so
 * everything downstream is fully typed.
 */
type Renderer = (data: any) => React.ReactNode;

const RENDERERS: Record<string, Renderer> = {
  resume_analysis: (data: ResumeAnalysis) => <ResumeAnalysisView data={data} />,
  job_match: (data: JobMatch) => <JobMatchView data={data} />,
  ats_analysis: (data: ATSAnalysis) => <ATSAnalysisView data={data} />,
  career_intelligence: (data: CareerIntelligence) => (
    <CareerIntelligenceView data={data} />
  ),
};

export function renderAnalysis(moduleId: string, data: unknown) {
  const render = RENDERERS[moduleId];

  // A module the backend offers but the UI has no view for yet: show the raw
  // result rather than an error. New backend modules stay usable immediately.
  if (!render) {
    return (
      <div className="rounded-[var(--radius-card)] border bg-surface p-5">
        <p className="mb-3 text-sm text-muted">
          No custom view for <code className="text-xs">{moduleId}</code> yet —
          showing the raw result.
        </p>
        <pre className="overflow-x-auto rounded-lg border bg-surface-2 p-4 text-xs">
          {JSON.stringify(data, null, 2)}
        </pre>
      </div>
    );
  }

  return render(data);
}
