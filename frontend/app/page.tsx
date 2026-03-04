import Link from "next/link";

export default function Home() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16 text-center">
      <h2 className="mb-4 text-3xl font-bold">PIM AI Coach</h2>
      <p className="mb-8 text-lg text-[var(--muted-foreground)]">
        An AI-powered coaching assistant for Public Investment Management.
        Ask questions about international PIM best practices, national policies,
        and regulatory frameworks.
      </p>
      <Link
        href="/coach"
        className="inline-block rounded-lg bg-[var(--primary)] px-6 py-3 text-sm font-medium text-[var(--primary-foreground)] hover:opacity-90"
      >
        Start a conversation
      </Link>

      <div className="mt-16 grid gap-6 text-left sm:grid-cols-2">
        <div className="rounded-lg border border-[var(--border)] p-5">
          <h3 className="mb-2 font-semibold">Policy Q&A</h3>
          <p className="text-sm text-[var(--muted-foreground)]">
            Ask questions about PIM legislation, regulations, and guidelines
            from countries worldwide.
          </p>
        </div>
        <div className="rounded-lg border border-[var(--border)] p-5">
          <h3 className="mb-2 font-semibold">Cross-Country Comparison</h3>
          <p className="text-sm text-[var(--muted-foreground)]">
            Compare PIM approaches across countries, tiers of guidance, and
            policy areas.
          </p>
        </div>
        <div className="rounded-lg border border-[var(--border)] p-5">
          <h3 className="mb-2 font-semibold">Best Practices</h3>
          <p className="text-sm text-[var(--muted-foreground)]">
            Learn about international good practices in public investment
            appraisal, selection, and monitoring.
          </p>
        </div>
        <div className="rounded-lg border border-[var(--border)] p-5">
          <h3 className="mb-2 font-semibold">Country PIM Profile</h3>
          <p className="text-sm text-[var(--muted-foreground)]">
            Generate a comprehensive 2-page institutional profile summarizing
            any country&apos;s PIM framework, policies, and reform priorities.
          </p>
          <Link
            href="/country-profile"
            className="mt-3 inline-block text-sm font-medium text-[var(--primary)] hover:underline"
          >
            Generate a profile &rarr;
          </Link>
        </div>
        <div className="rounded-lg border border-[var(--border)] p-5">
          <h3 className="mb-2 font-semibold">Country PIM Transparency</h3>
          <p className="text-sm text-[var(--muted-foreground)]">
            Generate a transparency briefing with policy repository document
            listings, tier classifications, and completeness analysis.
          </p>
          <Link
            href="/country-transparency"
            className="mt-3 inline-block text-sm font-medium text-emerald-600 hover:underline"
          >
            Generate a briefing &rarr;
          </Link>
        </div>
      </div>
    </div>
  );
}
