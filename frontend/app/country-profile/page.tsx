"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useSSEStream, type SSEEvent } from "@/lib/useSSEStream";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { LoadingSpinner } from "@/components/LoadingSpinner";

interface Country {
  iso3: string;
  name: string;
}

export default function CountryProfilePage() {
  const [countries, setCountries] = useState<Country[]>([]);
  const [loadingCountries, setLoadingCountries] = useState(true);
  const [countriesError, setCountriesError] = useState<string | null>(null);
  const [selectedIso3, setSelectedIso3] = useState("");
  const [selectedName, setSelectedName] = useState("");
  const [langType, setLangType] = useState<"ENG" | "ORI">("ENG");

  // Generation state
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [reportContent, setReportContent] = useState("");
  const [error, setError] = useState<string | null>(null);

  // Export state
  const [exporting, setExporting] = useState<"docx" | "pdf" | null>(null);

  // Accumulated content ref to avoid stale closure in onEvent
  const accRef = useRef("");

  const { startStream, isStreaming } = useSSEStream({
    onEvent: (event: SSEEvent) => {
      switch (event.type) {
        case "status":
          setStatusMsg(event.data as string);
          break;
        case "token":
          accRef.current += event.data as string;
          setReportContent(accRef.current);
          break;
        case "error":
          setError(event.data as string);
          break;
        case "done":
          break;
      }
    },
  });

  // Load countries on mount
  useEffect(() => {
    fetch("/api/coach/countries")
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error(`HTTP ${res.status}`))))
      .then((data: Country[]) => setCountries(data))
      .catch(() => {
        setCountries([]);
        setCountriesError("Failed to load countries. Please refresh the page.");
      })
      .finally(() => setLoadingCountries(false));
  }, []);

  // Handle country selection
  const handleCountryChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      const iso3 = e.target.value;
      setSelectedIso3(iso3);
      const c = countries.find((c) => c.iso3 === iso3);
      setSelectedName(c?.name ?? "");
      setReportContent("");
      setError(null);
      setStatusMsg(null);
    },
    [countries]
  );

  // Generate profile
  async function generateProfile() {
    if (!selectedIso3) return;
    setReportContent("");
    setError(null);
    setStatusMsg(null);
    accRef.current = "";

    await startStream("/api/coach/country-profile", {
      country_iso3: selectedIso3,
      lang_type: langType,
    });
  }

  // Export as DOCX or PDF
  async function handleExport(format: "docx" | "pdf") {
    if (!reportContent) return;
    setExporting(format);
    try {
      const res = await fetch("/api/coach/country-profile/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: reportContent,
          country_name: selectedName,
          format,
        }),
      });

      if (!res.ok) {
        setError("Export failed. Please try again.");
        return;
      }

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const safeName = selectedName.replace(/[^a-z0-9_\- ]/gi, "").replace(/\s+/g, "_");
      a.download = `PIM_Profile_${safeName}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      setError("Export failed. Please try again.");
    } finally {
      setExporting(null);
    }
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-16">
      <h2 className="mb-4 text-3xl font-bold">
        Country PIM Institutional Profile
      </h2>
      <p className="mb-8 text-[var(--muted-foreground)]">
        Generate a comprehensive institutional profile summarizing a
        country&apos;s public investment management framework, policy
        architecture, and the 8 must-have PIM stages. The profile draws on
        documents from the{" "}
        <a
          href="https://pim-policyrepository4.vercel.app/"
          target="_blank"
          rel="noopener noreferrer"
          className="underline hover:text-[var(--foreground)]"
        >
          PIM Policy Repository
        </a>{" "}
        and the AI Coach&apos;s knowledge base.
      </p>

      {/* ── Country selection & generate ───────────────────────── */}
      <div className="rounded-lg border border-[var(--border)] bg-[var(--muted)]/40 p-5 space-y-4">
        <div className="flex flex-wrap items-end gap-4">
          {/* Country dropdown */}
          <div className="flex-1 min-w-[200px]">
            <label
              htmlFor="country-select"
              className="block text-sm font-medium mb-1"
            >
              Select Country
            </label>
            <select
              id="country-select"
              value={selectedIso3}
              onChange={handleCountryChange}
              disabled={loadingCountries || isStreaming}
              aria-describedby={countriesError ? "countries-error" : undefined}
              className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/40"
            >
              <option value="">
                {loadingCountries ? "Loading countries\u2026" : "Choose a country\u2026"}
              </option>
              {countries.map((c) => (
                <option key={c.iso3} value={c.iso3}>
                  {c.name}
                </option>
              ))}
            </select>
            {countriesError && (
              <p id="countries-error" className="mt-1 text-xs text-red-600">{countriesError}</p>
            )}
          </div>

          {/* Language selector */}
          <div className="min-w-[140px]">
            <label
              htmlFor="lang-select"
              className="block text-sm font-medium mb-1"
            >
              Document Language
            </label>
            <select
              id="lang-select"
              value={langType}
              onChange={(e) => setLangType(e.target.value as "ENG" | "ORI")}
              disabled={isStreaming}
              className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/40"
            >
              <option value="ENG">English</option>
              <option value="ORI">Original Language</option>
            </select>
          </div>

          {/* Generate button */}
          <button
            onClick={generateProfile}
            disabled={!selectedIso3 || isStreaming}
            className="inline-flex items-center gap-2 rounded-md bg-[var(--primary)] px-5 py-2 text-sm font-medium text-[var(--primary-foreground)] transition-colors hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isStreaming ? (
              <>
                <svg
                  className="h-4 w-4 animate-spin"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
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
                Generating&hellip;
              </>
            ) : (
              "Generate Profile"
            )}
          </button>
        </div>

        {/* Original language banner */}
        {langType === "ORI" && (
          <div className="rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-800 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-200">
            Original language mode — The profile will be generated from non-English
            source documents and the response will be in the document&apos;s original language.
          </div>
        )}

        {/* Status message */}
        {statusMsg && isStreaming && (
          <p className="text-sm text-[var(--muted-foreground)]" aria-live="polite">{statusMsg}</p>
        )}
      </div>

      {/* ── Error display ──────────────────────────────────────── */}
      {error && (
        <div role="alert" className="mt-4 rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-800 dark:border-red-700 dark:bg-red-900/30 dark:text-red-300">
          {error}
        </div>
      )}

      {/* ── Report display ─────────────────────────────────────── */}
      {(reportContent || isStreaming) && (
        <div className="mt-8">
          {/* Download buttons */}
          {reportContent && !isStreaming && (
            <div className="mb-4 flex gap-3">
              <button
                onClick={() => handleExport("docx")}
                disabled={!!exporting}
                aria-label="Download as Word document"
                className="inline-flex items-center gap-2 rounded-md border border-[var(--primary)] px-4 py-2 text-sm font-medium text-[var(--primary)] transition-colors hover:bg-[var(--primary)]/10 disabled:opacity-50"
              >
                {exporting === "docx" ? (
                  <>
                    <LoadingSpinner />
                    Exporting&hellip;
                  </>
                ) : (
                  <>
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></svg>
                    Download Word (.docx)
                  </>
                )}
              </button>

              <button
                onClick={() => handleExport("pdf")}
                disabled={!!exporting}
                aria-label="Download as PDF"
                className="inline-flex items-center gap-2 rounded-md border border-[var(--border)] px-4 py-2 text-sm font-medium text-[var(--foreground)] transition-colors hover:bg-[var(--muted)] disabled:opacity-50"
              >
                {exporting === "pdf" ? (
                  <>
                    <LoadingSpinner />
                    Exporting&hellip;
                  </>
                ) : (
                  <>
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></svg>
                    Download PDF
                  </>
                )}
              </button>
            </div>
          )}

          {/* Rendered report */}
          <div className="rounded-lg border border-[var(--border)] bg-[var(--background)] p-6 shadow-sm">
            <div className="prose prose-sm max-w-none dark:prose-invert prose-headings:text-[var(--foreground)] prose-p:text-[var(--foreground)] prose-td:text-sm prose-th:text-sm prose-table:text-sm">
              <ErrorBoundary>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {reportContent}
                </ReactMarkdown>
              </ErrorBoundary>
              {isStreaming && (
                <span className="inline-block h-4 w-1 animate-pulse bg-[var(--primary)]" />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
