import { Button } from "./Button";
import { Card, CardBody } from "./Card";

/**
 * Loading, empty, and error states as first-class components.
 *
 * Building these up front - rather than after the happy path "works" - is what
 * stops an app from feeling like a demo. Most of a user's time is spent in one
 * of these three states.
 */

export function LoadingAnalysis({ moduleTitle }: { moduleTitle: string }) {
  return (
    <Card>
      <CardBody className="space-y-5">
        <div className="flex items-center gap-4">
          <div className="shimmer size-32 rounded-full bg-surface-2" />
          <div className="flex-1 space-y-2.5">
            <div className="shimmer h-4 w-2/3 rounded bg-surface-2" />
            <div className="shimmer h-3 w-full rounded bg-surface-2" />
            <div className="shimmer h-3 w-4/5 rounded bg-surface-2" />
          </div>
        </div>
        <div className="grid gap-3 sm:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <div key={i} className="shimmer h-10 rounded bg-surface-2" />
          ))}
        </div>
        <p className="text-center text-sm text-muted">
          Running {moduleTitle}. This usually takes 10&ndash;25 seconds.
        </p>
      </CardBody>
    </Card>
  );
}

export function EmptyState({
  title,
  description,
  icon,
}: {
  title: string;
  description: string;
  icon?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-14 text-center">
      {icon && <div className="mb-3 text-subtle">{icon}</div>}
      <h3 className="text-sm font-semibold">{title}</h3>
      <p className="mt-1 max-w-sm text-sm text-muted">{description}</p>
    </div>
  );
}

export function ErrorState({
  title = "Something went wrong",
  message,
  hint,
  onRetry,
}: {
  title?: string;
  message: string;
  hint?: string;
  onRetry?: () => void;
}) {
  return (
    <div
      role="alert"
      className="rounded-[var(--radius-card)] border border-danger/30 bg-danger/[0.06] p-5"
    >
      <h3 className="text-sm font-semibold text-danger">{title}</h3>
      <p className="mt-1 text-sm text-fg">{message}</p>
      {hint && <p className="mt-2 text-sm text-muted">{hint}</p>}
      {onRetry && (
        <Button variant="secondary" className="mt-4" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}
