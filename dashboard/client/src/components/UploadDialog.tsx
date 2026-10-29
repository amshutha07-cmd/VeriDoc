/* "Add documents". Opens from the header on every page. Sends files to the backend through UploadContext. */
import { useState } from "react";
import { FileUp, ShieldCheck, X } from "lucide-react";
import Modal from "@/components/Modal";
import { useUpload, type UploadDomain, type UploadItem } from "@/contexts/UploadContext";
import { HAS_BACKEND, formatCount } from "@/lib/api";

const COLLECTION_NAME: Record<UploadDomain, string> = { legal: "Indian law", corporate: "Corporate / handbook" };

function StatusCell({ item }: { item: UploadItem }) {
  if (item.status === "indexed") {
    return (
      <span className="flex w-24 shrink-0 items-center justify-end gap-2 text-[13px]">
        <span className="h-2 w-2 bg-lime" /> Indexed
      </span>
    );
  }
  if (item.status === "failed") {
    return (
      <span className="flex w-24 shrink-0 items-center justify-end gap-2 text-[13px] text-coral">
        <span className="h-2 w-2 bg-coral" /> Failed
      </span>
    );
  }
  return (
    <span className="flex w-24 shrink-0 items-center justify-end gap-2 text-[13px] text-soft">
      <span className="h-2 w-2 animate-pulse border border-lime" /> Indexing
    </span>
  );
}

function Bar({ status }: { status: UploadItem["status"] }) {
  if (status === "indexed") return <span className="h-1.5 w-24 shrink-0 bg-lime sm:w-28" />;
  if (status === "failed") return <span className="h-1.5 w-24 shrink-0 bg-coral sm:w-28" />;
  return (
    <span className="relative h-1.5 w-24 shrink-0 overflow-hidden bg-line sm:w-28">
      <span className="absolute inset-y-0 left-0 w-2/5 animate-pulse bg-lime" />
    </span>
  );
}

export default function UploadDialog() {
  const { dialogOpen, closeDialog, domain, setDomain, addFiles, items, lastResult, uploading } = useUpload();
  const [dragging, setDragging] = useState(false);

  return (
    <Modal open={dialogOpen} onClose={closeDialog} label="Add source documents" className="max-w-[660px]">
      <div className="p-6 sm:px-8 sm:py-7">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-lime">Add documents</div>
            <h2 className="mt-2 text-[32px] font-black leading-none tracking-[-0.03em] sm:text-4xl">Add source documents</h2>
          </div>
          <button onClick={closeDialog} aria-label="Close" className="-mr-2 -mt-2 flex h-11 w-11 shrink-0 items-center justify-center text-fg hover:text-lime">
            <X className="h-5 w-5" />
          </button>
        </div>
        <p className="mt-3 max-w-[520px] text-[15px] leading-relaxed text-soft">
          Add Acts, rules, amendments or judgments. Each file is fingerprinted, read and indexed without rebuilding the corpus.
        </p>

        {!HAS_BACKEND && (
          <div role="status" className="mt-4 border border-coral px-4 py-3 text-[14px] leading-snug text-coral">
            No backend is connected, so files cannot be indexed from this workspace yet.
          </div>
        )}

        <label htmlFor="upload-domain" className="mt-6 block font-mono text-[11px] uppercase tracking-[0.12em] text-mute">
          Collection
        </label>
        <select
          id="upload-domain"
          value={domain}
          onChange={(event) => setDomain(event.target.value as UploadDomain)}
          disabled={uploading}
          className="mt-2 h-12 w-full border-[1.5px] border-fg bg-ink px-3 text-[15px] text-fg disabled:opacity-60"
        >
          <option value="legal">Indian law collection</option>
          <option value="corporate">Corporate / handbook collection</option>
        </select>

        <label
          htmlFor="upload-files"
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setDragging(false);
            void addFiles(event.dataTransfer.files);
          }}
          className={`mt-4 flex cursor-pointer flex-col items-center justify-center border-2 border-dashed px-5 py-7 text-center transition-colors ${
            dragging ? "border-lime bg-tint" : "border-lime"
          } ${uploading ? "pointer-events-none opacity-60" : ""}`}
        >
          <input
            id="upload-files"
            type="file"
            accept="application/pdf,.pdf,.docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            multiple
            className="sr-only"
            disabled={uploading}
            onChange={(event) => {
              void addFiles(event.target.files);
              event.target.value = "";
            }}
          />
          <FileUp className="h-7 w-7 text-lime" strokeWidth={1.8} />
          <span className="mt-2 text-[18px] font-extrabold">Drop PDFs or DOCX files here</span>
          <span className="mt-1 font-mono text-[11px] uppercase tracking-[0.1em] text-mute">PDF · DOCX · more than one file is fine</span>
        </label>

        {items.length > 0 && (
          <>
            <div className="mt-5 font-mono text-[11px] uppercase tracking-[0.12em] text-mute">This session</div>
            <ul className="mt-2 max-h-[220px] overflow-y-auto border-t border-line" aria-live="polite">
              {items.map((item) => (
                <li key={item.id} className="flex min-h-[52px] items-center gap-3 border-b border-line py-2 sm:gap-4">
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-[15px] font-semibold">{item.name}</span>
                    <span className="block font-mono text-[10px] uppercase tracking-[0.08em] text-mute">{COLLECTION_NAME[item.domain]}</span>
                    {item.status === "failed" && item.message && <span className="mt-0.5 block text-[13px] leading-snug text-coral">{item.message}</span>}
                  </span>
                  <Bar status={item.status} />
                  <StatusCell item={item} />
                </li>
              ))}
            </ul>
          </>
        )}

        {lastResult && (
          <p className="mt-4 text-[14px] leading-relaxed text-soft">
            Last upload added <b className="text-fg">{formatCount(lastResult.pages)}</b> pages and <b className="text-fg">{formatCount(lastResult.chunks)}</b> chunks to the {COLLECTION_NAME[lastResult.domain]} collection
            {typeof lastResult.totalChunks === "number" ? <>, which now holds <b className="text-fg">{formatCount(lastResult.totalChunks)}</b> chunks.</> : "."}
          </p>
        )}

        <div className="mt-5 flex flex-wrap items-center justify-between gap-4">
          <span className="flex items-center gap-2 font-mono text-[11px] text-mute">
            <ShieldCheck className="h-4 w-4 text-lime" /> SHA-256 provenance is preserved at ingestion
          </span>
          <button onClick={closeDialog} className="h-11 bg-lime px-7 text-[14px] font-extrabold uppercase tracking-[0.04em] text-lime-ink hover:bg-[#e2ff6e]">
            Done
          </button>
        </div>
      </div>
    </Modal>
  );
}
