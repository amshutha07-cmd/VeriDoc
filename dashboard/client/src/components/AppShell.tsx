/* The frame around every page: header with navigation, "Guide" and "Add documents", a bottom tab bar on phones, and the dialogs. */
import { useState, type ReactNode } from "react";
import { Link, useLocation } from "wouter";
import { CircleHelp, Clock3, Database, Layers3, Network, Search, UploadCloud } from "lucide-react";
import GuideDialog from "@/components/GuideDialog";
import LogoMark from "@/components/LogoMark";
import UploadDialog from "@/components/UploadDialog";
import { useUpload } from "@/contexts/UploadContext";
import { HAS_BACKEND } from "@/lib/api";

const NAV = [
  { label: "Ask the corpus", short: "Ask", href: "/", Icon: Search },
  { label: "Registry", short: "Registry", href: "/corpus", Icon: Database },
  { label: "Graph", short: "Graph", href: "/graph", Icon: Network },
  { label: "Ingestion", short: "Ingest", href: "/ingestion", Icon: Clock3 },
  { label: "Evaluation", short: "Evals", href: "/evaluation", Icon: Layers3 },
];

export default function AppShell({ children }: { children: ReactNode }) {
  const [location] = useLocation();
  const [guideOpen, setGuideOpen] = useState(false);
  const { openDialog } = useUpload();

  return (
    <div className="min-h-screen bg-ink text-fg">
      <a href="#main" className="skip-link">
        Skip to content
      </a>

      <header className="sticky top-0 z-30 border-b border-line bg-ink/95 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-[1440px] items-center justify-between gap-4 px-4 sm:px-7">
          <div className="flex min-w-0 items-center gap-7">
            <Link href="/" aria-label="VeriDoc Nexus, home" className="flex items-center gap-2.5">
              <LogoMark size={28} />
              <span className="text-[17px] font-black tracking-[0.02em]">
                VERIDOC <span className="text-lime">NEXUS</span>
              </span>
            </Link>
            <nav aria-label="Workspace" className="hidden items-center gap-6 font-mono text-[12px] uppercase tracking-[0.08em] lg:flex">
              {NAV.map(({ label, href }) => {
                const active = location === href;
                return (
                  <Link
                    key={href}
                    href={href}
                    aria-current={active ? "page" : undefined}
                    className={`border-b-2 pb-1 transition-colors ${active ? "border-lime text-lime" : "border-transparent text-mute hover:text-fg"}`}
                  >
                    {label}
                  </Link>
                );
              })}
            </nav>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setGuideOpen(true)}
              className="flex h-9 items-center gap-2 border border-edge px-3 font-mono text-[11px] uppercase tracking-[0.1em] text-soft transition-colors hover:border-fg hover:text-fg"
            >
              <CircleHelp className="h-3.5 w-3.5" /> <span className="hidden sm:inline">Guide</span>
              <span className="sm:hidden">Help</span>
            </button>
            <button
              onClick={openDialog}
              className="flex h-9 items-center gap-2 bg-lime px-3 text-[13px] font-extrabold uppercase tracking-[0.04em] text-lime-ink transition-colors hover:bg-[#e2ff6e] sm:px-4"
            >
              <UploadCloud className="h-4 w-4" />
              <span className="hidden sm:inline">Add documents</span>
              <span className="sm:hidden">Add</span>
            </button>
          </div>
        </div>
      </header>

      <main id="main" className="mx-auto w-full max-w-[1440px] px-4 pb-28 pt-5 sm:px-7 sm:pt-6 lg:pb-12">
        {children}
        <footer className="mt-10 flex flex-wrap items-center justify-between gap-3 border-t border-line pt-4 font-mono text-[11px] text-mute">
          <span>Every claim is anchored to a source passage before it reaches the answer.</span>
          <span className="flex items-center gap-2">
            <span className={`h-2 w-2 ${HAS_BACKEND ? "bg-lime" : "border border-mute"}`} />
            {HAS_BACKEND ? "Backend connected" : "Demo workspace"}
          </span>
        </footer>
      </main>

      <nav
        aria-label="Workspace"
        className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-5 border-t border-line bg-ink pb-[env(safe-area-inset-bottom)] lg:hidden"
      >
        {NAV.map(({ short, href, Icon }) => {
          const active = location === href;
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? "page" : undefined}
              className={`flex min-h-[56px] flex-col items-center justify-center gap-1 text-[11px] font-semibold ${active ? "text-lime" : "text-mute"}`}
            >
              <Icon className="h-5 w-5" strokeWidth={1.9} />
              {short}
            </Link>
          );
        })}
      </nav>

      <GuideDialog open={guideOpen} onClose={() => setGuideOpen(false)} />
      <UploadDialog />
    </div>
  );
}
