import { Badge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { ScoreBar, ScoreRing } from "@/components/ui/Score";
import type { CareerIntelligence, NextAction, Priority } from "@/lib/types";

const PRIORITY_TONE: Record<Priority, "danger" | "warning" | "accent" | "neutral"> = {
  critical: "danger",
  high: "warning",
  medium: "accent",
  low: "neutral",
};

const PRIORITY_ORDER: Record<Priority, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
};

const TIMEFRAME_LABEL: Record<NextAction["timeframe"], string> = {
  this_week: "This week",
  this_month: "This month",
  this_quarter: "This quarter",
};

const TIMEFRAME_ORDER: Record<NextAction["timeframe"], number> = {
  this_week: 0,
  this_month: 1,
  this_quarter: 2,
};

export function CareerIntelligenceView({ data }: { data: CareerIntelligence }) {
  const gaps = [...data.skill_gaps].sort(
    (a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority],
  );
  const roadmap = [...data.learning_roadmap].sort((a, b) => a.step - b.step);
  const actions = [...data.next_actions].sort(
    (a, b) => TIMEFRAME_ORDER[a.timeframe] - TIMEFRAME_ORDER[b.timeframe],
  );
  const totalWeeks = roadmap.reduce((sum, s) => sum + s.estimated_weeks, 0);

  return (
    <div className="space-y-4">
      <Card>
        <CardBody className="flex flex-col gap-6 sm:flex-row sm:items-center">
          <ScoreRing score={data.readiness_score} label="Readiness" />
          <div className="min-w-0 flex-1">
            {data.confidence !== "high" && (
              <Badge tone="neutral" className="mb-2">
                {data.confidence} confidence
              </Badge>
            )}
            <h2 className="text-lg font-semibold tracking-tight text-balance">
              {data.headline}
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-muted">
              {data.current_positioning}
            </p>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader
          title="Roles within reach"
          description="Realistic in the next 6–12 months"
        />
        <CardBody className="space-y-3">
          {data.recommended_roles.map((role, i) => (
            <div key={i} className="rounded-lg border bg-surface-2/50 p-4">
              <div className="mb-2 flex items-start justify-between gap-4">
                <h3 className="text-sm font-semibold">{role.title}</h3>
                <div className="w-24 shrink-0">
                  <ScoreBar label="Fit" score={role.fit_score} />
                </div>
              </div>
              <p className="text-sm text-muted">{role.why}</p>
              <p className="mt-2 text-sm">
                <span className="text-subtle">Gap to close: </span>
                {role.gap_to_close}
              </p>
            </div>
          ))}
        </CardBody>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Skill gaps" description="Highest priority first" />
          <CardBody className="space-y-3">
            {gaps.length === 0 && <p className="text-sm text-muted">No major gaps identified.</p>}
            {gaps.map((gap, i) => (
              <div key={i}>
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-sm font-medium">{gap.skill}</p>
                  <Badge tone={PRIORITY_TONE[gap.priority]}>{gap.priority}</Badge>
                </div>
                <p className="mt-0.5 text-sm text-muted">{gap.why_it_matters}</p>
              </div>
            ))}
          </CardBody>
        </Card>

        <Card>
          <CardHeader
            title="Next actions"
            description="Start at the top"
          />
          <CardBody className="space-y-3">
            {actions.map((action, i) => (
              <div key={i} className="flex gap-3">
                <Badge tone={action.timeframe === "this_week" ? "accent" : "neutral"}>
                  {TIMEFRAME_LABEL[action.timeframe]}
                </Badge>
                <p className="min-w-0 flex-1 text-sm">{action.action}</p>
              </div>
            ))}
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader
          title="Learning roadmap"
          description={`${roadmap.length} steps · about ${totalWeeks} weeks total`}
        />
        <CardBody>
          <ol className="relative space-y-5 border-l pl-6">
            {roadmap.map((step) => (
              <li key={step.step} className="relative">
                <span
                  aria-hidden
                  className="absolute -left-[1.9rem] grid size-6 place-items-center rounded-full bg-accent text-[0.6875rem] font-bold text-on-accent"
                >
                  {step.step}
                </span>
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="text-sm font-semibold">{step.focus}</h3>
                  <Badge tone="neutral">
                    ~{step.estimated_weeks} {step.estimated_weeks === 1 ? "week" : "weeks"}
                  </Badge>
                </div>
                <p className="mt-1 text-sm text-muted">{step.outcome}</p>
              </li>
            ))}
          </ol>
        </CardBody>
      </Card>
    </div>
  );
}
