import { useState } from "react";

type GraphNode = { node?: string; type?: string; source?: string; page?: number | string; section?: string; excerpt?: string; relationship?: string };

export default function KnowledgeGraph() {
  const [question, setQuestion] = useState("");
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [status, setStatus] = useState("not run");
  const [selected, setSelected] = useState<GraphNode | null>(null);
  const apiBase = ((import.meta.env.VITE_VERIDOC_API_URL as string | undefined) || "http://127.0.0.1:8000" ).replace(/\/$/, "");

  async function inspectGraph() {
    if (!question.trim()) return;
    setStatus("loading");
    setSelected(null);
    try {
      const response = await fetch(apiBase + "/graph/search", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question }) });
      if (!response.ok) throw new Error("Graph API returned " + response.status);
      const payload = await response.json();
      const nextNodes = Array.isArray(payload.nodes) ? payload.nodes : [];
      setNodes(nextNodes);
      setStatus(payload.status === "connected" ? "connected" : "no graph results");
    } catch {
      setNodes([]);
      setStatus("API unavailable");
    }
  }

  return <main className="min-h-screen bg-[#f3efe7] px-5 py-10 text-[#1e2625] sm:px-10"><div className="mx-auto max-w-6xl"><div className="mb-8 flex items-end justify-between gap-4"><div><div className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#b96845]">VeriDoc / Knowledge Graph</div><h1 className="mt-3 font-serif text-4xl">Act ? Section ? Page ? Passage</h1><p className="mt-3 max-w-2xl font-serif text-lg text-[#5e665f]">Live graph context from the backend. Empty results remain honest.</p></div><div className="font-mono text-[10px] uppercase tracking-[0.12em] text-[#547461]">{status}</div></div><div className="mb-8 flex flex-col gap-3 sm:flex-row"><input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask about an Act, section, page, or passage" className="min-h-12 flex-1 border border-[#b9aea0] bg-[#fffdf8] px-4 font-serif text-base outline-none focus:border-[#b96845]" /><button onClick={inspectGraph} disabled={status === "loading"} className="bg-[#1e2625] px-6 py-3 font-mono text-[10px] uppercase tracking-[0.14em] text-[#f8f5ef] disabled:opacity-50">{status === "loading" ? "Inspecting..." : "Inspect graph"}</button></div>{nodes.length === 0 ? <section className="border border-[#d9d1c4] bg-[#f8f5ef] p-8"><div className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#b96845]">Graph status</div><h2 className="mt-4 font-serif text-3xl">{status === "not run" ? "Run a graph inspection" : status}</h2><p className="mt-4 font-serif text-lg text-[#5e665f]">No invented nodes are shown. The current graph store may not contain a matching path for this question.</p></section> : <div className="grid gap-5 lg:grid-cols-[1.15fr_0.85fr]"><section className="border border-[#293431] bg-[#17211f] p-6 text-[#f4f0e8] shadow-[6px_6px_0_#b96845]"><div className="mb-6 flex items-center justify-between"><div className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#e5a182]">Live graph paths</div><div className="font-mono text-[10px] text-[#a9c3b1]">{nodes.length} nodes</div></div><div className="space-y-3">{nodes.map((item, index) => <button key={(item.node || "node") + index} onClick={() => setSelected(item)} className="flex w-full flex-wrap items-center gap-2 border border-[#53645c] bg-[#22302d] p-4 text-left transition hover:border-[#e5a182]"><span className="font-mono text-[10px] text-[#e5a182]">{String(index + 1).padStart(2, "0")}</span><span>Act</span><span className="text-[#e5a182]">?</span><span>{item.section || "Section"}</span><span className="text-[#e5a182]">?</span><span>p. {item.page ?? "?"}</span><span className="text-[#e5a182]">?</span><span className="truncate">{item.source || "Passage"}</span></button>)}</div></section><aside className="border border-[#293431] bg-[#1d2926] p-6 text-[#f4f0e8]"><div className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#e5a182]">Node inspector</div>{selected ? <><h2 className="mt-5 font-serif text-2xl">{selected.source || "Source passage"}</h2><div className="mt-2 font-mono text-[10px] text-[#a9c3b1]">Section {selected.section || "—"} · page {selected.page ?? "—"}</div><p className="mt-5 border-l-2 border-[#b96845] pl-4 font-serif text-[15px] leading-relaxed text-[#e5ddd2]">{selected.excerpt || "No excerpt returned by the graph endpoint."}</p><div className="mt-5 font-mono text-[10px] uppercase tracking-[0.1em] text-[#b7c8bc]">{selected.relationship || "Act ? Section ? Page ? Passage"}</div></> : <p className="mt-5 font-serif text-lg text-[#b7c8bc]">Select a live graph path to inspect it.</p>}</aside></div>}</div></main>;
}