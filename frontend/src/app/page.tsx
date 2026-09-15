import { Analyzer } from "@/components/Analyzer";
import { Logo } from "@/components/ui/Logo";

export default function DashboardPage() {
  return (
    <div className="min-h-dvh">
      <header className="border-b bg-surface/60 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
          <Logo />
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="rounded text-sm text-muted underline-offset-4 hover:text-fg hover:underline"
          >
            API docs
          </a>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold tracking-tight text-balance">
            Analyze a resume
          </h1>
          <p className="mt-1 text-sm text-muted">
            Upload a CV to get a scored quality review with prioritised,
            specific improvements.
          </p>
        </div>
        <Analyzer />
      </main>
    </div>
  );
}
