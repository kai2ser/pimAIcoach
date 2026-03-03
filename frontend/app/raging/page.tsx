"use client";

import Image from "next/image";
import { useEffect, useState } from "react";

interface CollectionStats {
  total_chunks: number;
  total_documents: number;
  total_tokens: number | null;
  lang_eng_documents: number;
  lang_ori_documents: number;
  last_updated: string | null;
  collection_name: string;
}

export default function RagingPage() {
  const [stats, setStats] = useState<CollectionStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/coach/stats")
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => setStats(data))
      .catch(() => setStats(null))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="mx-auto max-w-3xl px-4 py-16">
      <h2 className="mb-6 text-3xl font-bold">
        Retrieval-Augmented Generation (RAG)
      </h2>
      <p className="mb-4 text-[var(--muted-foreground)]">
        Retrieval-augmented generation (RAG) is a technique that enables large
        language models (LLMs) to retrieve and incorporate new information from
        external data sources. The AI Coach implements RAG workflows from the
        documents stored and updated in the PIM Country Policy Profiles
        Repository Application. These documents are maintained in both
        source/original language, as well as English translations (if this is
        not the source language). Implementing Retrieval-Augmented Generation
        (RAG) involves three core steps:{" "}
        <strong>indexing</strong> (preparing data),{" "}
        <strong>retrieval</strong> (finding relevant context), and{" "}
        <strong>generation</strong> (producing the answer). Key actions include
        data ingestion, chunking, embedding, vector storage, query processing,
        and prompt augmentation for an LLM. This prototype application
        implements these different steps in ways that try to cater to different
        language contexts, as well as the particular structure of policy
        documents (including law).
      </p>
      <div className="my-8 overflow-hidden rounded-lg border border-[var(--border)]">
        <Image
          src="/rag-diagram.png"
          alt="Working Across Languages for AI Retrieval Augmented Generation — diagram showing English and Non-English source data flowing to English and Non-English responses"
          width={960}
          height={540}
          className="w-full h-auto"
        />
      </div>

      {/* ── Input Updates ─────────────────────────────────────── */}
      <h3 className="mb-4 mt-12 text-2xl font-bold">Input Updates</h3>
      <p className="mb-6 text-[var(--muted-foreground)]">
        The baseline international RAG is based on English originals and
        translations (where official language is not English).
      </p>

      {loading ? (
        <div className="flex items-center gap-2 text-sm text-[var(--muted-foreground)]">
          <svg
            className="h-4 w-4 animate-spin"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
          Loading collection statistics…
        </div>
      ) : stats ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="rounded-lg border border-[var(--border)] bg-[var(--muted)]/40 p-5">
            <p className="text-sm text-[var(--muted-foreground)]">
              Last Updated
            </p>
            <p className="mt-1 text-2xl font-semibold">
              {stats.last_updated ?? "—"}
            </p>
          </div>
          <div className="rounded-lg border border-[var(--border)] bg-[var(--muted)]/40 p-5">
            <p className="text-sm text-[var(--muted-foreground)]">
              Documents Indexed
            </p>
            <p className="mt-1 text-2xl font-semibold">
              {stats.total_documents.toLocaleString()}
            </p>
            <p className="mt-1 text-xs text-[var(--muted-foreground)]">
              {stats.lang_eng_documents.toLocaleString()} English ·{" "}
              {stats.lang_ori_documents.toLocaleString()} Original language
            </p>
          </div>
          <div className="rounded-lg border border-[var(--border)] bg-[var(--muted)]/40 p-5">
            <p className="text-sm text-[var(--muted-foreground)]">
              Total Tokens
            </p>
            <p className="mt-1 text-2xl font-semibold">
              {stats.total_tokens != null
                ? stats.total_tokens.toLocaleString()
                : "—"}
            </p>
          </div>
        </div>
      ) : (
        <p className="text-sm text-[var(--muted-foreground)]">
          Unable to load collection statistics.
        </p>
      )}
    </div>
  );
}
