import { useEffect, useState } from "react";
import { Link } from "wouter";

const API_URL = (import.meta.env.VITE_VERIDOC_API_URL as string | undefined)?.replace(/\/$/, "");

type Stats = {
  handbook_chunks?: number;
  legal_chunks?: number;
  chunk_count?: number;
};

export default function CorpusRegistry() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!API_URL) {
      setError("VITE_VERIDOC_API_URL is not configured.");
      setLoading(false);
      return;
    }
    fetch(`${API_URL}/ingest/stats`)
      .then((response) => {
        if (!response.ok) throw new Error(`Backend returned ${response.status}`);
        return response.json();
      })
      .then(setStats)
      .catch((reason) => setError(reason instanceof Error ? reason.message : "Could not load corpus stats."))
      .finally(() => setLoading(false));
  }, []);

  const cards = [
    ["Handbook / corporate", stats?.handbook_chunks ?? stats?.chunk_count ?? "—", "384-dimensional collection"],
    ["Indian law", stats?.legal_chunks ?? "—", "1,536-dimensional collection"],
  ];

  return (
    <main className="min-h-screen bg-[#f4f0e8] px-6 py-10 text-[#1e2625] sm:px-12 lg:px-20">
      <div className="mx-auto max-w-6xl">
        <div className="mb-10 flex items-start justify-between gap-6 border-b border-[#d9d1c4] pb-6">
          <div>
            <div className="mb-3 font-mono text-[10px] uppercase tracking-[0.2em] text-[#b96845]">VeriDoc / Corpus registry</div>
            <h1 className="font-serif text-4xl tracking-tight">Evidence inventory</h1>
            <p className="mt-3 max-w-2xl font-serif text-[16px] leading-relaxed text-[#6a706a]">Live collection health from the connected backend. Counts are read from Chroma, not mocked in the interface.</p>
          </div>
          <Link href="/" className="border border-[#1e2625] px-4 py-2 font-mono text-[10px] uppercase tracking-[0.14em] hover:bg-[#1e2625] hover:text-[#f8f5ef]">Back to investigation</Link>
        </div>
        {loading && <div className="border border-[#d9d1c4] bg-[#f8f5ef] p-6 font-mono text-xs text-[#6a706a]">Loading corpus statistics…</div>}
        {error && <div className="border border-[#b96845] bg-[#f8f5ef] p-6 text-sm text-[#8b3f2b]">Could not load live registry data: {error}</div>}
        {!loading && !error && <>
          <div className="grid gap-4 md:grid-cols-2">
            {cards.map(([label, value, detail]) => <article key={label} className="border border-[#d9d1c4] bg-[#f8f5ef] p-6 shadow-[4px_4px_0_#dec7b8]"><div className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#8c857c]">{label}</div><div className="mt-5 font-serif text-5xl">{value}</div><div className="mt-3 font-mono text-[10px] uppercase tracking-[0.12em] text-[#6e8b78]">{detail}</div></article>)}
          </div>
          <section className="mt-8 border border-[#d9d1c4] bg-[#f8f5ef] p-6"><div className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#8c857c]">Registry note</div><p className="mt-3 max-w-3xl font-serif text-[17px] leading-relaxed text-[#3b4540]">The legal and handbook collections use different embedding dimensions and must remain separate. New uploads should be routed to the collection matching their selected domain.</p></section>
        </>}
      </div>
    </main>
  );
}
