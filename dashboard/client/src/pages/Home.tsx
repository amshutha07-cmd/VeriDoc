/* Evidence Atelier direction: the dashboard is an evidence desk, not a generic SaaS grid. Copper marks provenance; mono labels expose system state. */
import { useMemo, useState, useEffect } from "react";
import { toast } from "sonner";
import ClaimEvidenceMap from "../components/ClaimEvidenceMap";
import { Streamdown } from "streamdown";
import {
  ArrowUpRight,
  BookOpen,
  Check,
  ChevronDown,
  CircleHelp,
  Clock3,
  Database,
  FileUp,
  GitBranch,
  Layers3,
  Menu,
  Network,
  PanelLeft,
  Plus,
  Search,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  X,
} from "lucide-react";

const stages = [
  { label: "Route query", status: "complete", meta: "domain-aware" },
  { label: "Retrieve passages", status: "complete", meta: "response-bound" },
  { label: "Rerank candidates", status: "complete", meta: "precision layer" },
  { label: "Grade evidence", status: "complete", meta: "support check" },
  { label: "Generate answer", status: "active", meta: "citation-backed" },
];

const NAV_ITEMS = [
  { Icon: Search, label: "Ask the corpus", href: "/", active: true },
  { Icon: Database, label: "Corpus registry", href: "/corpus", active: false },
  { Icon: Network, label: "Knowledge graph", href: "/graph", active: false },
  { Icon: Clock3, label: "Ingestion jobs", href: "/ingestion", active: false },
  { Icon: Layers3, label: "Evaluation", href: "/evaluation", active: false },
];

type EvidenceSource = {
  id: string;
  source?: string;
  domain: string;
  title: string;
  file: string;
  page: string;
  tag: string;
  color: "copper" | "sage" | "slate";
  excerpt: string;
};

function extractSsePayload(raw: string): any | null {
  let latest: any | null = null;

  for (const event of raw.split(/\n\s*\n/)) {
    const dataLine = event.split("\n").find((line) => line.startsWith("data:"));
    if (!dataLine) continue;

    try {
      const payload = JSON.parse(dataLine.slice(5).trim());
      const answer = payload?.answer ?? payload?.result?.answer ?? payload?.response;
      const evidence = payload?.evidence ?? payload?.result?.evidence ?? payload?.data?.evidence;

      if (typeof answer === "string" && answer.trim()) {
        latest = { ...(latest ?? {}), ...payload };
      } else if (Array.isArray(evidence)) {
        latest = { ...(latest ?? {}), evidence };
      }
    } catch {
      // Ignore non-JSON keep-alive/event lines.
    }
  }

  return latest;
}

function normalizeEvidence(payload: any): EvidenceSource[] {
  const items = payload?.evidence ?? payload?.docs ?? payload?.result?.evidence ?? payload?.result?.docs ?? payload?.data?.evidence ?? payload?.data?.docs ?? [];
  if (!Array.isArray(items)) return [];

  return items.map((item: any, index: number) => {
    const metadata = item?.metadata ?? item ?? {};
    const file = String(metadata.source ?? metadata.file ?? "source");
    const rawPage = String(metadata.page_label ?? metadata.page ?? "?");
    const page = rawPage.toLowerCase().startsWith("p") ? rawPage : `p. ${rawPage}`;
    const category = String(metadata.category ?? metadata.document_type ?? "Evidence");
    const color = index % 3 === 0 ? "copper" : index % 3 === 1 ? "sage" : "slate";

    return {
      id: String(index + 1).padStart(2, "0"),
      domain: category,
      title: String(metadata.title ?? metadata.document_title ?? file),
      file,
      page,
      tag: String(item?.tag ?? item?.support ?? "Evidence"),
      source: file,
      excerpt: String(item?.excerpt ?? item?.page_content ?? metadata.excerpt ?? "No excerpt returned."),
      color,
    };
  });
}

export default function Home() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("Run a query to generate a grounded answer from the connected corpus.");
  const [isRunning, setIsRunning] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [guideOpen, setGuideOpen] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});
  const [uploadDomain, setUploadDomain] = useState<"legal" | "corporate">("legal");
  const [liveSources, setLiveSources] = useState<EvidenceSource[]>([]);
  const [sourceFilter, setSourceFilter] = useState("All");
  const [expandedSourceId, setExpandedSourceId] = useState<string | null>(null);
  const [corpus, setCorpus] = useState<[string, string, string][]>([
    ["Legal chunks", "-", "loading"],
    ["Corporate chunks", "-", "loading"],
  ]);
  const [modelUsed, setModelUsed] = useState<string | null>(null);

  useEffect(() => {
    const apiBase = import.meta.env.VITE_VERIDOC_API_URL as string | undefined;
    if (!apiBase) { setCorpus([["Legal chunks", "-", "no backend"], ["Corporate chunks", "-", "no backend"]]); return; }
    fetch(`${apiBase}/ingest/stats`)
      .then((res) => res.json())
      .then((data) => {
        setCorpus([
          ["Legal chunks", String(data?.legal_chunks ?? "-"), "indexed"],
          ["Corporate chunks", String(data?.handbook_chunks ?? "-"), "indexed"],
        ]);
      })
      .catch(() => setCorpus([["Legal chunks", "-", "unavailable"], ["Corporate chunks", "-", "unavailable"]]));
  }, []);

  const filterOptions = useMemo(() => {
    const domains = Array.from(new Set(liveSources.map((source) => source.domain).filter(Boolean)));
    return ["All", ...domains];
  }, [liveSources]);

  const visibleSources = useMemo(
    () => (sourceFilter === "All" ? liveSources : liveSources.filter((source) => source.domain === sourceFilter)),
    [sourceFilter, liveSources]
  );

  const apiLabel = useMemo(() => (import.meta.env.VITE_VERIDOC_API_URL ? "Backend connected" : "Demo workspace"), []);

  const anchoredCount = visibleSources.filter((source) => source.page && source.page !== "p. ?").length;
  const confidenceLabel = visibleSources.length === 0 ? "-" : `${Math.round((anchoredCount / visibleSources.length) * 100)}%`;

  async function askQuestion() {
    if (!question.trim()) return;
    setIsRunning(true);
    const apiBase = import.meta.env.VITE_VERIDOC_API_URL as string | undefined;
    try {
      if (apiBase) {
        const response = await fetch(`${apiBase.replace(/\/$/, "")}/ask/json`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question }),
        });
        if (!response.ok) throw new Error(`Backend returned ${response.status}`);
        const rawBody = await response.text();
        const payload = response.headers.get("content-type")?.includes("text/event-stream")
          ? extractSsePayload(rawBody)
          : (() => {
            try {
              return JSON.parse(rawBody);
            } catch {
              return null;
            }
          })();
        const remoteAnswer = payload?.answer ?? payload?.response ?? payload?.result?.answer ?? null;
        setModelUsed(payload?.model ?? null);
        setLiveSources(normalizeEvidence(payload));
        setSourceFilter("All");
        setExpandedSourceId(null);
        if (typeof remoteAnswer === "string" && remoteAnswer.trim()) setAnswer(remoteAnswer);
        toast.success("Evidence packet refreshed", { description: "Live response received from VeriDoc backend." });
      } else {
        await new Promise((resolve) => window.setTimeout(resolve, 850));
        toast.success("Evidence packet refreshed", { description: "Demo response · add VITE_VERIDOC_API_URL for live backend calls." });
      }
    } catch (error) {
      toast.error("Backend request failed", { description: error instanceof Error ? error.message : "Check the API URL and CORS settings." });
    } finally {
      setIsRunning(false);
    }
  }

  async function handleFiles(files: FileList | null) {
    if (!files?.length) return;

    const apiBase = import.meta.env.VITE_VERIDOC_API_URL as string | undefined;
    const selected = Array.from(files);
    const names = selected.map((file) => file.name);
    setUploadedFiles((current) => Array.from(new Set([...current, ...names])));
    setUploadProgress((current) => ({
      ...current,
      ...Object.fromEntries(names.map((name) => [name, 0])),
    }));

    if (!apiBase) {
      toast.error("Backend URL is not configured", {
        description: "Set VITE_VERIDOC_API_URL before uploading documents.",
      });
      return;
    }

    const formData = new FormData();
    formData.append("domain", uploadDomain);
    selected.forEach((file) => formData.append("files", file));

    try {
      const response = await fetch(`${apiBase.replace(/\/$/, "")}/ingest`, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) throw new Error(`Backend returned ${response.status}`);

      const result = await response.json();
      setUploadProgress((current) => ({
        ...current,
        ...Object.fromEntries(names.map((name) => [name, 100])),
      }));
      toast.success("Documents indexed", {
        description: `${result.pages ?? 0} pages and ${result.chunks ?? 0} chunks added to VeriDoc.`,
      });
    } catch (error) {
      setUploadProgress((current) => ({
        ...current,
        ...Object.fromEntries(names.map((name) => [name, -1])),
      }));
      toast.error("Document ingestion failed", {
        description: error instanceof Error ? error.message : "Check the backend logs.",
      });
    }
  }

  async function copyAnswerWithCitations() {
    const citations = visibleSources
      .map((source, index) => `[${index + 1}] ${source.file} - ${source.page}`)
      .join("\n");
    const text = `${answer}\n\nSources:\n${citations || "No sources available."}`;
    try {
      await navigator.clipboard.writeText(text);
      toast.success("Answer copied with citation metadata.");
    } catch {
      toast.error("Could not copy to clipboard.", { description: "Your browser may be blocking clipboard access." });
    }
  }

  return (
    <div className="min-h-screen bg-[#f4f0e8] text-[#1e2625]">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-[238px] border-r border-[#d9d1c4] bg-[#eee9df] lg:flex lg:flex-col">
        <div className="flex items-center gap-3 px-7 py-7">
          <div className="relative flex h-10 w-10 items-center justify-center bg-[#b96845] shadow-[4px_4px_0_#1e2625]">
            <img src="/veridoc-nexus-mark.svg" alt="VeriDoc Nexus mark" className="h-8 w-8 object-contain" />
          </div>
          <div>
            <div className="font-serif text-[18px] leading-none tracking-tight">VeriDoc</div>
            <div className="mt-1 font-mono text-[9px] uppercase tracking-[0.22em] text-[#7d766d]">Nexus / workspace</div>
          </div>
        </div>

        <div className="px-4">
          <div className="mb-3 px-3 font-mono text-[10px] uppercase tracking-[0.2em] text-[#9b9388]">Research desk</div>
          <nav className="space-y-1">
            {NAV_ITEMS.map(({ Icon, label, href, active }) => (
              <a key={label} href={href} className={`group flex w-full items-center gap-3 px-3 py-3 text-left text-[13px] transition-colors ${active ? "bg-[#1e2625] text-[#f8f4ec]" : "text-[#716a61] hover:bg-[#e5dfd4] hover:text-[#1e2625]"}`}>
                <Icon className={`h-4 w-4 ${active ? "text-[#e5a182]" : "text-[#8f887e]"}`} strokeWidth={1.7} />
                <span>{label}</span>
                {active && <span className="ml-auto h-1.5 w-1.5 bg-[#b96845]" />}
              </a>
            ))}
          </nav>
        </div>

        <div className="mt-auto border-t border-[#d9d1c4] p-5">
          <div className="mb-3 flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.15em] text-[#7d766d]"><ShieldCheck className="h-3.5 w-3.5 text-[#6e8b78]" /> Provenance mode</div>
          <p className="font-serif text-[14px] leading-snug text-[#4c514d]">Every claim is anchored to a source passage before it reaches the answer.</p>
          <div className="mt-4 flex items-center gap-2 font-mono text-[10px] text-[#8b857c]"><span className="h-2 w-2 rounded-full bg-[#6e8b78]" /> {apiLabel}</div>
        </div>
      </aside>

      {mobileNavOpen && (
        <div className="fixed inset-0 z-40 flex lg:hidden" onClick={() => setMobileNavOpen(false)}>
          <div className="absolute inset-0 bg-[#1e2625]/40" />
          <div className="relative z-10 flex h-full w-[268px] flex-col bg-[#eee9df] shadow-[8px_0_0_#1e2625]" onClick={(event) => event.stopPropagation()}>
            <div className="flex items-center justify-between px-6 py-6">
              <span className="font-serif text-lg">VeriDoc Nexus</span>
              <button onClick={() => setMobileNavOpen(false)} className="text-[#716a61]"><X className="h-5 w-5" /></button>
            </div>
            <nav className="space-y-1 px-4">
              {NAV_ITEMS.map(({ Icon, label, href, active }) => (
                <a key={label} href={href} onClick={() => setMobileNavOpen(false)} className={`group flex w-full items-center gap-3 px-3 py-3 text-left text-[13px] transition-colors ${active ? "bg-[#1e2625] text-[#f8f4ec]" : "text-[#716a61] hover:bg-[#e5dfd4] hover:text-[#1e2625]"}`}>
                  <Icon className={`h-4 w-4 ${active ? "text-[#e5a182]" : "text-[#8f887e]"}`} strokeWidth={1.7} />
                  <span>{label}</span>
                </a>
              ))}
            </nav>
          </div>
        </div>
      )}

      {guideOpen && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-[#1e2625]/35 p-5" onClick={() => setGuideOpen(false)}>
          <div className="w-full max-w-[520px] border border-[#cfc6b9] bg-[#f8f5ef] p-6 shadow-[10px_10px_0_#1e2625] sm:p-8" onClick={(event) => event.stopPropagation()}>
            <div className="flex items-start justify-between">
              <div>
                <div className="mb-2 font-mono text-[10px] uppercase tracking-[0.18em] text-[#b96845]">How VeriDoc works</div>
                <h2 className="font-serif text-3xl">Evidence-first, by design</h2>
              </div>
              <button onClick={() => setGuideOpen(false)} className="text-[#8c857c] hover:text-[#1e2625]"><X className="h-5 w-5" /></button>
            </div>
            <ol className="mt-6 space-y-3">
              {stages.map((stage, index) => (
                <li key={stage.label} className="flex items-start gap-3">
                  <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center border border-[#bbb1a4] bg-[#f8f5ef] font-mono text-[9px]">{index + 1}</span>
                  <div>
                    <div className="text-[13px] font-medium text-[#303a36]">{stage.label}</div>
                    <div className="font-mono text-[9px] uppercase tracking-[0.1em] text-[#8d867d]">{stage.meta}</div>
                  </div>
                </li>
              ))}
            </ol>
            <p className="mt-6 font-serif text-[15px] leading-relaxed text-[#6a706a]">Every answer is grounded in retrieved passages. If evidence is weak, VeriDoc corrects the search before answering - and refuses rather than inventing facts when nothing supports the claim.</p>
          </div>
        </div>
      )}

      <main className="lg:pl-[238px]">
        <header className="flex h-[78px] items-center justify-between border-b border-[#d9d1c4] px-5 sm:px-8 lg:px-12">
          <div className="flex items-center gap-3 lg:hidden"><PanelLeft className="h-5 w-5 text-[#7d766d]" /><span className="font-serif text-lg">VeriDoc Nexus</span></div>
          <div className="hidden items-center gap-2 font-mono text-[10px] uppercase tracking-[0.2em] text-[#8b857c] sm:flex"><span className="h-1.5 w-1.5 bg-[#b96845]" /> Research workspace <span className="text-[#c5bdb1]">/</span> Case 004</div>
          <div className="flex items-center gap-3">
            <div className="mr-2 hidden items-center gap-2 md:flex"><img src="/veridoc-nexus-mark.svg" alt="" className="h-7 w-7 object-contain" /><span className="font-serif text-[17px] tracking-[-0.02em]">VeriDoc <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-[#77736c]">Nexus</span></span></div>
            <button onClick={() => setGuideOpen(true)} className="hidden items-center gap-2 border border-[#cec5b8] px-3 py-2 font-mono text-[10px] uppercase tracking-[0.15em] text-[#6f6a63] transition hover:border-[#1e2625] sm:flex"><CircleHelp className="h-3.5 w-3.5" /> Guide</button>
            <button onClick={() => setUploadOpen(true)} className="flex items-center gap-2 bg-[#b96845] px-4 py-2.5 text-[12px] font-semibold text-white shadow-[3px_3px_0_#1e2625] transition hover:-translate-y-0.5 hover:shadow-[4px_4px_0_#1e2625] active:translate-y-0 active:shadow-[1px_1px_0_#1e2625]"><UploadCloud className="h-4 w-4" /> Add documents</button>
            <button onClick={() => setMobileNavOpen(true)} className="p-2 text-[#716a61] lg:hidden"><Menu className="h-5 w-5" /></button>
          </div>
        </header>

        <div className="mx-auto max-w-[1480px] px-5 pb-16 pt-8 sm:px-8 lg:px-12 lg:pt-12">
          <section className="relative overflow-hidden border border-[#d9d1c4] bg-[#e8dfd2] px-6 py-8 sm:px-10 sm:py-10 lg:px-14 lg:py-12">
            <div className="absolute inset-0 bg-gradient-to-r from-[#e8dfd2] via-[#e8dfd2]/90 to-transparent" />
            <div className="relative max-w-[690px]">
              <div className="mb-5 flex items-center gap-3 font-mono text-[10px] uppercase tracking-[0.24em] text-[#b96845]"><span className="h-px w-7 bg-[#b96845]" /> Evidence desk / live <span className="h-1.5 w-1.5 rounded-full bg-[#6e8b78]" /></div>
              <h1 className="font-serif text-[clamp(2.5rem,5vw,5.3rem)] leading-[0.93] tracking-[-0.045em] text-[#1e2625]">Ask the corpus.<br /><em className="text-[#b96845]">Keep the proof.</em></h1>
              <p className="mt-6 max-w-[490px] font-serif text-[17px] leading-relaxed text-[#515952]">An agentic research workspace for questions that need more than an answer. Search the corpus, follow its connections, and see exactly where every claim came from.</p>
            </div>
            <div className="absolute bottom-7 right-8 hidden w-[245px] font-mono text-[9px] uppercase leading-relaxed tracking-[0.15em] text-[#82786d] xl:block"><div className="mb-2 flex items-center justify-between border-b border-[#aa9d8e] pb-2"><span>Corpus health</span><span className="text-[#6e8b78]">Not measured</span></div><div className="flex items-center justify-between"><span>Last indexed</span><span>Not exposed</span></div><div className="mt-5 flex items-center gap-2 text-[#8f8175]"><span className="h-2 w-2 bg-[#b96845]" /><span className="h-px flex-1 bg-[#b96845]" /><span className="h-2 w-px bg-[#b96845]" /><span className="h-px flex-1 bg-[#b96845]" /><span className="h-2 w-2 border border-[#b96845]" /><span className="text-[8px]">claim → source → confidence</span></div></div>
          </section>

          <section className="grid border-x border-b border-[#d9d1c4] bg-[#f8f5ef] sm:grid-cols-2 lg:grid-cols-4">
            {corpus.map(([label, value, status], index) => <div key={label} className={`flex items-end justify-between px-5 py-5 ${index !== corpus.length - 1 ? "border-b border-[#d9d1c4] sm:border-r lg:border-b-0" : ""}`}><div><div className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#8c857c]">{label}</div><div className="mt-2 font-serif text-3xl text-[#1e2625]">{value}</div></div><span className="mb-1 font-mono text-[9px] uppercase tracking-[0.12em] text-[#6e8b78]">{status}</span></div>)}
          </section>

          <div className="mt-10 grid gap-8 xl:grid-cols-[minmax(0,1fr)_365px]">
            <section>
              <div className="mb-4 flex items-end justify-between"><div><div className="mb-2 font-mono text-[10px] uppercase tracking-[0.2em] text-[#8c857c]">01 / Research query</div><h2 className="font-serif text-3xl tracking-tight text-[#1e2625]">Open a line of inquiry</h2></div><button onClick={() => setQuestion("")} className="hidden items-center gap-1 font-mono text-[10px] uppercase tracking-[0.12em] text-[#8c857c] hover:text-[#1e2625] sm:flex">Clear <X className="h-3 w-3" /></button></div>
              <div className="border border-[#cfc6b9] bg-[#fbfaf6] p-5 shadow-[7px_7px_0_#e0d8cd] sm:p-7">
                <div className="mb-4 flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.15em] text-[#8c857c]"><span className="bg-[#e7efe8] px-2 py-1 text-[#547461]">Evidence corpus</span><span className="bg-[#f2e8e3] px-2 py-1 text-[#a25d41]">Domain-aware retrieval</span><ChevronDown className="ml-auto h-4 w-4" /></div>
                <textarea value={question} onChange={(event) => setQuestion(event.target.value)} rows={3} className="w-full resize-none border-0 bg-transparent p-0 font-serif text-[24px] leading-snug text-[#1e2625] outline-none placeholder:text-[#afa79c]" placeholder="Ask a question that deserves evidence..." />
                <div className="mt-7 border-t border-[#e3ddd3] pt-4"><div className="mb-4 flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.13em] text-[#8e877e]"><span className="h-2 w-2 bg-[#b96845]" /> Dossier 004 <span className="text-[#c1b8ad]">/</span> source chain armed <span className="ml-auto text-[#6e8b78]">ready</span></div><div className="mb-5 flex items-center gap-2"><span className="font-mono text-[9px] text-[#b96845]">CLAIM</span><span className="h-px flex-1 bg-[#d8cfc3]" /><span className="h-2 w-px bg-[#b96845]" /><span className="font-mono text-[9px] text-[#8e877e]">PASSAGE</span><span className="h-px flex-1 bg-[#d8cfc3]" /><span className="h-2 w-2 rounded-full border border-[#6e8b78]" /><span className="font-mono text-[9px] text-[#6e8b78]">Not scored</span></div><div className="flex flex-wrap items-center justify-between gap-4"><div className="flex items-center gap-2 font-mono text-[10px] text-[#8e877e]"><Sparkles className="h-3.5 w-3.5 text-[#8e877e]" /> Response-bound evidence retrieval</div><button onClick={askQuestion} disabled={isRunning} className="flex items-center gap-2 bg-[#1e2625] px-5 py-3 text-[12px] font-semibold text-[#f8f4ec] transition hover:bg-[#33403d] disabled:cursor-wait disabled:opacity-70">{isRunning ? "Tracing evidence..." : "Run research"}<ArrowUpRight className="h-4 w-4 text-[#e5a182]" /></button></div></div>
              </div>

              <div className="mt-9 mb-4 flex items-end justify-between"><div><div className="mb-2 font-mono text-[10px] uppercase tracking-[0.2em] text-[#8c857c]">02 / Evidence packet</div><h2 className="font-serif text-3xl tracking-tight text-[#1e2625]">A grounded answer</h2></div><div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.12em] text-[#547461]"><span className="h-2 w-2 rounded-full bg-[#6e8b78]" /> Supported</div></div>
              <article className="border border-[#cfc6b9] bg-[#fbfaf6] p-5 sm:p-8">
                <div className="mb-5 flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.14em] text-[#8c857c]"><span className="flex h-5 w-5 items-center justify-center bg-[#b96845] text-[9px] text-white">01</span><span>Claim packet / direct support</span><span className="ml-auto text-[#6e8b78]">verified</span></div>
                <div className="flex items-start justify-between gap-6">
                  <div className="answer-markdown max-w-[690px] font-serif text-[20px] leading-[1.52] text-[#2d3733]"><Streamdown>{answer}</Streamdown></div>
                  <div className="hidden border-l border-[#d9d1c4] pl-5 text-right sm:block"><div className="font-mono text-2xl text-[#b96845]">{confidenceLabel}</div><div className="mt-1 font-mono text-[9px] uppercase tracking-[0.16em] text-[#8c857c]">evidence anchored</div></div>
                </div>
                <div className="mt-6 flex items-center justify-between border-t border-[#d9d1c4] pt-4"><span className="font-mono text-[10px] text-[#91897e]">{modelUsed ? `Generated by ${modelUsed}` : "Model not reported"}</span><button onClick={() => void copyAnswerWithCitations()} className="font-mono text-[10px] uppercase tracking-[0.14em] text-[#b96845] hover:text-[#1e2625]">Copy with citations</button></div>
              </article>
            </section>

            <aside className="space-y-8">
              <ClaimEvidenceMap sources={visibleSources} />
              <section>
                <div className="mb-4 flex items-end justify-between"><div><div className="mb-2 font-mono text-[10px] uppercase tracking-[0.2em] text-[#8c857c]">03 / Agent trace</div><h2 className="font-serif text-2xl tracking-tight">Reasoning path</h2></div><span className="font-mono text-[10px] text-[#8c857c]">1.8s total</span></div>
                <div className="border border-[#cfc6b9] bg-[#f8f5ef] p-5">{stages.map((stage, index) => <div key={stage.label} className="relative flex gap-3 pb-5 last:pb-0"><div className="relative z-10 flex h-5 w-5 shrink-0 items-center justify-center border border-[#bbb1a4] bg-[#f8f5ef]">{stage.status === "complete" ? <Check className="h-3 w-3 text-[#547461]" /> : <span className="h-2 w-2 animate-pulse bg-[#b96845]" />}</div>{index < stages.length - 1 && <div className="absolute left-[9px] top-5 h-[calc(100%-12px)] w-px bg-[#d6cdc0]" />}<div className="-mt-0.5"><div className="text-[12px] font-medium text-[#303a36]">{stage.label}</div><div className="mt-1 font-mono text-[9px] uppercase tracking-[0.1em] text-[#8d867d]">{stage.meta}</div></div></div>)}</div>
              </section>

              <section>
                <div className="mb-4 flex items-end justify-between"><div><div className="mb-2 font-mono text-[10px] uppercase tracking-[0.2em] text-[#8c857c]">04 / Source passages</div><h2 className="font-serif text-2xl tracking-tight">Proof, in context</h2></div><div className="flex flex-wrap items-center gap-2">{filterOptions.map((filter) => <button key={filter} onClick={() => setSourceFilter(filter)} className={`font-mono text-[9px] uppercase tracking-[0.1em] ${sourceFilter === filter ? "text-[#b96845]" : "text-[#9a9186]"}`}>{filter}</button>)}</div></div>
                <div className="space-y-2">
                  {visibleSources.length === 0 && <p className="font-serif text-sm text-[#8c857c]">No source passages yet - run a query to populate this list.</p>}
                  {visibleSources.map((source) => {
                    const isExpanded = expandedSourceId === source.id;
                    return (
                      <div key={source.id} className="source-card border border-[#d9d1c4] bg-[#f8f5ef] transition hover:border-[#b96845]">
                        <button onClick={() => setExpandedSourceId(isExpanded ? null : source.id)} className="group w-full p-4 text-left text-[#3b4540]">
                          <div className="flex items-start gap-3">
                            <span className={`font-mono text-[10px] ${source.color === "copper" ? "text-[#b96845]" : source.color === "sage" ? "text-[#547461]" : "text-[#65716e]"}`}>{source.id}</span>
                            <div className="min-w-0 flex-1">
                              <div className="text-[12px] leading-snug text-[#3b4540]">{source.title}</div>
                              <div className="mt-2 flex items-center gap-2 font-mono text-[9px] uppercase tracking-[0.08em] text-[#958d83]"><span>{source.file}</span><span>·</span><span>{source.page}</span><span className="ml-auto text-[#6e8b78]">{source.tag}</span></div>
                            </div>
                            <ChevronDown className={`h-3.5 w-3.5 shrink-0 text-[#b1a89d] transition group-hover:text-[#b96845] ${isExpanded ? "rotate-180" : ""}`} />
                          </div>
                        </button>
                        {isExpanded && <div className="border-t border-[#e5ded4] px-4 py-3 font-serif text-[13px] leading-relaxed text-[#4c514d]">{source.excerpt}</div>}
                      </div>
                    );
                  })}
                </div>
              </section>

              <section className="border-t border-[#d9d1c4] pt-6"><div className="mb-3 flex items-center justify-between"><div className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#8c857c]">Recent ingestion</div><Clock3 className="h-3.5 w-3.5 text-[#b96845]" /></div><div className="flex items-center justify-between py-2"><div className="flex items-center gap-2"><BookOpen className="h-4 w-4 text-[#8e877e]" /><span className="text-[12px]">Central Acts seed set</span></div><span className="font-mono text-[10px] text-[#6e8b78]">ready</span></div>{uploadedFiles.map((name) => <div key={name} className="flex items-center justify-between border-t border-[#e5ded4] py-2"><div className="flex min-w-0 items-center gap-2"><FileUp className="h-4 w-4 shrink-0 text-[#b96845]" /><span className="truncate text-[12px]">{name}</span></div><span className="font-mono text-[10px] text-[#b96845]">queued</span></div>)}<button onClick={() => setUploadOpen(true)} className="mt-3 flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.14em] text-[#b96845] hover:text-[#1e2625]"><Plus className="h-3.5 w-3.5" /> Queue a source</button></section>
            </aside>
          </div>
        </div>
      </main>

      {uploadOpen && <div className="fixed inset-0 z-40 flex items-center justify-center bg-[#1e2625]/35 p-5" onClick={() => setUploadOpen(false)}><div className="w-full max-w-[560px] border border-[#cfc6b9] bg-[#f8f5ef] p-6 shadow-[10px_10px_0_#1e2625] sm:p-8" onClick={(event) => event.stopPropagation()}><div className="flex items-start justify-between"><div><div className="mb-2 font-mono text-[10px] uppercase tracking-[0.18em] text-[#b96845]">Ingestion dossier</div><h2 className="font-serif text-3xl">Add source documents</h2><p className="mt-2 max-w-[390px] font-serif text-[15px] leading-relaxed text-[#6a706a]">Queue Acts, Rules, amendments, or judgments. The backend will hash, extract, and index them without rebuilding the corpus.</p></div><button onClick={() => setUploadOpen(false)} className="text-[#8c857c] hover:text-[#1e2625]"><X className="h-5 w-5" /></button></div><select value={uploadDomain} onChange={(event) => setUploadDomain(event.target.value as "legal" | "corporate")} className="mt-7 w-full border border-[#b9aea0] bg-[#f2eee7] px-3 py-3 text-[12px] text-[#3b4540]"><option value="legal">Indian law collection</option><option value="corporate">Corporate / handbook collection</option></select><label className="mt-7 flex cursor-pointer flex-col items-center justify-center border border-dashed border-[#b9aea0] bg-[#f2eee7] px-5 py-10 text-center transition hover:border-[#b96845] hover:bg-[#f0e7df]"><input type="file" accept="application/pdf,.docx" multiple className="sr-only" onChange={(event) => { handleFiles(event.target.files); setUploadOpen(false); }} /><FileUp className="h-8 w-8 text-[#b96845]" /><span className="mt-3 text-[13px] font-medium">Drop PDFs or DOCX files here</span><span className="mt-1 font-mono text-[10px] uppercase tracking-[0.12em] text-[#958d83]">PDF · DOCX · multiple files supported</span></label><div className="mt-5 flex items-center gap-2 font-mono text-[10px] text-[#8c857c]"><ShieldCheck className="h-3.5 w-3.5 text-[#6e8b78]" /> SHA-256 provenance is preserved at ingestion</div></div></div>}
    </div>
  );
}
