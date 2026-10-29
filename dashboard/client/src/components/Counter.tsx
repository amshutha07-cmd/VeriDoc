/* One big number with its label and a small note, used for the two chunk counts. */
import type { ReactNode } from "react";

export default function Counter({ label, value, note, accent = false }: { label: string; value: string; note?: ReactNode; accent?: boolean }) {
  return (
    <div className="flex items-end justify-between gap-4 border border-line bg-panel px-5 py-4">
      <div className="min-w-0">
        <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-mute">{label}</div>
        <div className={`mt-1 text-[clamp(2.5rem,6vw,3.5rem)] font-black leading-none tracking-[-0.04em] ${accent ? "text-lime" : ""}`}>{value}</div>
      </div>
      {note && <div className="text-right font-mono text-[11px] leading-relaxed text-mute">{note}</div>}
    </div>
  );
}
