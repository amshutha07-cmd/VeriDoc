import { Link } from "wouter";

export default function KnowledgeGraph() {
  return (
    <main className="min-h-screen bg-[#f4f0e8] px-6 py-10 text-[#1e2625] sm:px-12 lg:px-20">
      <div className="mx-auto max-w-6xl">
        <div className="mb-10 flex items-start justify-between gap-6 border-b border-[#d9d1c4] pb-6"><div><div className="mb-3 font-mono text-[10px] uppercase tracking-[0.2em] text-[#b96845]">VeriDoc / Knowledge graph</div><h1 className="font-serif text-4xl tracking-tight">Relationship explorer</h1><p className="mt-3 max-w-2xl font-serif text-[16px] leading-relaxed text-[#6a706a]">A transparent view of source relationships and graph-backed evidence.</p></div><Link href="/" className="border border-[#1e2625] px-4 py-2 font-mono text-[10px] uppercase tracking-[0.14em] hover:bg-[#1e2625] hover:text-[#f8f5ef]">Back to investigation</Link></div>
        <section className="border border-[#d9d1c4] bg-[#f8f5ef] p-8 shadow-[4px_4px_0_#dec7b8]"><div className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#b96845]">Graph status</div><h2 className="mt-4 font-serif text-3xl">Graph inspection API not exposed</h2><p className="mt-4 max-w-2xl font-serif text-[17px] leading-relaxed text-[#4c514d]">The backend currently uses graph context during investigation, but it does not yet expose a safe node-search endpoint for this screen. No invented nodes or relationships are shown.</p><div className="mt-8 grid gap-3 md:grid-cols-4">{["Act", "Section", "Page", "Source passage"].map((item, index) => <div key={item} className="border border-[#d9d1c4] bg-[#f2eee7] p-4"><div className="font-mono text-[10px] text-[#8c857c]">0{index + 1}</div><div className="mt-3 font-serif text-lg">{item}</div><div className="mt-2 font-mono text-[9px] uppercase tracking-[0.1em] text-[#8c857c]">awaiting endpoint</div></div>)}</div></section>
      </div>
    </main>
  );
}
