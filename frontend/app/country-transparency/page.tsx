"use client";

import { useCallback, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Country {
  iso3: string;
  name: string;
}

export default function CountryTransparencyPage() {
  const [countries, setCountries] = useState<Country[]>([]);
  const [loadingCountries, setLoadingCountries] = useState(true);
  const [selectedIso3, setSelectedIso3] = useState("");
  const [selectedName, setSelectedName] = useState("");

  // Generation state
  const [generating, setGenerating] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [reportContent, setReportContent] = useState("");
  const [error, setError] = useState<string | null>(null);

  // Export state
  const [exporting, setExporting] = useState<"docx" | "pdf" | null>(null);

  // Load countries on mount
  useEffect(() => {
    fetch("/api/coach/countries")
      .then((res) => (res.ok ? res.json() : []))
      .then((data: Country[]) => setCountries(data))
      .catch(() => setCountries([]))
      .finally(() => setLoadingCountries(false));
  }, []);

  // Handle country selection
  const handleCountryChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      const iso3 = e.target.value;
      setSelectedIso3(iso3);
      const c = countries.find((c) => c.iso3 === iso3);
      setSelectedName(c?.name ?? "");
      // Reset previous results
      setReportContent("");
      setError(null);
      setStatusMsg(null);
    },
    [countries]
  );

  // Generate transparency briefing
  async function generateBriefing() {
    if (!selectedIso3) return;

    setGenerating(true);
    setReportContent("");
    setError(null);
    setStatusMsg(null);

    try {
      const res = await fetch("/api/coach/country-transparency", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ country_iso3: selectedIso3 }),
      });

      if (!res.ok) {
        setError(`Request failed (${res.status}).`);
        setGenerating(false);
        return;
      }

      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let accumulated = "";

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
                setStatusMsg(event.data);
                break;
              case "token":
                accumulated += event.data;
                setReportContent(accumulated);
                break;
              case "error":
                setError(event.data);
                break;
              case "done":
                break;
            }
          } catch {
            // skip malformed SSE lines
          }
        }
      }
    } catch {
      setError("Connection lost. Please try again.");
    } finally {
      setGenerating(false);
    }
  }

  // Export as DOCX or PDF
  async function handleExport(format: "docx" | "pdf") {
    if (!reportContent) return;
    setExporting(format);
    try {
      const res = await fetch("/api/coach/country-transparency/export", {
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
      a.download = `PIM_Transparency_${selectedName.replace(/\s+/g, "_")}.${format}`;
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
        Country PIM Transparency
      </h2>
      <p className="mb-8 text-[var(--muted-foreground)]">
        Generate a comprehensive transparency briefing for a country&apos;s
        public investment management framework, covering institutional
        architecture, the 8 must-have PIM stages, and policy repository
        document listings with tier classifications. The briefing draws on
        the{" "}
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
              htmlFor="transparency-country-select"
              className="block text-sm font-medium mb-1"
            >
              Select Country
            </label>
            <select
              id="transparency-country-select"
              value={selectedIso3}
              onChange={handleCountryChange}
              disabled={loadingCountries || generating}
              className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
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
          </div>

          {/* Generate button — green theme */}
          <button
            onClick={generateBriefing}
            disabled={!selectedIso3 || generating}
            className="inline-flex items-center gap-2 rounded-md bg-emerald-600 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {generating ? (
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
                Generating&hellip;
              </>
            ) : (
              "Generate Briefing"
            )}
          </button>
        </div>

        {/* Status message */}
        {statusMsg && generating && (
          <p className="text-sm text-[var(--muted-foreground)]">{statusMsg}</p>
        )}
      </div>

      {/* ── Error display ──────────────────────────────────────── */}
      {error && (
        <div className="mt-4 rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-800 dark:border-red-700 dark:bg-red-900/30 dark:text-red-300">
          {error}
        </div>
      )}

      {/* ── Report display ─────────────────────────────────────── */}
      {(reportContent || generating) && (
        <div className="mt-8">
          {/* Download buttons */}
          {reportContent && !generating && (
            <div className="mb-4 flex gap-3">
              <button
                onClick={() => handleExport("docx")}
                disabled={!!exporting}
                className="inline-flex items-center gap-2 rounded-md border border-emerald-600 px-4 py-2 text-sm font-medium text-emerald-600 transition-colors hover:bg-emerald-50 disabled:opacity-50"
              >
                {exporting === "docx" ? (
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
                    Exporting&hellip;
                  </>
                ) : (
                  <>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                      <polyline points="7 10 12 15 17 10" />
                      <line x1="12" y1="15" x2="12" y2="3" />
                    </svg>
                    Download Word (.docx)
                  </>
                )}
              </button>

              <button
                onClick={() => handleExport("pdf")}
                disabled={!!exporting}
                className="inline-flex items-center gap-2 rounded-md border border-[var(--border)] px-4 py-2 text-sm font-medium text-[var(--foreground)] transition-colors hover:bg-[var(--muted)] disabled:opacity-50"
              >
                {exporting === "pdf" ? (
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
                    Exporting&hellip;
                  </>
                ) : (
                  <>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                      <polyline points="7 10 12 15 17 10" />
                      <line x1="12" y1="15" x2="12" y2="3" />
                    </svg>
                    Download PDF
                  </>
                )}
              </button>
            </div>
          )}

          {/* Rendered report */}
          <div className="rounded-lg border border-[var(--border)] bg-[var(--background)] p-6 shadow-sm">
            <div className="prose prose-sm max-w-none dark:prose-invert prose-headings:text-[var(--foreground)] prose-p:text-[var(--foreground)] prose-td:text-sm prose-th:text-sm prose-table:text-sm">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {reportContent}
              </ReactMarkdown>
              {generating && (
                <span className="inline-block h-4 w-1 animate-pulse bg-emerald-500" />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
