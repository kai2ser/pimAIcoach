export default function AboutPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16">
      <h2 className="mb-6 text-3xl font-bold">About PIM AI Coach</h2>
      <p className="mb-4 text-[var(--muted-foreground)]">
        PIM AI Coach is an AI-powered coaching assistant for Public Investment
        Management. It leverages a Retrieval-Augmented Generation (RAG) pipeline
        to provide accurate, source-backed answers about international PIM best
        practices, national policies, and regulatory frameworks.
      </p>
      <p className="mb-4 text-[var(--muted-foreground)]">
        Built by{" "}
        <a
          href="https://pim-pam.net"
          className="underline hover:text-[var(--foreground)]"
          target="_blank"
          rel="noopener noreferrer"
        >
          PIM PAM
        </a>
        , this tool is designed to support practitioners, policymakers, and
        researchers working in public investment management across the globe.
      </p>
    </div>
  );
}
