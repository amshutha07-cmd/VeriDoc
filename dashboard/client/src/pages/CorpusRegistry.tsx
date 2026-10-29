/* Corpus registry. Chunk counts come from GET {API}/ingest/stats, as before.
   The document list is read from GET {API}/graph/explore: every Act or Company is one row, and its fingerprint is the SHA-256 the graph stored on its pages. */
import { useEffect, useMemo, useState } from "react";
import { Plus } from "lucide-react";
import Counter from "@/components/Counter";
import PageHero from "@/components/PageHero";
import { useUpload } from "@/contexts/UploadContext";
import { API_BASE, errorDetail, formatCount } from "@/lib/api";
import { useIngestStats } from "@/lib/useIngestStats";

type GraphNode = { id: string; type?: string; [key: string]: unknown };
type GraphEdge = { from: string; to: string; [key: string]: unknown };
type Collection = "Legal" | "Corporate";
type DocRow = { id: string; title: string; file?: string; collection: Collection; fingerprint?: string };
type DocsState = { status: "idle" | "loading" | "ready" | "error"; rows: DocRow[]; error?: string };
type Filter = "All" | Collection;

const text = (value: unknown): string | undefined => (typeof value === "string" && value.trim() ? value.trim() : undefined);

/** Finds the first SHA-256 stored on a document's pages or passages. Stops after a few hundred nodes. */
function findFingerprint(rootId: string, byId: Map<string, GraphNode>, children: Map<string, string[]>): string | undefined {
  const seen = new Set<string>([rootId]);
  const queue = [rootId];
  while (queue.length && seen.size < 500) {
    const id = queue.shift() as string;
    const hash = text(byId.get(id)?.sha256);
    if (hash) return hash;
    for (const next of children.get(id) ?? []) {
      if (!seen.has(next)) {
        seen.add(next);
        queue.push(next);
      }
    }
  }
  return undefined;
}

function buildRows(nodes: GraphNode[], edges: GraphEdge[]): DocRow[] {
  const byId = new Map(nodes.map((node) => [node.id, node]));
  const children = new Map<string, string[]>();
  for (const edge of edges) {
    const list = children.get(edge.from) ?? [];
    list.push(edge.to);
    children.set(edge.from, list);
  }
  return nodes
    .filter((node) => node.type === "Act" || node.type === "Company")
    .map((node) => ({
      id: node.id,
      title: node.type === "Act" ? text(node.title) ?? text(node.source) ?? "Act" : text(node.name) ?? "Company",
      file: text(node.source),
      collection: (node.type === "Act" ? "Legal" : "Corporate") as Collection,
      fingerprint: findFingerprint(node.id, byId, children),
    }));
}

const shortHash = (hash: string) => (hash.length > 14 ? `${hash.slice(0, 8)}…${hash.slice(-4)}` : hash);

export default function CorpusRegistry() {
  const { status, error, legalChunks, corporateChunks } = useIngestStats();
  const { openDialog, ingestVersion } = useUpload();
  const [docs, setDocs] = useState<DocsState>({ status: API_BASE ? "loading" : "idle", rows: [] });
  const [filter, setFilter] = useState<Filter>("All");

  useEffect(() => {
    if (!API_BASE) return;
    let cancelled = false;
    setDocs((current) => ({ ...current, status: current.status === "ready" ? "ready" : "loading" }));
    fetch(`${API_BASE}/graph/explore`)
      .then(async (response) => {
        if (!response.ok) throw new Error(await errorDetail(response));
        return response.json();
      })
      .then((data) => {
        if (cancelled) return;
        const nodes: GraphNode[] = Array.isArray(data?.nodes) ? data.nodes : [];
        const edges: GraphEdge[] = Array.isArray(data?.edges) ? data.edges : [];
        setDocs({ status: "ready", rows: buildRows(nodes, edges) });
      })
      .catch((reason) => {
        if (cancelled) return;
        setDocs({ status: "error", rows: [], error: reason instanceof Error ? reason.message : "Could not read the graph." });
      });
    return () => {
      cancelled = true;
    };
  }, [ingestVersion]);

  const visible = useMemo(() => (filter === "All" ? docs.rows : docs.rows.filter((row) => row.collection === filter)), [docs.rows, filter]);
  const legalDocs = docs.rows.filter((row) => row.collection === "Legal").length;
  const corporateDocs = docs.rows.filter((row) => row.collection === "Corporate").length;
  const fingerprinted = docs.rows.filter((row) => row.fingerprint).length;

  const loadError = status === "error" ? error : status === "nobackend" ? "VITE_VERIDOC_API_URL is not configured." : null;

  return (
    <div className="flex flex-col gap-3">
      <PageHero eyebrow="Corpus registry" title="What the corpus holds.">
        Live collection health from the connected backend. Counts are read from Chroma, not mocked in the interface.
      </PageHero>

      {loadError && (
        <div role="alert" className="border border-coral px-5 py-4 text-[15px] leading-snug text-coral">
          Could not load live registry data: {loadError}
        </div>
      )}

      <div className="grid gap-3 md:grid-cols-2">
        <Counter label="Indian law" value={status === "loading" ? "…" : formatCount(legalChunks)} accent note={<>persisted chunks<br />1,536 dimensions</>} />
        <Counter label="Handbook / corporate" value={status === "loading" ? "…" : formatCount(corporateChunks)} note={<>persisted chunks<br />384 dimensions</>} />
      </div>

      <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_340px] lg:items-start">
        <section aria-labelledby="documents-heading" className="border border-line bg-sunken">
          <div className="flex items-center justify-between border-b border-line px-4 py-3">
            <h2 id="documents-heading" className="font-mono text-[11px] uppercase tracking-[0.12em] text-mute">
              Documents &nbsp;·&nbsp; {visible.length}
            </h2>
          </div>

          <div className="hidden grid-cols-[minmax(0,1fr)_110px_minmax(0,200px)_150px] gap-4 border-b border-line px-4 py-2.5 font-mono text-[11px] uppercase tracking-[0.12em] text-mute sm:grid">
            <span>Document</span>
            <span>Collection</span>
            <span>File</span>
            <span>Fingerprint</span>
          </div>

          {docs.status === "loading" && <p className="px-4 py-6 text-[15px] text-mute">Reading the graph…</p>}
          {docs.status === "idle" && <p className="px-4 py-6 text-[15px] text-mute">Connect a backend to list the documents in the corpus.</p>}
          {docs.status === "error" && (
            <p className="px-4 py-6 text-[15px] leading-snug text-mute">
              The document list needs the graph store ({docs.error}). The chunk counts above are not affected.
            </p>
          )}
          {docs.status === "ready" && docs.rows.length === 0 && (
            <div className="px-4 py-6">
              <p className="text-[15px] leading-snug text-mute">No Acts or companies are in the graph yet.</p>
              <button onClick={openDialog} className="mt-3 h-10 bg-lime px-4 text-[13px] font-extrabold uppercase tracking-[0.04em] text-lime-ink hover:bg-[#e2ff6e]">
                Add documents
              </button>
            </div>
          )}

          <ul>
            {visible.map((row) => (
              <li key={row.id} className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-4 gap-y-1 border-b border-line-soft px-4 py-3 last:border-b-0 sm:grid-cols-[minmax(0,1fr)_110px_minmax(0,200px)_150px] sm:py-3.5">
                <span className="min-w-0 truncate text-[15px] font-semibold">{row.title}</span>
                <span className={`text-right text-[13px] sm:text-left ${row.collection === "Legal" ? "text-lime" : "text-peri"}`}>{row.collection}</span>
                <span className="col-span-2 min-w-0 truncate font-mono text-[12px] text-mute sm:col-span-1">{row.file ?? "—"}</span>
                <span className="col-span-2 font-mono text-[12px] text-mute sm:col-span-1" title={row.fingerprint}>
                  {row.fingerprint ? shortHash(row.fingerprint) : "not recorded"}
                </span>
              </li>
            ))}
          </ul>
        </section>

        <aside className="flex flex-col gap-3">
          <div className="border border-line bg-panel px-5 py-4">
            <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-mute">Show</div>
            <div className="mt-3 flex flex-wrap gap-2" role="group" aria-label="Filter documents by collection">
              {(
                [
                  ["All", docs.rows.length],
                  ["Legal", legalDocs],
                  ["Corporate", corporateDocs],
                ] as [Filter, number][]
              ).map(([value, count]) => (
                <button
                  key={value}
                  onClick={() => setFilter(value)}
                  aria-pressed={filter === value}
                  className={`h-10 px-4 text-[14px] ${filter === value ? "bg-lime font-extrabold text-lime-ink" : "border border-edge text-fg hover:border-fg"}`}
                >
                  {value} &nbsp;{count}
                </button>
              ))}
            </div>
          </div>

          <div className="border border-line bg-panel px-5 py-4">
            <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-mute">Fingerprints recorded</div>
            <div className="mt-2 text-[clamp(2.5rem,6vw,3.5rem)] font-black leading-none tracking-[-0.04em] text-lime">
              {docs.status === "ready" ? `${fingerprinted} of ${docs.rows.length}` : "—"}
            </div>
            <p className="mt-2 text-[14px] leading-snug text-soft">documents have a SHA-256 stored in the graph. This page reads them. It cannot re-check a file against them yet.</p>
          </div>

          <div className="border border-line bg-panel px-5 py-4">
            <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-mute">Registry note</div>
            <p className="mt-2 text-[14px] leading-relaxed text-soft">
              The legal and handbook collections use different embedding dimensions and must remain separate. New uploads should be routed to the collection matching their selected domain.
            </p>
          </div>

          <div className="border border-dashed border-edge px-5 py-4">
            <div className="text-[18px] font-extrabold tracking-[-0.01em]">Missing a source?</div>
            <p className="mt-1.5 text-[14px] leading-snug text-mute">Add Acts, rules, judgments or company filings. New files are indexed into the collection you pick.</p>
            <button onClick={openDialog} className="mt-3 flex h-11 items-center gap-2 bg-lime px-4 text-[13px] font-extrabold uppercase tracking-[0.04em] text-lime-ink hover:bg-[#e2ff6e]">
              <Plus className="h-4 w-4" strokeWidth={2.4} /> Add documents
            </button>
          </div>
        </aside>
      </div>
    </div>
  );
}
