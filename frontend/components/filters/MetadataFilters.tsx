"use client";

import { memo, useEffect, useState } from "react";

export interface Filters {
  country?: string;
  policy_guidance_tier?: number;
  strategy_tier?: number;
  year_from?: number;
  year_to?: number;
  lang_type?: string;
}

interface Country {
  iso3: string;
  name: string;
}

interface MetadataFiltersProps {
  filters: Filters;
  onChange: (filters: Filters) => void;
}

export const MetadataFilters = memo(function MetadataFilters({ filters, onChange }: MetadataFiltersProps) {
  const [countries, setCountries] = useState<Country[]>([]);

  useEffect(() => {
    fetch("/api/coach/countries")
      .then((res) => (res.ok ? res.json() : []))
      .then((data: Country[]) => setCountries(data))
      .catch(() => setCountries([]));
  }, []);

  const update = (key: keyof Filters, value: string | number | undefined) => {
    const next = { ...filters };
    if (value === "" || value === undefined) {
      delete next[key];
    } else {
      (next as Record<string, unknown>)[key] = value;
    }
    onChange(next);
  };

  return (
    <div className="flex flex-wrap items-end gap-3">
      <label className="block">
        <span className="mb-1 block text-xs text-[var(--muted-foreground)]">
          Country
        </span>
        <select
          value={filters.country || ""}
          onChange={(e) => update("country", e.target.value || undefined)}
          className="rounded border border-[var(--border)] bg-[var(--background)] px-2 py-1 text-xs"
        >
          <option value="">All countries</option>
          {countries.map((c) => (
            <option key={c.iso3} value={c.iso3}>
              {c.name}
            </option>
          ))}
        </select>
      </label>

      <label className="block">
        <span className="mb-1 block text-xs text-[var(--muted-foreground)]">
          Policy Tier
        </span>
        <select
          value={filters.policy_guidance_tier || ""}
          onChange={(e) =>
            update(
              "policy_guidance_tier",
              e.target.value ? Number(e.target.value) : undefined
            )
          }
          className="rounded border border-[var(--border)] bg-[var(--background)] px-2 py-1 text-xs"
        >
          <option value="">All</option>
          <option value="1">1 — Legislation</option>
          <option value="2">2 — Regulations</option>
          <option value="3">3 — Guidelines</option>
          <option value="4">4 — Strategy</option>
        </select>
      </label>

      <label className="block">
        <span className="mb-1 block text-xs text-[var(--muted-foreground)]">
          Language
        </span>
        <select
          value={filters.lang_type || ""}
          onChange={(e) => update("lang_type", e.target.value || undefined)}
          className="rounded border border-[var(--border)] bg-[var(--background)] px-2 py-1 text-xs"
        >
          <option value="">All</option>
          <option value="ENG">English</option>
          <option value="ORI">Original</option>
        </select>
      </label>

      <label className="block">
        <span className="mb-1 block text-xs text-[var(--muted-foreground)]">
          Year from
        </span>
        <input
          type="number"
          value={filters.year_from || ""}
          onChange={(e) =>
            update("year_from", e.target.value ? Number(e.target.value) : undefined)
          }
          placeholder="2000"
          className="w-20 rounded border border-[var(--border)] bg-[var(--background)] px-2 py-1 text-xs"
        />
      </label>

      <label className="block">
        <span className="mb-1 block text-xs text-[var(--muted-foreground)]">
          Year to
        </span>
        <input
          type="number"
          value={filters.year_to || ""}
          onChange={(e) =>
            update("year_to", e.target.value ? Number(e.target.value) : undefined)
          }
          placeholder="2026"
          className="w-20 rounded border border-[var(--border)] bg-[var(--background)] px-2 py-1 text-xs"
        />
      </label>

      <button
        onClick={() => onChange({})}
        className="rounded border border-[var(--border)] px-2 py-1 text-xs text-[var(--muted-foreground)] hover:bg-[var(--muted)]"
      >
        Clear
      </button>
    </div>
  );
});
