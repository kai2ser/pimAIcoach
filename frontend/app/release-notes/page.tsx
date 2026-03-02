export default function ReleaseNotesPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16">
      <h2 className="mb-8 text-3xl font-bold">Release Notes</h2>

      <article className="mb-8 rounded-lg border border-[var(--border)] p-6">
        <div className="mb-2 flex items-center gap-3">
          <h3 className="text-xl font-semibold">v0.1.0</h3>
          <span className="rounded-full bg-[var(--muted)] px-2.5 py-0.5 text-xs text-[var(--muted-foreground)]">
            Initial Release
          </span>
        </div>
        <p className="mb-3 text-sm text-[var(--muted-foreground)]">
          March 2026
        </p>
        <ul className="list-inside list-disc space-y-1 text-[var(--muted-foreground)]">
          <li>RAG-powered Q&amp;A for Public Investment Management</li>
          <li>Real-time streaming responses</li>
          <li>Metadata filtering by country, year, and document type</li>
          <li>Source citations with retrieved document excerpts</li>
          <li>API key authentication for admin and ingestion endpoints</li>
        </ul>
      </article>
    </div>
  );
}
