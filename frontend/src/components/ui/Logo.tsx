/**
 * The Hirelens mark.
 *
 * Drawn in code rather than loaded as an image: nothing to 404, nothing to
 * optimise, and it inherits the theme's accent colour automatically. Kept in
 * its own component so rebranding again means editing one file.
 */
import { cn } from "@/lib/cn";

export function LogoMark({
  size = 32,
  className,
}: {
  size?: number;
  className?: string;
}) {
  return (
    <span
      aria-hidden
      className={cn(
        "grid shrink-0 place-items-center rounded-lg bg-accent",
        "font-bold tracking-tight text-on-accent",
        className,
      )}
      style={{ width: size, height: size, fontSize: size * 0.46 }}
    >
      H
    </span>
  );
}

export function Logo({ size = 32 }: { size?: number }) {
  return (
    <div className="flex items-center gap-2.5">
      <LogoMark size={size} />
      <div>
        <p className="text-sm font-semibold tracking-tight">Hirelens</p>
        <p className="text-xs text-subtle">Career Intelligence</p>
      </div>
    </div>
  );
}
