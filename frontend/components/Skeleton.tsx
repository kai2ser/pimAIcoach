/**
 * Reusable skeleton loader components for perceived performance.
 */

export function SkeletonLine({ width = "100%" }: { width?: string }) {
  return (
    <div
      className="h-4 animate-pulse rounded bg-[var(--muted)]"
      style={{ width }}
    />
  );
}

export function SkeletonCard() {
  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--muted)]/40 p-5 space-y-3">
      <SkeletonLine width="40%" />
      <SkeletonLine width="70%" />
      <SkeletonLine width="55%" />
    </div>
  );
}

export function SkeletonGrid({ count = 3 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}
