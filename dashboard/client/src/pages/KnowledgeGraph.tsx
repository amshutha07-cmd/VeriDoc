/* Knowledge graph. Same two modes and endpoints as before:
   Ask a question -> POST {API}/graph/search, Browse graph -> GET {API}/graph/explore.
   When no API URL is set the page still tries http://127.0.0.1:8000, as the earlier version did. */
import { useMemo, useState, type ReactNode } from "react";
import PageHero from "@/components/PageHero";

type GraphNode = { node?: string; type?: string; source?: string; page?: number | string; section?: string; excerpt?: string; relationship?: string };
type ExploreNode = { id: string; type?: string; [key: string]: unknown };
type ExploreEdge = { from: string; to: string; [key: string]: unknown };

const limeButton = "h-12 bg-lime px-6 text-[13px] font-extrabold uppercase tracking-[0.04em] text-lime-ink hover:bg-[#e2ff6e] disabled:opacity-50";

function PaperCard({ children }: { children: ReactNode }) {
  return <p className="mt-4 border-l-4 border-lime bg-paper px-4 py-3 font-serif text-[15px] leading-relaxed text-[#1c1c1c]">{children}</p>;
}

export default function KnowledgeGraph() {
  const [mode, setMode] = useState<"search" | "browse">("search");

  // Search mode
  const [question, setQuestion] = useState("");
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [status, setStatus] = useState("not run");
  const [selected, setSelected] = useState<GraphNode | null>(null);

  // Browse mode
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

  const rootNodes = useMemo(() => exploreNodes.filter((n) => n.type === "Act" || n.type === "Company"), [exploreNodes]);

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

  function renderTree(nodeId: string, depth: number, trail: Set<string> = new Set()): ReactNode {
    const n = nodeById.get(nodeId);
    if (!n || trail.has(nodeId)) return null; // guards against a cycle in the edge list
    const kids = childrenOf.get(nodeId) || [];
    const isLeaf = kids.length === 0;
    const isOpen = expanded.has(nodeId);
    const isPassage = n.type === "SourcePassage" || n.type === "CorpPassage";
    const isSelected = selectedNode?.id === nodeId;
    const nextTrail = new Set(trail).add(nodeId);
    const clickable = isPassage || !isLeaf;

    return (
      <li key={nodeId}>
        <button
          type="button"
          disabled={!clickable}
          aria-expanded={!isLeaf ? isOpen : undefined}
          onClick={() => {
            if (isPassage) setSelectedNode(n);
            else if (!isLeaf) toggleExpanded(nodeId);
          }}
          style={{ paddingLeft: 12 + depth * 18 }}
          className={`flex min-h-11 w-full items-center gap-3 border-b border-line-soft py-2 pr-3 text-left ${clickable ? "hover:bg-tint" : "cursor-default"} ${isSelected ? "bg-tint" : ""}`}
        >
          <span aria-hidden className={`w-3 shrink-0 font-mono text-[15px] ${isOpen ? "text-coral" : "text-lime"}`}>
            {isLeaf ? "" : isOpen ? "−" : "+"}
          </span>
          <span className="w-[92px] shrink-0 font-mono text-[10px] uppercase tracking-[0.08em] text-mute">{n.type}</span>
          <span className={`min-w-0 truncate text-[15px] ${isSelected ? "font-bold text-lime" : ""}`}>{labelFor(n)}</span>
        </button>
        {isOpen && !isLeaf && <ul>{kids.map((childId) => renderTree(childId, depth + 1, nextTrail))}</ul>}
      </li>
    );
  }

  const tab = (active: boolean) => `h-11 px-5 text-[13px] font-extrabold uppercase tracking-[0.04em] ${active ? "bg-lime text-lime-ink" : "border border-white/70 text-white hover:bg-white/10"}`;

  return (
    <div className="flex flex-col gap-3">
      <PageHero eyebrow="Knowledge graph" title="Act ▶ Article ▶ Page ▶ Passage">
        {mode === "search" ? "Live graph context from the backend. Empty results remain honest." : "Browse the full graph structure directly."}
      </PageHero>

      <div className="flex flex-wrap gap-2" role="group" aria-label="Graph mode">
        <button onClick={switchToBrowse} aria-pressed={mode === "browse"} className={mode === "browse" ? "h-11 bg-lime px-5 text-[13px] font-extrabold uppercase tracking-[0.04em] text-lime-ink" : "h-11 border border-edge px-5 text-[13px] font-extrabold uppercase tracking-[0.04em] hover:border-fg"}>
          Browse graph
        </button>
        <button onClick={() => setMode("search")} aria-pressed={mode === "search"} className={mode === "search" ? "h-11 bg-lime px-5 text-[13px] font-extrabold uppercase tracking-[0.04em] text-lime-ink" : "h-11 border border-edge px-5 text-[13px] font-extrabold uppercase tracking-[0.04em] hover:border-fg"}>
          Ask a question
        </button>
      </div>

      {mode === "search" && (
        <>
          <form
            className="flex flex-col gap-2 sm:flex-row"
            onSubmit={(event) => {
              event.preventDefault();
              void inspectGraph();
            }}
          >
            <label htmlFor="graph-question" className="sr-only">
              Ask about an Act, section, page, or passage
            </label>
            <input
              id="graph-question"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ask about an Act, section, page, or passage"
              className="h-12 flex-1 border border-edge bg-sunken px-4 text-[16px] text-fg outline-none placeholder:text-mute focus:border-lime"
            />
            <button type="submit" disabled={status === "loading"} className={limeButton}>
              {status === "loading" ? "Inspecting…" : "Inspect graph"}
            </button>
          </form>

          {nodes.length === 0 ? (
            <section className="border border-line bg-sunken px-5 py-6" aria-live="polite">
              <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-mute">Graph status</div>
              <h2 className={`mt-2 text-[28px] font-extrabold tracking-[-0.02em] ${status === "API unavailable" ? "text-coral" : ""}`}>{status === "not run" ? "Run a graph inspection" : status}</h2>
              <p className="mt-2 max-w-[620px] text-[15px] leading-snug text-soft">No invented nodes are shown. The current graph store may not contain a matching path for this question.</p>
            </section>
          ) : (
            <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,420px)] lg:items-start">
              <section className="border border-line bg-sunken">
                <div className="flex items-center justify-between border-b border-line px-4 py-3 font-mono text-[11px] uppercase tracking-[0.12em] text-mute">
                  <span>Live graph paths</span>
                  <span>{nodes.length} nodes</span>
                </div>
                <ul>
                  {nodes.map((item, index) => (
                    <li key={(item.node || "node") + index}>
                      <button
                        onClick={() => setSelected(item)}
                        aria-pressed={selected === item}
                        className={`flex min-h-14 w-full flex-wrap items-center gap-x-2.5 gap-y-1 border-b border-line-soft px-4 py-3 text-left hover:bg-tint ${selected === item ? "bg-tint" : ""}`}
                      >
                        <span className="font-mono text-[12px] text-lime">{String(index + 1).padStart(2, "0")}</span>
                        <span className="text-[15px]">Act</span>
                        <span aria-hidden className="text-lime">▶</span>
                        <span className="text-[15px]">{item.section || "Section"}</span>
                        <span aria-hidden className="text-lime">▶</span>
                        <span className="text-[15px]">p. {item.page ?? "?"}</span>
                        <span aria-hidden className="text-lime">▶</span>
                        <span className="min-w-0 truncate text-[15px] font-semibold">{item.source || "Passage"}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              </section>

              <aside className="border border-line bg-panel px-5 py-4" aria-live="polite">
                <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-mute">Node inspector</div>
                {selected ? (
                  <>
                    <h2 className="mt-3 text-[22px] font-extrabold leading-tight tracking-[-0.01em]">{selected.source || "Source passage"}</h2>
                    <div className="mt-1 font-mono text-[12px] text-mute">
                      Section {selected.section || "?"} ▶ page {selected.page ?? "?"}
                    </div>
                    <PaperCard>{selected.excerpt || "No excerpt returned by the graph endpoint."}</PaperCard>
                    <div className="mt-4 font-mono text-[11px] uppercase tracking-[0.08em] text-mute">{selected.relationship || "Act → Section → Page → Passage"}</div>
                  </>
                ) : (
                  <p className="mt-3 text-[15px] leading-snug text-soft">Select a live graph path to inspect it.</p>
                )}
              </aside>
            </div>
          )}
        </>
      )}

      {mode === "browse" && (
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,420px)] lg:items-start">
          <section className="border border-line bg-sunken">
            <div className="flex items-center justify-between border-b border-line px-4 py-3 font-mono text-[11px] uppercase tracking-[0.12em] text-mute">
              <span>Graph tree</span>
              <span className={exploreStatus === "error" ? "text-coral" : ""} aria-live="polite">
                {exploreStatus === "loading" && "loading…"}
                {exploreStatus === "loaded" && `${exploreNodes.length} nodes / ${exploreEdges.length} edges`}
                {exploreStatus === "error" && "API unavailable"}
              </span>
            </div>
            <div className="max-h-[70vh] overflow-y-auto">
              {exploreStatus === "loaded" && rootNodes.length === 0 && <p className="px-4 py-6 text-[15px] text-mute">No Act or Company root nodes found in the graph.</p>}
              {exploreStatus === "error" && <p className="px-4 py-6 text-[15px] text-mute">The graph could not be loaded. Check that the backend is running.</p>}
              {exploreStatus === "loaded" && <ul>{rootNodes.map((root) => renderTree(root.id, 0))}</ul>}
            </div>
          </section>

          <aside className="border border-line bg-panel px-5 py-4" aria-live="polite">
            <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-mute">Node inspector</div>
            {selectedNode ? (
              <>
                <h2 className="mt-3 text-[22px] font-extrabold tracking-[-0.01em]">{String(selectedNode.type)}</h2>
                <div className="mt-1 font-mono text-[12px] text-mute">
                  {selectedNode.source ? String(selectedNode.source) : ""} {selectedNode.page !== undefined ? `▶ page ${selectedNode.page}` : ""}
                </div>
                <PaperCard>{String(selectedNode.excerpt || "No excerpt on this node.")}</PaperCard>
              </>
            ) : (
              <p className="mt-3 text-[15px] leading-snug text-soft">Click an Act or Company to expand it, then select a passage to inspect it.</p>
            )}
          </aside>
        </div>
      )}
    </div>
  );
}
