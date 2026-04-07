"use client";

import Image from "next/image";
import { useCallback, useEffect, useRef, useState } from "react";
import { SkeletonGrid } from "@/components/Skeleton";

interface CollectionStats {
  total_chunks: number;
  total_documents: number;
  total_tokens: number | null;
  lang_eng_documents: number;
  lang_ori_documents: number;
  last_updated: string | null;
  collection_name: string;
}

interface ReindexProgress {
  current: number;
  total: number;
  document: string;
  status: "ingesting" | "done" | "error";
  chunks?: number;
  error?: string;
}

interface ReindexResult {
  succeeded: number;
  failed: number;
  total_chunks: number;
  message?: string;
}

export default function RagingPage() {
  const [stats, setStats] = useState<CollectionStats | null>(null);
  const [loading, setLoading] = useState(true);

  // Re-index state
  const [apiKey, setApiKey] = useState("");
  const [reindexing, setReindexing] = useState(false);
  const [activeFilter, setActiveFilter] = useState<"all" | "eng" | null>(null);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [progress, setProgress] = useState<ReindexProgress | null>(null);
  const [result, setResult] = useState<ReindexResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const logRef = useRef<HTMLDivElement>(null);

  const fetchStats = useCallback(() => {
    fetch("/api/coach/stats")
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => setStats(data))
      .catch(() => setStats(null))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  async function triggerReindex(langFilter: "all" | "eng") {
    setReindexing(true);
    setActiveFilter(langFilter);
    setProgress(null);
    setResult(null);
    setError(null);
    setStatusMsg(null);

    try {
      const res = await fetch("/api/coach/reindex", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": apiKey,
        },
        body: JSON.stringify({
          lang_filter: langFilter,
          clear_existing: true,
        }),
      });

      if (!res.ok) {
        const detail =
          res.status === 401 || res.status === 403
            ? "Invalid or missing API key."
            : `Request failed (${res.status}).`;
        setError(detail);
        setReindexing(false);
        setActiveFilter(null);
        return;
      }

      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const parts = buffer.split("\n\n");
        buffer = parts.pop()!;

        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith("data: ")) continue;
          try {
            const event = JSON.parse(line.slice(6));
            switch (event.type) {
              case "status":
                setStatusMsg(event.message);
                break;
              case "progress":
                setProgress({
                  current: event.current,
                  total: event.total,
                  document: event.document,
                  status: event.status,
                  chunks: event.chunks,
                  error: event.error,
                });
                break;
              case "complete":
                setResult({
                  succeeded: event.succeeded,
                  failed: event.failed,
                  total_chunks: event.total_chunks,
                  message: event.message,
                });
                break;
              case "error":
                setError(event.message);
                break;
            }
          } catch (e) {
            console.warn("[RAGing] Failed to parse SSE event:", line, e);
          }
        }
      }
    } catch (err) {
      setError("Connection lost. The re-index may still be running on the server.");
    } finally {
      setReindexing(false);
      setActiveFilter(null);
      // Refresh stats after re-index completes
      fetchStats();
    }
  }

  // Auto-scroll log area when progress updates
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [progress, statusMsg]);

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
          loading="lazy"
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
        <SkeletonGrid count={3} />
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

      {/* ── Re-Index Controls ──────────────────────────────────── */}
      <h3 className="mb-4 mt-12 text-2xl font-bold">Re-Index Controls</h3>
      <p className="mb-4 text-sm text-[var(--muted-foreground)]">
        Trigger a re-index of documents from the{" "}
        <a
          href="https://github.com/kai2ser/pimrepository"
          target="_blank"
          rel="noopener noreferrer"
          className="underline hover:text-[var(--foreground)]"
        >
          PIM Policy Repository
        </a>
        . This clears the existing collection and re-ingests all matching
        documents. An admin API key is required.
      </p>

      <div className="rounded-lg border border-[var(--border)] bg-[var(--muted)]/40 p-5 space-y-4">
        {/* API Key input */}
        <div>
          <label
            htmlFor="api-key"
            className="block text-sm font-medium mb-1"
          >
            Admin API Key
          </label>
          <input
            id="api-key"
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="Enter your API key"
            className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/40"
            disabled={reindexing}
          />
        </div>

        {/* Action buttons */}
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => triggerReindex("all")}
            disabled={reindexing || !apiKey}
            className="inline-flex items-center gap-2 rounded-md bg-[var(--primary)] px-4 py-2 text-sm font-medium text-[var(--primary-foreground)] transition-colors hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {reindexing && activeFilter === "all" ? (
              <>
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
                Re-indexing…
              </>
            ) : (
              "Re-index All Documents"
            )}
          </button>

          <button
            onClick={() => triggerReindex("eng")}
            disabled={reindexing || !apiKey}
            className="inline-flex items-center gap-2 rounded-md border border-[var(--primary)] px-4 py-2 text-sm font-medium text-[var(--primary)] transition-colors hover:bg-[var(--primary)]/10 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {reindexing && activeFilter === "eng" ? (
              <>
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
                Re-indexing…
              </>
            ) : (
              "Re-index English Only"
            )}
          </button>
        </div>

        {/* Status / progress area */}
        {(reindexing || result || error) && (
          <div
            ref={logRef}
            className="space-y-3 pt-2"
          >
            {/* Status message */}
            {statusMsg && !result && (
              <p className="text-sm text-[var(--muted-foreground)]">
                {statusMsg}
              </p>
            )}

            {/* Progress bar */}
            {progress && (
              <div>
                <div className="flex justify-between text-xs text-[var(--muted-foreground)] mb-1">
                  <span className="truncate max-w-[70%]">
                    {progress.document}
                  </span>
                  <span className="tabular-nums">
                    {progress.current} / {progress.total}
                  </span>
                </div>
                <div className="h-2 w-full rounded-full bg-[var(--border)]">
                  <div
                    className="h-2 rounded-full bg-[var(--primary)] transition-all duration-300"
                    style={{
                      width: `${(progress.current / progress.total) * 100}%`,
                    }}
                  />
                </div>
                {progress.status === "error" && progress.error && (
                  <p className="mt-1 text-xs text-red-600 dark:text-red-400">
                    Error: {progress.error}
                  </p>
                )}
              </div>
            )}

            {/* Completion summary */}
            {result && (
              <div className="rounded-md border border-green-300 bg-green-50 p-3 text-sm text-green-800 dark:border-green-700 dark:bg-green-900/30 dark:text-green-300">
                {result.message ? (
                  <p>{result.message}</p>
                ) : (
                  <p>
                    Re-index complete:{" "}
                    <strong>{result.succeeded}</strong> succeeded
                    {result.failed > 0 && (
                      <>, <strong>{result.failed}</strong> failed</>
                    )}
                    .{" "}
                    <strong>
                      {result.total_chunks.toLocaleString()}
                    </strong>{" "}
                    total chunks created.
                  </p>
                )}
              </div>
            )}

            {/* Error display */}
            {error && (
              <div className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-800 dark:border-red-700 dark:bg-red-900/30 dark:text-red-300">
                {error}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
