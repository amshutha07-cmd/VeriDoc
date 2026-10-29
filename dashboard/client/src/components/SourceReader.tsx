/* The proof. Shows the chain claim, passage, page, file for the chosen source, and the passage itself on a paper page with its first sentence highlighted. */
import { ChevronDown } from "lucide-react";
import { claimText, splitLead, type EvidenceSource } from "@/lib/evidence";

export default function SourceReader({
  sources,
  selectedId,
  onSelect,
}: {
  sources: EvidenceSource[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const index = sources.findIndex((source) => source.id === selectedId);
  const source = index >= 0 ? sources[index] : null;

  if (!source) {
    return (
      <section aria-label="Source reader" className="border border-dashed border-edge p-6">
        <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-mute">Source reader</div>
        <p className="mt-3 text-[22px] font-extrabold leading-tight tracking-[-0.01em]">The proof opens here.</p>
        <p className="mt-2 max-w-[420px] text-[15px] leading-relaxed text-mute">
          Run a question. Pick any claim and the passage it came from appears on its page, with the file and page number beside it.
        </p>
      </section>
    );
  }

  const [lead, rest] = splitLead(source.excerpt);
  const go = (offset: number) => {
    const next = sources[(index + offset + sources.length) % sources.length];
    if (next) onSelect(next.id);
  };

  return (
    <section aria-label="Source reader" className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-mute">
          Source {index + 1} of {sources.length}
        </div>
        {sources.length > 1 && (
          <div className="flex gap-2">
            <button onClick={() => go(-1)} className="flex h-9 items-center gap-1.5 border border-edge px-3 text-[13px] font-semibold hover:border-fg">
              <ChevronDown className="h-3.5 w-3.5 rotate-90" /> Previous
            </button>
            <button onClick={() => go(1)} className="flex h-9 items-center gap-1.5 border border-edge px-3 text-[13px] font-semibold hover:border-fg">
              Next <ChevronDown className="h-3.5 w-3.5 -rotate-90" />
            </button>
          </div>
        )}
      </div>

      <dl className="grid grid-cols-2 border border-line bg-panel sm:grid-cols-4">
        {[
          ["Claim", claimText(source.excerpt)],
          ["Passage", `“${source.excerpt.slice(0, 48).trim()}…”`],
          ["Page", source.page],
          ["File", source.file],
        ].map(([label, value], position) => (
          <div key={label} className={`min-w-0 p-3 ${position < 2 ? "border-b border-line sm:border-b-0" : ""} ${position % 2 === 0 ? "border-r border-line" : ""} ${position === 1 ? "sm:border-r" : ""} ${position === 2 ? "sm:border-r" : ""}`}>
            <dt className="font-mono text-[10px] uppercase tracking-[0.14em] text-lime">
              {label}
              {label !== "File" ? " ▶" : ""}
            </dt>
            <dd className={`mt-1.5 line-clamp-3 break-words leading-snug ${label === "Page" ? "text-[22px] font-black" : "text-[13px]"} ${label === "Passage" ? "italic" : ""}`}>{value}</dd>
          </div>
        ))}
      </dl>

      <article className="bg-paper px-5 py-6 font-serif text-[#1a1a1a] sm:px-8 sm:py-7">
        <div className="flex flex-wrap items-baseline justify-between gap-2 text-[11px] uppercase tracking-[0.16em] text-[#55534c]">
          <span className="break-words">{source.file}</span>
          <span>{source.page}</span>
        </div>
        <p className="mt-5 text-[19px] leading-[1.75] sm:text-[21px]">
          <mark className="bg-lime px-0 py-0.5 text-[#14150f] [box-decoration-break:clone]">{lead}</mark>
          {rest}
        </p>
      </article>

      <div className="flex flex-wrap gap-x-4 gap-y-1 font-mono text-[11px] text-mute">
        {source.documentType && <span>{source.documentType}</span>}
        {source.organization && <span>{source.organization}</span>}
        {source.year && <span>{source.year}</span>}
        <span>{source.domain}</span>
      </div>
    </section>
  );
}
