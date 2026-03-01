import { FileText } from "lucide-react";

export interface Source {
  content: string;
  metadata: {
    country?: string;
    country_name?: string;
    name_eng?: string;
    year?: number;
    policy_guidance_tier?: number;
    source?: string;
    [key: string]: unknown;
  };
}

const TIER_LABELS: Record<number, string> = {
  1: "Legislation",
  2: "Regulation",
  3: "Guidelines",
  4: "Strategy",
};

export function SourceCards({ sources }: { sources: Source[] }) {
  if (sources.length === 0) return null;

  return (
    <div>
      <p className="mb-2 text-xs font-medium text-[var(--muted-foreground)]">
        Sources ({sources.length})
      </p>
      <div className="flex gap-2 overflow-x-auto pb-1">
        {sources.map((source, i) => (
          <div
            key={i}
            className="shrink-0 rounded-lg border border-[var(--border)] bg-[var(--background)] p-3"
            style={{ maxWidth: 260 }}
          >
            <div className="mb-1 flex items-center gap-1.5">
              <FileText className="h-3.5 w-3.5 text-[var(--primary)]" />
              <span className="truncate text-xs font-medium">
                {source.metadata.country_name || source.metadata.country || "Unknown"}
                {source.metadata.year ? ` (${source.metadata.year})` : ""}
              </span>
            </div>
            {source.metadata.name_eng && (
              <p className="mb-1 truncate text-xs text-[var(--muted-foreground)]">
                {source.metadata.name_eng}
              </p>
            )}
            {source.metadata.policy_guidance_tier && (
              <span className="inline-block rounded-full bg-[var(--accent)] px-2 py-0.5 text-[10px]">
                {TIER_LABELS[source.metadata.policy_guidance_tier] || `Tier ${source.metadata.policy_guidance_tier}`}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
