import { cn } from "@/lib/cn";

/** Scores share one colour rule across the whole product, defined once here. */
export function scoreTone(score: number): "success" | "warning" | "danger" {
  if (score >= 75) return "success";
  if (score >= 50) return "warning";
  return "danger";
}

const TONE_VAR = {
  success: "var(--success)",
  warning: "var(--warning)",
  danger: "var(--danger)",
} as const;

/**
 * Radial score gauge drawn as SVG.
 *
 * Hand-drawn rather than pulled from a charting library: it is one arc, and a
 * dependency that renders one arc is a dependency that also breaks builds.
 */
export function ScoreRing({
  score,
  size = 128,
  label = "Overall",
}: {
  score: number;
  size?: number;
  label?: string;
}) {
  const stroke = size * 0.085;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(100, score));
  const color = TONE_VAR[scoreTone(clamped)];

  return (
    <div
      className="relative shrink-0"
      style={{ width: size, height: size }}
      role="img"
      aria-label={`${label} score: ${clamped} out of 100`}
    >
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={stroke}
          stroke="var(--border)"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={stroke}
          stroke={color}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference * (1 - clamped / 100)}
          style={{ transition: "stroke-dashoffset 700ms ease-out" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span
          className="font-semibold tabular-nums"
          style={{ fontSize: size * 0.26, color }}
        >
          {clamped}
        </span>
        <span className="text-[0.6875rem] text-subtle">{label}</span>
      </div>
    </div>
  );
}

/** Horizontal score bar, for the secondary metrics. */
export function ScoreBar({
  label,
  score,
  className,
}: {
  label: string;
  score: number;
  className?: string;
}) {
  const clamped = Math.max(0, Math.min(100, score));
  return (
    <div className={cn("min-w-0", className)}>
      <div className="mb-1.5 flex items-baseline justify-between gap-2">
        <span className="truncate text-xs font-medium text-muted">{label}</span>
        <span className="text-xs font-semibold tabular-nums">{clamped}</span>
      </div>
      <div
        className="h-1.5 w-full overflow-hidden rounded-full bg-surface-2"
        role="img"
        aria-label={`${label}: ${clamped} out of 100`}
      >
        <div
          className="h-full rounded-full"
          style={{
            width: `${clamped}%`,
            background: TONE_VAR[scoreTone(clamped)],
            transition: "width 700ms ease-out",
          }}
        />
      </div>
    </div>
  );
}
