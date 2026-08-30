import { useState, useMemo } from "react";

type GraphNode = { node?: string; type?: string; source?: string; page?: number | string; section?: string; excerpt?: string; relationship?: string };
type ExploreNode = { id: string; type?: string; [key: string]: unknown };
type ExploreEdge = { from: string; to: string; [key: string]: unknown };

export default function KnowledgeGraph() {
  const [mode, setMode] = useState<"search" | "browse">("search");

  // --- Search mode state (unchanged behavior) ---
  const [question, setQuestion] = useState("");
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [status, setStatus] = useState("not run");
  const [selected, setSelected] = useState<GraphNode | null>(null);

  // --- Browse mode state ---
  const [exploreNodes, setExploreNodes] = useState<ExploreNode[]>([]);
  const [exploreEdges, setExploreEdges] = useState<ExploreEdge[]>([]);
  const [exploreStatus, setExploreStatus] = useState<"idle" | "loading" | "loaded" | "error">("idle");
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [selectedNode, setSelectedNode] = useState<ExploreNode | null>(null);

  const apiBase = ((import.meta.env.VITE_VERIDOC_API_URL as string | undefined) || "http://127.0.0.1:8000").replace(/\/$/, "");

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

  async function loadExplore() {
    if (exploreStatus === "loaded" || exploreStatus === "loading") return;
    setExploreStatus("loading");
    try {
      const response = await fetch(apiBase + "/graph/explore");
      if (!response.ok) throw new Error("Explore API returned " + response.status);
      const payload = await response.json();
      setExploreNodes(Array.isArray(payload.nodes) ? payload.nodes : []);
      setExploreEdges(Array.isArray(payload.edges) ? payload.edges : []);
      setExploreStatus("loaded");
    } catch {
      setExploreNodes([]);
      setExploreEdges([]);
      setExploreStatus("error");
    }
  }

  function switchToBrowse() {
    setMode("browse");
    void loadExplore();
  }

  // Build id -> node lookup and parent -> children adjacency from the flat edge list
  const nodeById = useMemo(() => {
    const map = new Map<string, ExploreNode>();
    for (const n of exploreNodes) map.set(n.id, n);
    return map;
  }, [exploreNodes]);

  const childrenOf = useMemo(() => {
    const map = new Map<string, string[]>();
    for (const e of exploreEdges) {
      const list = map.get(e.from) || [];
      list.push(e.to);
      map.set(e.from, list);
    }
    return map;
  }, [exploreEdges]);

  const rootNodes = useMemo(
    () => exploreNodes.filter((n) => n.type === "Act" || n.type === "Company"),
    [exploreNodes]
  );

  function toggleExpanded(id: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function labelFor(n: ExploreNode): string {
    if (n.type === "Act") return String(n.title || n.source || "Act");
    if (n.type === "Company") return String(n.name || "Company");
    if (n.type === "Filing") return String(n.source || "Filing");
    if (n.type === "Article") return `Article ${n.article ?? "?"}`;
    if (n.type === "Section") return `Section ${n.section ?? "?"}`;
    if (n.type === "Page") return `Page ${n.page ?? "?"}`;
    if (n.type === "SourcePassage" || n.type === "CorpPassage") return String(n.excerpt || "Passage").slice(0, 60);
    return n.id;
  }

  function renderTree(nodeId: string, depth: number): React.ReactNode {
    const n = nodeById.get(nodeId);
    if (!n) return null;
    const kids = childrenOf.get(nodeId) || [];
    const isLeaf = kids.length === 0;
    const isOpen = expanded.has(nodeId);
    const isPassage = n.type === "SourcePassage" || n.type === "CorpPassage";

    return (
      <div key={nodeId} style={{ marginLeft: depth * 16 }}>
        <div
          className={
            "flex items-center gap-2 border-b border-[#293431] px-2 py-2 text-left transition hover:border-[#e5a182] cursor-pointer " +
            (selectedNode?.id === nodeId ? "bg-[#22302d]" : "")
          }
          onClick={() => {
            if (isPassage) {
              setSelectedNode(n);
            } else if (!isLeaf) {
              toggleExpanded(nodeId);
            }
          }}
        >
          {!isLeaf && (
            <span className="font-mono text-[10px] text-[#e5a182] w-3">{isOpen ? "-" : "+"}</span>
          )}
          {isLeaf && <span className="w-3" />}
          <span className="font-mono text-[9px] uppercase tracking-wide text-[#a9c3b1]">{n.type}</span>
          <span className="truncate text-sm">{labelFor(n)}</span>
        </div>
        {isOpen && !isLeaf && (
          <div>{kids.map((childId) => renderTree(childId, depth + 1))}</div>
        )}
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-[#f3efe7] px-5 py-10 text-[#1e2625] sm:px-10">
      <div className="mx-auto max-w-6xl">
        <div className="mb-8 flex items-end justify-between gap-4">
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#b96845]">VeriDoc / Knowledge Graph</div>
            <h1 className="mt-3 font-serif text-4xl">Act / Company → Section → Page → Passage</h1>
            <p className="mt-3 max-w-2xl font-serif text-lg text-[#5e665f]">
              {mode === "search" ? "Live graph context from the backend. Empty results remain honest." : "Browse the full graph structure directly."}
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setMode("search")}
              className={"font-mono text-[10px] uppercase tracking-[0.12em] px-4 py-2 border " + (mode === "search" ? "bg-[#1e2625] text-[#f8f5ef] border-[#1e2625]" : "border-[#b9aea0] text-[#5e665f]")}
            >
              Ask a question
            </button>
            <button
              onClick={switchToBrowse}
              className={"font-mono text-[10px] uppercase tracking-[0.12em] px-4 py-2 border " + (mode === "browse" ? "bg-[#1e2625] text-[#f8f5ef] border-[#1e2625]" : "border-[#b9aea0] text-[#5e665f]")}
            >
              Browse graph
            </button>
          </div>
        </div>

        {mode === "search" && (
          <>
            <div className="mb-8 flex flex-col gap-3 sm:flex-row">
              <input
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Ask about an Act, section, page, or passage"
                className="min-h-12 flex-1 border border-[#b9aea0] bg-[#fffdf8] px-4 font-serif text-base outline-none focus:border-[#b96845]"
              />
              <button
                onClick={inspectGraph}
                disabled={status === "loading"}
                className="bg-[#1e2625] px-6 py-3 font-mono text-[10px] uppercase tracking-[0.14em] text-[#f8f5ef] disabled:opacity-50"
              >
                {status === "loading" ? "Inspecting..." : "Inspect graph"}
              </button>
            </div>
            {nodes.length === 0 ? (
              <section className="border border-[#d9d1c4] bg-[#f8f5ef] p-8">
                <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#b96845]">Graph status</div>
                <h2 className="mt-4 font-serif text-3xl">{status === "not run" ? "Run a graph inspection" : status}</h2>
                <p className="mt-4 font-serif text-lg text-[#5e665f]">No invented nodes are shown. The current graph store may not contain a matching path for this question.</p>
              </section>
            ) : (
              <div className="grid gap-5 lg:grid-cols-[1.15fr_0.85fr]">
                <section className="border border-[#293431] bg-[#17211f] p-6 text-[#f4f0e8] shadow-[6px_6px_0_#b96845]">
                  <div className="mb-6 flex items-center justify-between">
                    <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#e5a182]">Live graph paths</div>
                    <div className="font-mono text-[10px] text-[#a9c3b1]">{nodes.length} nodes</div>
                  </div>
                  <div className="space-y-3">
                    {nodes.map((item, index) => (
                      <button
                        key={(item.node || "node") + index}
                        onClick={() => setSelected(item)}
                        className="flex w-full flex-wrap items-center gap-2 border border-[#53645c] bg-[#22302d] p-4 text-left transition hover:border-[#e5a182]"
                      >
                        <span className="font-mono text-[10px] text-[#e5a182]">{String(index + 1).padStart(2, "0")}</span>
                        <span>Act</span>
                        <span className="text-[#e5a182]">→</span>
                        <span>{item.section || "Section"}</span>
                        <span className="text-[#e5a182]">→</span>
                        <span>p. {item.page ?? "?"}</span>
                        <span className="text-[#e5a182]">→</span>
                        <span className="truncate">{item.source || "Passage"}</span>
                      </button>
                    ))}
                  </div>
                </section>
                <aside className="border border-[#293431] bg-[#1d2926] p-6 text-[#f4f0e8]">
                  <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#e5a182]">Node inspector</div>
                  {selected ? (
                    <>
                      <h2 className="mt-5 font-serif text-2xl">{selected.source || "Source passage"}</h2>
                      <div className="mt-2 font-mono text-[10px] text-[#a9c3b1]">Section {selected.section || "?"} → page {selected.page ?? "?"}</div>
                      <p className="mt-5 border-l-2 border-[#b96845] pl-4 font-serif text-[15px] leading-relaxed text-[#e5ddd2]">{selected.excerpt || "No excerpt returned by the graph endpoint."}</p>
                      <div className="mt-5 font-mono text-[10px] uppercase tracking-[0.1em] text-[#b7c8bc]">{selected.relationship || "Act → Section → Page → Passage"}</div>
                    </>
                  ) : (
                    <p className="mt-5 font-serif text-lg text-[#b7c8bc]">Select a live graph path to inspect it.</p>
                  )}
                </aside>
              </div>
            )}
          </>
        )}

        {mode === "browse" && (
          <div className="grid gap-5 lg:grid-cols-[1.15fr_0.85fr]">
            <section className="border border-[#293431] bg-[#17211f] p-6 text-[#f4f0e8] shadow-[6px_6px_0_#b96845] max-h-[70vh] overflow-y-auto">
              <div className="mb-6 flex items-center justify-between">
                <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#e5a182]">Graph tree</div>
                <div className="font-mono text-[10px] text-[#a9c3b1]">
                  {exploreStatus === "loading" && "loading..."}
                  {exploreStatus === "loaded" && `${exploreNodes.length} nodes / ${exploreEdges.length} edges`}
                  {exploreStatus === "error" && "API unavailable"}
                </div>
              </div>
              {exploreStatus === "loaded" && rootNodes.length === 0 && (
                <p className="font-serif text-lg text-[#b7c8bc]">No Act or Company root nodes found in the graph.</p>
              )}
              {exploreStatus === "loaded" && rootNodes.map((root) => renderTree(root.id, 0))}
            </section>
            <aside className="border border-[#293431] bg-[#1d2926] p-6 text-[#f4f0e8]">
              <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#e5a182]">Node inspector</div>
              {selectedNode ? (
                <>
                  <h2 className="mt-5 font-serif text-2xl">{String(selectedNode.type)}</h2>
                  <div className="mt-2 font-mono text-[10px] text-[#a9c3b1]">
                    {selectedNode.source ? String(selectedNode.source) : ""} {selectedNode.page !== undefined ? `→ page ${selectedNode.page}` : ""}
                  </div>
                  <p className="mt-5 border-l-2 border-[#b96845] pl-4 font-serif text-[15px] leading-relaxed text-[#e5ddd2]">
                    {String(selectedNode.excerpt || "No excerpt on this node.")}
                  </p>
                </>
              ) : (
                <p className="mt-5 font-serif text-lg text-[#b7c8bc]">Click an Act or Company to expand it, then select a passage to inspect it.</p>
              )}
            </aside>
          </div>
        )}
      </div>
    </main>
  );
}
