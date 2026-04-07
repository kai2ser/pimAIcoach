"use client";

import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";

// ── Types ────────────────────────────────────────────────────────────────────

interface Summary {
  total_chunks: number;
  total_documents: number;
  total_tokens: number | null;
  lang_eng_documents: number;
  lang_ori_documents: number;
  last_updated: string | null;
  collection_name: string;
}

interface CountryBreakdown {
  country: string;
  country_name: string | null;
  documents: number;
  chunks: number;
}

interface TierBreakdown {
  tier: number | null;
  label: string;
  documents: number;
}

interface YearBreakdown {
  year: string | null;
  documents: number;
}

interface DetailedStats {
  summary: Summary;
  by_country: CountryBreakdown[];
  by_tier: TierBreakdown[];
  by_year: YearBreakdown[];
  embedding_model: string;
  vector_store: string;
  chunk_size: number;
  chunk_overlap: number;
  retriever_type: string;
}

// ── Colours ──────────────────────────────────────────────────────────────────

const BLUE = "#1d4ed8";
const BLUE_LIGHT = "#3b82f6";
const TIER_COLORS = ["#1d4ed8", "#2563eb", "#3b82f6", "#60a5fa"];
const LANG_COLORS = ["#1d4ed8", "#10b981"];

// ── Component ────────────────────────────────────────────────────────────────

export default function StatisticsContent() {
  const [data, setData] = useState<DetailedStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function fetchData() {
    setLoading(true);
    setError(null);
    fetch("/api/coach/stats/detail")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((d: DetailedStats) => setData(d))
      .catch(() => setError("Failed to load statistics. Please try again."))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return (
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
    );
  }

  if (error || !data) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-16">
        <h2 className="mb-6 text-3xl font-bold">Vector Database Analytics</h2>
        <div role="alert" className="rounded-md border border-red-300 bg-red-50 p-4 text-sm text-red-800 dark:border-red-700 dark:bg-red-900/30 dark:text-red-300">
          {error || "No data available."}
        </div>
        <button onClick={fetchData} className="mt-4 rounded-md bg-[var(--primary)] px-4 py-2 text-sm font-medium text-[var(--primary-foreground)] hover:opacity-90">
          Retry
        </button>
      </div>
    );
  }

  const { summary, by_country, by_tier, by_year } = data;

  // Prepare language pie data
  const langData = [
    { name: "English", value: summary.lang_eng_documents },
    { name: "Original Language", value: summary.lang_ori_documents },
  ].filter((d) => d.value > 0);

  return (
    <div className="mx-auto max-w-5xl px-4 py-16">
      {/* ── Header ──────────────────────────────────────────── */}
      <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold">Vector Database Analytics</h2>
          <p className="mt-1 text-[var(--muted-foreground)]">
            Real-time overview of the document collection stored in pgvector.
            Embedding model:{" "}
            <span className="font-mono text-xs">{data.embedding_model}</span>
          </p>
        </div>
        <button
          onClick={fetchData}
          className="inline-flex items-center gap-2 rounded-md border border-[var(--border)] px-4 py-2 text-sm font-medium text-[var(--foreground)] transition-colors hover:bg-[var(--muted)]"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <polyline points="23 4 23 10 17 10" /><polyline points="1 20 1 14 7 14" /><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
          </svg>
          Refresh
        </button>
      </div>

      {/* ── Summary cards ───────────────────────────────────── */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Documents Indexed" value={summary.total_documents} />
        <StatCard label="Text Chunks" value={summary.total_chunks} />
        <StatCard
          label="Total Tokens"
          value={summary.total_tokens != null ? summary.total_tokens : "—"}
        />
        <StatCard label="Countries" value={by_country.length} />
      </div>

      {/* ── Config badges ───────────────────────────────────── */}
      <div className="mt-4 flex flex-wrap gap-2">
        <Badge label="Vector Store" value={data.vector_store} />
        <Badge label="Chunk Size" value={`${data.chunk_size} chars`} />
        <Badge label="Overlap" value={`${data.chunk_overlap} chars`} />
        <Badge label="Retriever" value={data.retriever_type} />
      </div>

      {/* ── Charts row 1: Documents per Country + Tier split ── */}
      <div className="mt-10 grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Country bar chart — takes 2/3 */}
        <div className="lg:col-span-2 rounded-lg border border-[var(--border)] bg-[var(--background)] p-5 shadow-sm">
          <h3 className="mb-4 text-sm font-semibold uppercase tracking-wide text-[var(--muted-foreground)]">
            Documents by Country
          </h3>
          {by_country.length > 0 ? (
            <ResponsiveContainer width="100%" height={Math.max(300, by_country.length * 32)}>
              <BarChart data={by_country} layout="vertical" margin={{ left: 10, right: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis type="number" tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} />
                <YAxis
                  type="category"
                  dataKey="country"
                  width={48}
                  tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--background)",
                    borderColor: "var(--border)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                  formatter={(value, name) => [
                    Number(value).toLocaleString(),
                    name === "documents" ? "Documents" : "Chunks",
                  ]}
                  labelFormatter={(label) => {
                    const l = String(label);
                    const c = by_country.find((x) => x.country === l);
                    return c?.country_name || l;
                  }}
                />
                <Bar dataKey="documents" fill={BLUE} radius={[0, 4, 4, 0]} name="documents" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="py-12 text-center text-sm text-[var(--muted-foreground)]">
              No country data available.
            </p>
          )}
        </div>

        {/* Tier pie chart — takes 1/3 */}
        <div className="rounded-lg border border-[var(--border)] bg-[var(--background)] p-5 shadow-sm">
          <h3 className="mb-4 text-sm font-semibold uppercase tracking-wide text-[var(--muted-foreground)]">
            Documents by Policy Tier
          </h3>
          {by_tier.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={by_tier}
                  dataKey="documents"
                  nameKey="label"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  innerRadius={45}
                  paddingAngle={2}
                  label={({ name, value }) => `${name}: ${value}`}
                  labelLine={false}
                >
                  {by_tier.map((_, idx) => (
                    <Cell key={idx} fill={TIER_COLORS[idx % TIER_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--background)",
                    borderColor: "var(--border)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="py-12 text-center text-sm text-[var(--muted-foreground)]">
              No tier data available.
            </p>
          )}
          {/* Legend below the chart */}
          <div className="mt-2 space-y-1">
            {by_tier.map((t, idx) => (
              <div key={t.tier} className="flex items-center gap-2 text-xs text-[var(--muted-foreground)]">
                <span
                  className="inline-block h-2.5 w-2.5 rounded-full"
                  style={{ backgroundColor: TIER_COLORS[idx % TIER_COLORS.length] }}
                />
                {t.label} ({t.documents})
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Charts row 2: Year timeline + Language split ───── */}
      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Year bar chart — takes 2/3 */}
        <div className="lg:col-span-2 rounded-lg border border-[var(--border)] bg-[var(--background)] p-5 shadow-sm">
          <h3 className="mb-4 text-sm font-semibold uppercase tracking-wide text-[var(--muted-foreground)]">
            Documents by Year
          </h3>
          {by_year.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={by_year} margin={{ bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis
                  dataKey="year"
                  tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
                  angle={-45}
                  textAnchor="end"
                  height={60}
                />
                <YAxis tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--background)",
                    borderColor: "var(--border)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                  formatter={(value) => [Number(value).toLocaleString(), "Documents"]}
                />
                <Bar dataKey="documents" fill={BLUE_LIGHT} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="py-12 text-center text-sm text-[var(--muted-foreground)]">
              No year data available.
            </p>
          )}
        </div>

        {/* Language pie chart — takes 1/3 */}
        <div className="rounded-lg border border-[var(--border)] bg-[var(--background)] p-5 shadow-sm">
          <h3 className="mb-4 text-sm font-semibold uppercase tracking-wide text-[var(--muted-foreground)]">
            Language Distribution
          </h3>
          {langData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={langData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  innerRadius={40}
                  paddingAngle={3}
                >
                  {langData.map((_, idx) => (
                    <Cell key={idx} fill={LANG_COLORS[idx % LANG_COLORS.length]} />
                  ))}
                </Pie>
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--background)",
                    borderColor: "var(--border)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                  formatter={(value) => [Number(value).toLocaleString(), "Documents"]}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="py-12 text-center text-sm text-[var(--muted-foreground)]">
              No language data available.
            </p>
          )}
          <div className="mt-2 text-center text-xs text-[var(--muted-foreground)]">
            {summary.lang_eng_documents} English &middot;{" "}
            {summary.lang_ori_documents} Original
          </div>
        </div>
      </div>

      {/* ── Country data table ──────────────────────────────── */}
      {by_country.length > 0 && (
        <div className="mt-10 rounded-lg border border-[var(--border)] bg-[var(--background)] shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-[var(--border)]">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-[var(--muted-foreground)]">
              Country Detail
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--border)] bg-[var(--muted)]">
                  <th className="px-5 py-3 text-left font-medium text-[var(--muted-foreground)]">
                    Country
                  </th>
                  <th className="px-5 py-3 text-left font-medium text-[var(--muted-foreground)]">
                    ISO3
                  </th>
                  <th className="px-5 py-3 text-right font-medium text-[var(--muted-foreground)]">
                    Documents
                  </th>
                  <th className="px-5 py-3 text-right font-medium text-[var(--muted-foreground)]">
                    Chunks
                  </th>
                  <th className="px-5 py-3 text-right font-medium text-[var(--muted-foreground)]">
                    Avg Chunks/Doc
                  </th>
                </tr>
              </thead>
              <tbody>
                {by_country.map((c) => (
                  <tr
                    key={c.country}
                    className="border-b border-[var(--border)] last:border-0 hover:bg-[var(--muted)]/50 transition-colors"
                  >
                    <td className="px-5 py-3 font-medium">
                      {c.country_name || c.country}
                    </td>
                    <td className="px-5 py-3 font-mono text-xs text-[var(--muted-foreground)]">
                      {c.country}
                    </td>
                    <td className="px-5 py-3 text-right tabular-nums">
                      {c.documents.toLocaleString()}
                    </td>
                    <td className="px-5 py-3 text-right tabular-nums">
                      {c.chunks.toLocaleString()}
                    </td>
                    <td className="px-5 py-3 text-right tabular-nums">
                      {c.documents > 0
                        ? (c.chunks / c.documents).toFixed(1)
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="bg-[var(--muted)] font-medium">
                  <td className="px-5 py-3" colSpan={2}>
                    Total
                  </td>
                  <td className="px-5 py-3 text-right tabular-nums">
                    {summary.total_documents.toLocaleString()}
                  </td>
                  <td className="px-5 py-3 text-right tabular-nums">
                    {summary.total_chunks.toLocaleString()}
                  </td>
                  <td className="px-5 py-3 text-right tabular-nums">
                    {summary.total_documents > 0
                      ? (summary.total_chunks / summary.total_documents).toFixed(1)
                      : "—"}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Subcomponents ────────────────────────────────────────────────────────────

function StatCard({ label, value }: { label: string; value: number | string }) {
  const formatted =
    typeof value === "number" ? value.toLocaleString() : value;

  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--muted)]/40 p-5">
      <p className="text-xs font-medium uppercase tracking-wide text-[var(--muted-foreground)]">
        {label}
      </p>
      <p className="mt-2 text-2xl font-bold tabular-nums">{formatted}</p>
    </div>
  );
}

function Badge({ label, value }: { label: string; value: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-[var(--border)] bg-[var(--muted)]/60 px-3 py-1 text-xs text-[var(--muted-foreground)]">
      <span className="font-medium text-[var(--foreground)]">{label}:</span>
      {value}
    </span>
  );
}
