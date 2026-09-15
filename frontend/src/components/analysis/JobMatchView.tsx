import { Badge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { ScoreBar, ScoreRing } from "@/components/ui/Score";
import type { Importance, JobMatch } from "@/lib/types";

const VERDICT_LABEL: Record<JobMatch["verdict"], string> = {
  strong_match: "Strong match",
  good_match: "Good match",
  partial_match: "Partial match",
  weak_match: "Weak match",
};

const VERDICT_TONE: Record<JobMatch["verdict"], "success" | "accent" | "warning" | "danger"> = {
  strong_match: "success",
  good_match: "accent",
  partial_match: "warning",
  weak_match: "danger",
};

const APPLY_LABEL: Record<JobMatch["should_apply"], string> = {
  yes: "Apply",
  yes_with_changes: "Apply after edits",
  probably_not: "Probably not this one",
};

const APPLY_TONE: Record<JobMatch["should_apply"], "success" | "warning" | "danger"> = {
  yes: "success",
  yes_with_changes: "warning",
  probably_not: "danger",
};

const IMPORTANCE_TONE: Record<Importance, "danger" | "warning" | "neutral"> = {
  critical: "danger",
  important: "warning",
  nice_to_have: "neutral",
};

const IMPORTANCE_ORDER: Record<Importance, number> = {
  critical: 0,
  important: 1,
  nice_to_have: 2,
};

export function JobMatchView({ data }: { data: JobMatch }) {
  const missing = [...data.missing_skills].sort(
    (a, b) => IMPORTANCE_ORDER[a.importance] - IMPORTANCE_ORDER[b.importance],
  );

  return (
    <div className="space-y-4">
      <Card>
        <CardBody className="flex flex-col gap-6 sm:flex-row sm:items-center">
          <ScoreRing score={data.match_score} label="Match" />
          <div className="min-w-0 flex-1">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <Badge tone={VERDICT_TONE[data.verdict]}>{VERDICT_LABEL[data.verdict]}</Badge>
              <Badge tone={APPLY_TONE[data.should_apply]}>{APPLY_LABEL[data.should_apply]}</Badge>
              {data.confidence !== "high" && (
                <Badge tone="neutral">{data.confidence} confidence</Badge>
              )}
            </div>
            <h2 className="text-lg font-semibold tracking-tight text-balance">
              {data.headline}
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-muted">{data.summary}</p>
            <div className="mt-5">
              <ScoreBar label="Keyword coverage" score={data.keyword_coverage.score} />
            </div>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader
          title="Experience alignment"
          aside={
            <Badge tone={data.experience_alignment.aligned ? "success" : "warning"}>
              {data.experience_alignment.aligned ? "aligned" : "mismatch"}
            </Badge>
          }
        />
        <CardBody className="space-y-3">
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-lg border bg-surface-2/50 p-3">
              <p className="text-xs font-medium text-subtle">Posting asks for</p>
              <p className="mt-0.5 text-sm font-medium">{data.experience_alignment.required}</p>
            </div>
            <div className="rounded-lg border bg-surface-2/50 p-3">
              <p className="text-xs font-medium text-subtle">Resume shows</p>
              <p className="mt-0.5 text-sm font-medium">{data.experience_alignment.candidate}</p>
            </div>
          </div>
          <p className="text-sm text-muted">{data.experience_alignment.comment}</p>
        </CardBody>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="What matches" description="Backed by the resume" />
          <CardBody className="space-y-3">
            {data.matching_skills.length === 0 && (
              <p className="text-sm text-muted">No clear matches found.</p>
            )}
            {data.matching_skills.map((s, i) => (
              <div key={i} className="flex gap-3">
                <span aria-hidden className="mt-1.5 size-1.5 shrink-0 rounded-full bg-success" />
                <div className="min-w-0">
                  <p className="text-sm font-medium">{s.skill}</p>
                  <p className="mt-0.5 text-sm text-muted">{s.evidence}</p>
                </div>
              </div>
            ))}
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="What's missing" description="Most damaging first" />
          <CardBody className="space-y-3">
            {missing.length === 0 && (
              <p className="text-sm text-muted">Nothing significant missing.</p>
            )}
            {missing.map((s, i) => (
              <div key={i} className="rounded-lg border bg-surface-2/50 p-3">
                <div className="mb-1 flex flex-wrap items-center gap-2">
                  <p className="text-sm font-medium">{s.skill}</p>
                  <Badge tone={IMPORTANCE_TONE[s.importance]}>
                    {s.importance.replace(/_/g, " ")}
                  </Badge>
                </div>
                <p className="text-sm text-muted">{s.how_to_address}</p>
              </div>
            ))}
          </CardBody>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Keywords covered" />
          <CardBody>
            <div className="flex flex-wrap gap-1.5">
              {data.keyword_coverage.covered.map((k) => (
                <Badge key={k} tone="success">{k}</Badge>
              ))}
              {data.keyword_coverage.covered.length === 0 && (
                <p className="text-sm text-muted">None found.</p>
              )}
            </div>
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Keywords missing" />
          <CardBody>
            <div className="flex flex-wrap gap-1.5">
              {data.keyword_coverage.missing.map((k) => (
                <Badge key={k} tone="danger">{k}</Badge>
              ))}
              {data.keyword_coverage.missing.length === 0 && (
                <p className="text-sm text-muted">Full coverage.</p>
              )}
            </div>
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader
          title="To improve this match"
          description="Changes specific to this posting"
        />
        <CardBody className="space-y-2.5">
          {data.recommendations.map((r, i) => (
            <div key={i} className="flex gap-3">
              <span className="text-xs font-semibold text-subtle tabular-nums">
                {String(i + 1).padStart(2, "0")}
              </span>
              <p className="text-sm">{r}</p>
            </div>
          ))}
        </CardBody>
      </Card>
    </div>
  );
}
