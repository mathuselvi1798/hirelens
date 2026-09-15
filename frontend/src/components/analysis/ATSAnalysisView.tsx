import { Badge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { ScoreBar, ScoreRing } from "@/components/ui/Score";
import type { ATSAnalysis, Severity } from "@/lib/types";

const RISK_TONE: Record<ATSAnalysis["parse_risk"], "success" | "warning" | "danger"> = {
  low: "success",
  medium: "warning",
  high: "danger",
};

const SEVERITY_TONE: Record<Severity, "danger" | "warning" | "neutral"> = {
  high: "danger",
  medium: "warning",
  low: "neutral",
};

const SEVERITY_ORDER: Record<Severity, number> = { high: 0, medium: 1, low: 2 };

export function ATSAnalysisView({ data }: { data: ATSAnalysis }) {
  const issues = [...data.issues].sort(
    (a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity],
  );

  const areas = [
    { label: "Formatting", area: data.formatting },
    { label: "Sections", area: data.sections },
    { label: "Keywords", area: data.keywords },
    { label: "Readability", area: data.readability },
  ];

  return (
    <div className="space-y-4">
      <Card>
        <CardBody className="flex flex-col gap-6 sm:flex-row sm:items-center">
          <ScoreRing score={data.ats_score} label="ATS" />
          <div className="min-w-0 flex-1">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <Badge tone={RISK_TONE[data.parse_risk]}>
                {data.parse_risk} parse risk
              </Badge>
              {data.confidence !== "high" && (
                <Badge tone="neutral">{data.confidence} confidence</Badge>
              )}
            </div>
            <h2 className="text-lg font-semibold tracking-tight text-balance">
              {data.headline}
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-muted">{data.summary}</p>
            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              {areas.map(({ label, area }) => (
                <ScoreBar key={label} label={label} score={area.score} />
              ))}
            </div>
          </div>
        </CardBody>
      </Card>

      {issues.length > 0 && (
        <Card>
          <CardHeader
            title="Parsing risks"
            description="Ordered by severity. Fix the top ones first."
          />
          <CardBody className="space-y-3">
            {issues.map((issue, i) => (
              <div key={i} className="rounded-lg border bg-surface-2/50 p-4">
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <Badge tone={SEVERITY_TONE[issue.severity]}>{issue.severity}</Badge>
                  <span className="text-xs font-medium text-subtle">{issue.area}</span>
                </div>
                <p className="text-sm font-medium">{issue.issue}</p>
                <div className="mt-2 rounded-md border-l-2 border-accent bg-surface px-3 py-2">
                  <p className="text-[0.6875rem] font-semibold tracking-wide text-subtle uppercase">
                    Fix
                  </p>
                  <p className="mt-1 text-sm">{issue.fix}</p>
                </div>
              </div>
            ))}
          </CardBody>
        </Card>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Area detail" />
          <CardBody className="space-y-4">
            {areas.map(({ label, area }) => (
              <div key={label}>
                <ScoreBar label={label} score={area.score} />
                <p className="mt-1.5 text-sm text-muted">{area.comment}</p>
              </div>
            ))}
          </CardBody>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader title="Sections not found" />
            <CardBody>
              <div className="flex flex-wrap gap-1.5">
                {data.missing_sections.map((s) => (
                  <Badge key={s} tone="warning">{s}</Badge>
                ))}
                {data.missing_sections.length === 0 && (
                  <p className="text-sm text-muted">All standard sections detected.</p>
                )}
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader
              title="Keywords worth adding"
              description="Only if you genuinely have the experience"
            />
            <CardBody>
              <div className="flex flex-wrap gap-1.5">
                {data.suggested_keywords.map((k) => (
                  <Badge key={k} tone="accent">{k}</Badge>
                ))}
                {data.suggested_keywords.length === 0 && (
                  <p className="text-sm text-muted">No additions suggested.</p>
                )}
              </div>
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
}
