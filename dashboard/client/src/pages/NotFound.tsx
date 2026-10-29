import { Link } from "wouter";

export default function NotFound() {
  return (
    <div className="bg-cobalt px-5 py-8 text-white sm:px-9 sm:py-10">
      <div className="font-mono text-[12px] uppercase tracking-[0.12em]">Page not found</div>
      <div className="mt-4 flex flex-col gap-4 sm:flex-row sm:items-end sm:gap-8">
        <div className="text-[clamp(6rem,22vw,12rem)] font-black leading-[0.82] tracking-[-0.05em]">404</div>
        <div className="pb-1">
          <h1 className="text-[clamp(1.6rem,4vw,2rem)] font-extrabold leading-tight tracking-[-0.02em]">No passage supports this page.</h1>
          <p className="mt-2 text-[15px] leading-snug">The address you opened is not in the workspace.</p>
        </div>
      </div>
      <Link href="/" className="mt-7 inline-flex h-11 items-center bg-lime px-6 text-[14px] font-extrabold uppercase tracking-[0.04em] text-lime-ink hover:bg-[#e2ff6e]">
        Back to Ask the corpus
      </Link>
    </div>
  );
}
