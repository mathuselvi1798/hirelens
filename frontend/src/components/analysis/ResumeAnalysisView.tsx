import { Badge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { ScoreBar, ScoreRing } from "@/components/ui/Score";
import type {
  Priority,
  ResumeAnalysis,
  Severity,
} from "@/lib/types";

const PRIORITY_TONE: Record<Priority, "danger" | "warning" | "accent" | "neutral"> = {
  critical: "danger",
  high: "warning",
  medium: "accent",
  low: "neutral",
};

const SEVERITY_TONE: Record<Severity, "danger" | "warning" | "neutral"> = {
  high: "danger",
  medium: "warning",
  low: "neutral",
};

const PRIORITY_ORDER: Record<Priority, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
};

export function ResumeAnalysisView({ data }: { data: ResumeAnalysis }) {
  const recommendations = [...data.recommendations].sort(
    (a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority],
  );

  return (
    <div className="space-y-4">
      {/* Headline result ------------------------------------------------- */}
      <Card>
        <CardBody className="flex flex-col gap-6 sm:flex-row sm:items-center">
          <ScoreRing score={data.overall_score} />
          <div className="min-w-0 flex-1">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <Badge tone="accent">
                {data.estimated_experience_level} level
              </Badge>
              {data.confidence !== "high" && (
                <Badge tone={data.confidence === "low" ? "warning" : "neutral"}>
                  {data.confidence} confidence
                </Badge>
              )}
            </div>
            <h2 className="text-lg font-semibold tracking-tight text-balance">
              {data.headline}
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-muted">
              {data.summary}
            </p>
            <div className="mt-5 grid gap-4 sm:grid-cols-3">
              <ScoreBar label="Clarity" score={data.clarity_score} />
              <ScoreBar label="Impact" score={data.impact_score} />
              <ScoreBar label="Structure" score={data.structure_score} />
            </div>
          </div>
        </CardBody>
      </Card>

      {data.confidence === "low" && (
        <p className="rounded-lg border border-warning/30 bg-warning/[0.07] px-4 py-3 text-sm text-muted">
          This analysis is marked <strong className="text-fg">low confidence</strong> —
          the extracted text was sparse or hard to read. Treat the scores as
          indicative, and try a text-based PDF or DOCX for a better result.
        </p>
      )}

      {/* Recommendations - the most actionable part, so it comes first ---- */}
      <Card>
        <CardHeader
          title="Prioritised improvements"
          description="Ordered by impact. Start at the top."
        />
        <CardBody className="space-y-3">
          {recommendations.map((rec, i) => (
            <div key={i} className="rounded-lg border bg-surface-2/50 p-4">
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <Badge tone={PRIORITY_TONE[rec.priority]}>{rec.priority}</Badge>
                <span className="text-xs font-medium text-subtle">{rec.area}</span>
              </div>
              <p className="text-sm font-medium">{rec.action}</p>
              <p className="mt-1 text-sm text-muted">{rec.rationale}</p>
              {rec.example && (
                <div className="mt-3 rounded-md border-l-2 border-accent bg-surface px-3 py-2">
                  <p className="text-[0.6875rem] font-semibold tracking-wide text-subtle uppercase">
                    Suggested rewrite
                  </p>
                  <p className="mt-1 text-sm">{rec.example}</p>
                </div>
              )}
            </div>
          ))}
        </CardBody>
      </Card>

      {/* Strengths and weaknesses ---------------------------------------- */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Strengths" />
          <CardBody className="space-y-3">
            {data.strengths.map((s, i) => (
              <div key={i} className="flex gap-3">
                <span
                  aria-hidden
                  className="mt-1.5 size-1.5 shrink-0 rounded-full bg-success"
                />
                <div className="min-w-0">
                  <p className="text-sm font-medium">{s.title}</p>
                  <p className="mt-0.5 text-sm text-muted">{s.detail}</p>
                </div>
              </div>
            ))}
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Weaknesses" />
          <CardBody className="space-y-3">
            {data.weaknesses.length === 0 && (
              <p className="text-sm text-muted">
                No significant weaknesses flagged.
              </p>
            )}
            {data.weaknesses.map((w, i) => (
              <div key={i} className="flex gap-3">
                <span
                  aria-hidden
                  className="mt-1.5 size-1.5 shrink-0 rounded-full"
                  style={{
                    background:
                      w.severity === "high"
                        ? "var(--danger)"
                        : w.severity === "medium"
                          ? "var(--warning)"
                          : "var(--fg-subtle)",
                  }}
                />
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-sm font-medium">{w.title}</p>
                    <Badge tone={SEVERITY_TONE[w.severity]}>{w.severity}</Badge>
                  </div>
                  <p className="mt-0.5 text-sm text-muted">{w.detail}</p>
                </div>
              </div>
            ))}
          </CardBody>
        </Card>
      </div>

      {/* Sections and skills --------------------------------------------- */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Section quality" />
          <CardBody className="space-y-4">
            {data.sections.map((section, i) => (
              <div key={i}>
                <ScoreBar
                  label={section.name}
                  score={section.present ? section.score : 0}
                />
                <p className="mt-1.5 text-sm text-muted">
                  {section.present ? section.comment : "Not found in the resume."}
                </p>
              </div>
            ))}
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Skills detected" />
          <CardBody className="space-y-4">
            {data.skills.length === 0 && (
              <p className="text-sm text-muted">No skill groups identified.</p>
            )}
            {data.skills.map((group, i) => (
              <div key={i}>
                <p className="mb-2 text-xs font-semibold tracking-wide text-subtle uppercase">
                  {group.category}
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {group.skills.map((skill) => (
                    <Badge key={skill}>{skill}</Badge>
                  ))}
                </div>
              </div>
            ))}
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
