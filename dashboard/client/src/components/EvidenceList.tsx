/* The numbered claims, each tied to the passage and page it came from. Picking one opens it in the source reader. */
import { useMemo } from "react";
import { claimText, type EvidenceSource } from "@/lib/evidence";

export default function EvidenceList({
  sources,
  allSources,
  selectedId,
  onSelect,
  filter,
  onFilter,
}: {
  sources: EvidenceSource[];
  allSources: EvidenceSource[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  filter: string;
  onFilter: (value: string) => void;
}) {
  const filters = useMemo(() => {
    const domains = Array.from(new Set(allSources.map((source) => source.domain).filter(Boolean)));
    return domains.length > 1 ? ["All", ...domains] : [];
  }, [allSources]);

  return (
    <section aria-labelledby="sources-heading" className="border border-line bg-sunken">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-4 py-3">
        <h2 id="sources-heading" className="font-mono text-[11px] uppercase tracking-[0.12em] text-mute">
          Sources &nbsp;·&nbsp; {sources.length}
        </h2>
        {filters.length > 0 && (
          <div className="flex flex-wrap gap-1.5" role="group" aria-label="Filter sources by domain">
            {filters.map((value) => (
              <button
                key={value}
                onClick={() => onFilter(value)}
                aria-pressed={filter === value}
                className={`h-7 px-2.5 font-mono text-[10px] uppercase tracking-[0.1em] ${
                  filter === value ? "bg-lime font-bold text-lime-ink" : "border border-edge text-soft hover:border-fg"
                }`}
              >
                {value}
              </button>
            ))}
          </div>
        )}
      </div>

      <ul className="flex flex-col gap-2 p-3">
        {sources.map((source) => {
          const selected = selectedId === source.id;
          return (
            <li key={source.id}>
              <button
                onClick={() => onSelect(source.id)}
                aria-pressed={selected}
                className={`flex w-full items-center gap-3 px-3 py-2.5 text-left transition-colors ${
                  selected ? "border-[1.5px] border-lime bg-tint" : "border border-line bg-panel hover:border-edge"
                }`}
              >
                <span className={`flex h-10 w-10 shrink-0 items-center justify-center text-[22px] font-black ${selected ? "bg-lime text-lime-ink" : "bg-line text-fg"}`}>
                  {Number(source.id)}
                </span>
                <span className="min-w-0 flex-1">
                  <span className={`line-clamp-2 block text-[15px] leading-snug ${selected ? "font-semibold" : ""}`}>{claimText(source.excerpt)}</span>
                  <span className={`mt-1 block truncate font-mono text-[11px] ${selected ? "text-[#c6e26a]" : "text-mute"}`}>
                    {selected ? "Viewing · " : ""}
                    {source.file} · {source.page}
                  </span>
                </span>
              </button>
            </li>
          );
        })}
        {sources.length === 0 && <li className="px-1 py-2 text-[14px] text-mute">No sources in this filter.</li>}
      </ul>
    </section>
  );
}
