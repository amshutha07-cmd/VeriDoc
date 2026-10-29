/* Ingestion monitor. Counts come from GET {API}/ingest/stats. "This session" shows what was uploaded in this browser tab, as reported by POST {API}/ingest. */
import { Plus } from "lucide-react";
import Counter from "@/components/Counter";
import PageHero from "@/components/PageHero";
import { useUpload } from "@/contexts/UploadContext";
import { formatCount } from "@/lib/api";
import { useIngestStats } from "@/lib/useIngestStats";

const STEPS = [
  { title: "Fingerprint", body: "A SHA-256 hash of the file, kept with its passages." },
  { title: "Extract", body: "Text and page numbers from a PDF or DOCX file." },
  { title: "Chunk", body: "Split into passages. Each one keeps its file and page." },
  { title: "Embed", body: "Indian law uses 1,536 dimensions. Corporate uses 384." },
  { title: "Index", body: "Stored in the collection that matches the domain you picked." },
];

const COLLECTION: Record<string, string> = { legal: "Indian law", corporate: "Corporate / handbook" };

export default function IngestionJobs() {
  const { status, error, legalChunks, corporateChunks } = useIngestStats();
  const { items, lastResult, openDialog } = useUpload();

  return (
    <div className="flex flex-col gap-3">
      <PageHero eyebrow="Ingestion monitor" title="From file to indexed evidence.">
        An upload finishes in one request. This page shows what is indexed now and how each file gets there.
      </PageHero>

      {(status === "error" || status === "nobackend") && (
        <div role="alert" className="border border-coral px-5 py-4 text-[15px] leading-snug text-coral">
          {status === "nobackend" ? "VITE_VERIDOC_API_URL is not configured." : error}
        </div>
      )}

      <div className="grid gap-3 md:grid-cols-2">
        <Counter label="Indian law" value={status === "loading" ? "…" : formatCount(legalChunks)} accent note={<>persisted chunks<br />1,536 dimensions</>} />
        <Counter label="Handbook / corporate" value={status === "loading" ? "…" : formatCount(corporateChunks)} note={<>persisted chunks<br />384 dimensions</>} />
      </div>

      <ol className="grid border border-line bg-sunken sm:grid-cols-2 lg:grid-cols-5">
        {STEPS.map((step, index) => (
          <li key={step.title} className="border-b border-line p-4 last:border-b-0 sm:border-r lg:border-b-0 lg:last:border-r-0">
            <span className="flex h-[30px] w-[30px] items-center justify-center bg-lime text-[16px] font-black text-lime-ink">{index + 1}</span>
            <div className="mt-3 text-[22px] font-extrabold tracking-[-0.01em]">{step.title}</div>
            <p className="mt-1.5 text-[14px] leading-snug text-soft">{step.body}</p>
          </li>
        ))}
      </ol>

      <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,420px)]">
        <section aria-labelledby="session-heading" className="flex flex-col border border-line bg-sunken">
          <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-3">
            <h2 id="session-heading" className="font-mono text-[11px] uppercase tracking-[0.12em] text-mute">
              This session
            </h2>
            <span className="font-mono text-[11px] text-mute">Not saved on the server</span>
          </div>

          {items.length === 0 ? (
            <div className="px-4 py-6">
              <p className="text-[15px] leading-snug text-mute">Nothing has been uploaded in this tab yet.</p>
              <button onClick={openDialog} className="mt-3 flex h-11 items-center gap-2 bg-lime px-4 text-[13px] font-extrabold uppercase tracking-[0.04em] text-lime-ink hover:bg-[#e2ff6e]">
                <Plus className="h-4 w-4" strokeWidth={2.4} /> Add documents
              </button>
            </div>
          ) : (
            <ul>
              {items.map((item) => (
                <li key={item.id} className="flex min-h-[56px] items-center gap-4 border-b border-line-soft px-4 py-2.5">
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-[15px] font-semibold">{item.name}</span>
                    <span className="block font-mono text-[10px] uppercase tracking-[0.08em] text-mute">{COLLECTION[item.domain]}</span>
                    {item.status === "failed" && item.message && <span className="mt-0.5 block text-[13px] leading-snug text-coral">{item.message}</span>}
                  </span>
                  <span className={`flex shrink-0 items-center gap-2 text-[13px] ${item.status === "failed" ? "text-coral" : ""}`}>
                    <span className={`h-2 w-2 ${item.status === "indexed" ? "bg-lime" : item.status === "failed" ? "bg-coral" : "animate-pulse border border-lime"}`} />
                    {item.status === "indexed" ? "Indexed" : item.status === "failed" ? "Failed" : "Indexing"}
                  </span>
                </li>
              ))}
            </ul>
          )}

          {lastResult && (
            <p className="mt-auto border-t border-line px-4 py-3 text-[14px] leading-relaxed text-soft">
              Last result: <b className="text-fg">{formatCount(lastResult.pages)}</b> pages and <b className="text-fg">{formatCount(lastResult.chunks)}</b> chunks added to {COLLECTION[lastResult.domain]}
              {typeof lastResult.totalChunks === "number" ? <>. That collection now holds <b className="text-fg">{formatCount(lastResult.totalChunks)}</b> chunks.</> : "."}
            </p>
          )}
        </section>

        <aside className="flex flex-col gap-2.5 border border-dashed border-edge p-5">
          <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-coral">Not available yet</div>
          <div className="text-[22px] font-extrabold tracking-[-0.01em]">What this page cannot show</div>
          {["Past uploads", "Cancel and retry", "Progress for each file"].map((label) => (
            <div key={label} className="flex h-10 items-center border border-dashed border-edge px-3.5 text-[14px] text-soft">
              {label}
            </div>
          ))}
          <p className="mt-1 text-[14px] leading-snug text-mute">
            Uploads complete synchronously through the current API. Historical job records, cancellation, retry controls, and per-file progress are not yet exposed.
          </p>
        </aside>
      </div>
    </div>
  );
}
