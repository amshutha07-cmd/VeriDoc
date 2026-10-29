/* "How VeriDoc works". The same five stages the old Guide explained. */
import { X } from "lucide-react";
import Modal from "@/components/Modal";

export const STAGES = [
  { label: "Route query", meta: "domain-aware" },
  { label: "Retrieve passages", meta: "response-bound" },
  { label: "Rerank candidates", meta: "precision layer" },
  { label: "Grade evidence", meta: "support check" },
  { label: "Generate answer", meta: "citation-backed" },
];

export default function GuideDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  return (
    <Modal open={open} onClose={onClose} label="How VeriDoc works" className="max-w-[540px]">
      <div className="p-6 sm:p-8">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-lime">How VeriDoc works</div>
            <h2 className="mt-2 text-[32px] font-black leading-none tracking-[-0.03em] sm:text-4xl">Evidence-first, by design</h2>
          </div>
          <button onClick={onClose} aria-label="Close" className="-mr-2 -mt-2 flex h-11 w-11 shrink-0 items-center justify-center text-fg hover:text-lime">
            <X className="h-5 w-5" />
          </button>
        </div>

        <ol className="mt-6 flex flex-col gap-3">
          {STAGES.map((stage, index) => (
            <li key={stage.label} className="flex items-start gap-3">
              <span className="flex h-7 w-7 shrink-0 items-center justify-center bg-lime text-[14px] font-black text-lime-ink">{index + 1}</span>
              <div>
                <div className="text-[15px] font-semibold">{stage.label}</div>
                <div className="font-mono text-[10px] uppercase tracking-[0.1em] text-mute">{stage.meta}</div>
              </div>
            </li>
          ))}
        </ol>

        <p className="mt-6 text-[15px] leading-relaxed text-soft">
          Every answer is grounded in retrieved passages. If evidence is weak, VeriDoc corrects the search before answering, and refuses rather than inventing facts when nothing supports the claim.
        </p>
      </div>
    </Modal>
  );
}
