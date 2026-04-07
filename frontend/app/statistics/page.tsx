"use client";

import dynamic from "next/dynamic";

/**
 * Lazy-load the statistics page content (includes Recharts ~170KB).
 * This prevents the charting library from being included in the shared
 * JS bundle that loads on every page.
 */
const StatisticsContent = dynamic(() => import("./StatisticsContent"), {
  loading: () => (
    <div className="mx-auto max-w-5xl px-4 py-16">
      <h2 className="mb-6 text-3xl font-bold">Vector Database Analytics</h2>
      <div className="flex items-center gap-2 text-sm text-[var(--muted-foreground)]">
        <svg className="h-4 w-4 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" aria-hidden="true">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        Loading statistics&hellip;
      </div>
    </div>
  ),
  ssr: false,
});

export default function StatisticsPage() {
  return <StatisticsContent />;
}
