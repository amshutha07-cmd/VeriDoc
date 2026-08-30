import { useMemo, useState } from "react";

type EvidenceItem = {
  source?: string;
  filename?: string;
  page?: number | string;
  excerpt?: string;
  tag?: string;
  category?: string;
  confidence?: number;
};

export default function ClaimEvidenceMap({ sources }: { sources: EvidenceItem[] }) {
  const [selected, setSelected] = useState<EvidenceItem | null>(null);
  const claims = useMemo(() => sources.slice(0, 4).map((source, index) => ({
    id: index + 1,
    text: (() => { const raw = (source.excerpt || "Evidence-backed finding from the retrieved passage.").replace(/^[\s\d.,;:()\-]+/, ""); const first = raw.split(/[.!?]/)[0].trim(); return first.length >= 12 ? first : (raw.slice(0, 140).trim() || "Evidence-backed finding from the retrieved passage."); })(),
    source,
  })), [sources]);
  const uniqueSources = new Set(sources.map((item) => item.source ?? item.filename ?? "Unknown source")).size;
  const anchoredPages = sources.filter((item) => item.page !== undefined && item.page !== null && String(item.page).trim() !== "").length;
  const quality = sources.length === 0 ? "Awaiting evidence" : anchoredPages === sources.length ? "Page-anchored" : "Partial metadata";

  if (!sources.length) return <section className="mt-8 border border-[#d9d1c4] bg-[#f8f5ef] p-6"><div className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#8c857c]">Claim / Evidence Map</div><p className="mt-4 font-serif text-lg text-[#b7c8bc]">Run an investigation to populate the claim and evidence relationship map.</p></section>;

  return <section className="mt-8 overflow-hidden border border-[#293431] bg-[#17211f] text-[#f4f0e8] shadow-[6px_6px_0_#b96845]"><div className="flex flex-wrap items-start justify-between gap-4 border-b border-[#40504a] px-5 py-4"><div><div className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#e5a182]">Claim / Evidence Graph</div><h2 className="mt-2 font-serif text-2xl">How the answer is supported</h2></div><div className="grid grid-cols-3 gap-4 font-mono text-[9px] uppercase tracking-[0.1em] text-[#b7c8bc]"><span><b className="block text-lg text-[#f4f0e8]">{claims.length}</b>claims</span><span><b className="block text-lg text-[#f4f0e8]">{sources.length}</b>passages</span><span><b className="block text-lg text-[#e5a182]">{uniqueSources}</b>sources</span></div></div><div className="grid gap-0 lg:grid-cols-[1.1fr_0.9fr]"><div className="relative min-h-[330px] overflow-hidden border-b border-[#40504a] p-6 lg:border-b-0 lg:border-r"><div className="absolute left-1/2 top-1/2 flex h-24 w-36 -translate-x-1/2 -translate-y-1/2 items-center justify-center border border-[#e5a182] bg-[#263633] px-3 text-center font-serif text-lg text-[#f8f5ef] shadow-[0_0_0_5px_#1d2926]">Grounded claim<div className="mt-1 font-mono text-[9px] uppercase tracking-[0.1em] text-[#a9c3b1]">{quality}</div></div>{claims.map((claim, index) => { const positions = ["left-5 top-5", "right-5 top-5", "left-5 bottom-5", "right-5 bottom-5"]; return <button key={`${claim.source.source}-${claim.source.page}-${index}`} onClick={() => setSelected(claim.source)} className={`absolute ${positions[index]} w-[42%] border p-3 text-left transition ${selected === claim.source ? "border-[#e5a182] bg-[#344640]" : "border-[#53645c] bg-[#22302d] hover:border-[#d0a58e]"}`}><div className="font-mono text-[9px] uppercase tracking-[0.08em] text-[#e5a182]">Claim {String(claim.id).padStart(2, "0")}</div><div className="mt-2 line-clamp-2 font-serif text-sm text-[#f4f0e8]">{claim.text}</div><div className="mt-1 font-mono text-[9px] text-[#b7c8bc]">{claim.source.source ?? claim.source.filename ?? "Source"} · p. {claim.source.page ?? "?"}</div></button>; })}</div><aside className="bg-[#1d2926] p-6 text-[#f4f0e8]"><div className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#b96845]">Evidence inspector</div>{selected ? <><div className="mt-5 flex items-center justify-between gap-3"><h3 className="truncate font-serif text-xl">{selected.source ?? selected.filename ?? "Source passage"}</h3><span className="font-mono text-[10px] text-[#6e8b78]">p. {selected.page ?? "?"}</span></div><div className="mt-4 border-l-2 border-[#b96845] pl-4 font-serif text-[15px] leading-relaxed text-[#e5ddd2]">{selected.excerpt ?? "Source passage selected from the evidence packet."}</div><div className="mt-5 flex flex-wrap gap-2 font-mono text-[9px] uppercase tracking-[0.1em] text-[#b7c8bc]"><span>{selected.tag ?? selected.category ?? "direct support"}</span><span>|</span><span>provenance preserved</span></div></> : <p className="mt-5 font-serif text-lg text-[#b7c8bc]">Select a claim node to inspect its supporting passage.</p>}</aside></div><div className="flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-[#40504a] px-5 py-3 font-mono text-[9px] uppercase tracking-[0.1em] text-[#b7c8bc]"><span className="text-[#e5a182]">Evidence quality</span><span>{quality}</span><span>{anchoredPages}/{sources.length} page anchors</span><span>{uniqueSources} unique source{uniqueSources === 1 ? "" : "s"}</span></div></section>;
}