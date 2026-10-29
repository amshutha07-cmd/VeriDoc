/* The cobalt block that opens every page except Ask. */
import type { ReactNode } from "react";

export default function PageHero({ eyebrow, title, children }: { eyebrow: string; title: ReactNode; children?: ReactNode }) {
  return (
    <section className="bg-cobalt px-5 py-6 text-white sm:px-7 sm:py-7">
      <div className="font-mono text-[12px] uppercase tracking-[0.12em]">{eyebrow}</div>
      <h1 className="mt-3 max-w-[900px] text-[clamp(2rem,5.5vw,3.5rem)] font-black leading-[1] tracking-[-0.035em] [text-wrap:balance]">{title}</h1>
      {children && <p className="mt-3 max-w-[680px] text-[15px] leading-snug">{children}</p>}
    </section>
  );
}
