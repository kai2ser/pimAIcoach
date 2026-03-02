import Image from "next/image";

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
        The focus of the AI coach is to help key PIM process stakeholders,
        including Ministries of Finance/Planning/Economy (PIM process
        coordinators), project owners (national Ministries, Departments,
        Agencies (MDA), sub-national governments (SNGs), and State-Owned
        Enterprises), as well as domestic and international financiers.
      </p>
      <div className="my-8 overflow-hidden rounded-lg border border-[var(--border)]">
        <Image
          src="/pim-stakeholders.png"
          alt="8 Must Have Dimensions for Project Delivery — Guidance, Appraisal, Independent Review, Selection, Implementation, Adjustment, Operation, and Evaluation across Upstream Pipeline and Downstream Portfolio phases"
          width={960}
          height={540}
          className="w-full h-auto"
        />
      </div>
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
