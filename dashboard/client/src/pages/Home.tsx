/* Ask the corpus. A cobalt answer block, the claims with their sources, and the source page open beside them.
   Backend contract is unchanged: POST {API}/ask/json with { question }, answer in `answer`, passages in `evidence` or `docs`. */
import { useMemo, useRef, useState } from "react";
import { toast } from "sonner";
import { Streamdown } from "streamdown";
import { ArrowUpRight, X } from "lucide-react";
import EvidenceList from "@/components/EvidenceList";
import SourceReader from "@/components/SourceReader";
import { API_BASE, HAS_BACKEND, errorDetail, formatCount } from "@/lib/api";
import {
  SAMPLE_ANSWER,
  SAMPLE_QUESTION,
  SAMPLE_SOURCES,
  extractSsePayload,
  hasPage,
  normalizeEvidence,
  type EvidenceSource,
} from "@/lib/evidence";
import { useIngestStats } from "@/lib/useIngestStats";

type Phase = "idle" | "running" | "done" | "error";
type RunMeta = { retries?: number; grade?: string; seconds?: number; sample?: boolean };

const EXAMPLES = [
  "Does Article 21 protect the right to privacy?",
  "What does the Forest Rights Act say about community rights?",
  "Who can amend the Constitution, and how?",
];

export default function Home() {
  const [question, setQuestion] = useState("");
  const [askedQuestion, setAskedQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [unsupported, setUnsupported] = useState(false);
  const [phase, setPhase] = useState<Phase>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [liveSources, setLiveSources] = useState<EvidenceSource[]>([]);
  const [sourceFilter, setSourceFilter] = useState("All");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [modelUsed, setModelUsed] = useState<string | null>(null);
  const [meta, setMeta] = useState<RunMeta>({});
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { status: statsStatus, legalChunks, corporateChunks } = useIngestStats();

  const visibleSources = useMemo(
    () => (sourceFilter === "All" ? liveSources : liveSources.filter((source) => source.domain === sourceFilter)),
    [sourceFilter, liveSources]
  );

  const anchoredCount = visibleSources.filter(hasPage).length;
  const finished = phase === "done" || phase === "error";
  const withheld = phase === "done" && (liveSources.length === 0 || !answer.trim());
  const fullyAnchored = visibleSources.length > 0 && anchoredCount === visibleSources.length;

  async function askQuestion() {
    const asked = question.trim();
    if (!asked || phase === "running") return;
    setPhase("running");
    setErrorMessage(null);
    const started = performance.now();

    try {
      if (API_BASE) {
        const response = await fetch(`${API_BASE}/ask/json`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: asked }),
        });
        if (response.status === 429) throw new Error("Too many questions in a minute. Wait a moment and ask again.");
        if (!response.ok) throw new Error(await errorDetail(response));

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
        if (!payload) throw new Error("The backend sent a response this workspace could not read.");
        if (payload.error) throw new Error(String(payload.error));

        const remoteAnswer = payload?.answer ?? payload?.response ?? payload?.result?.answer ?? "";
        const sources = normalizeEvidence(payload);
        setAskedQuestion(asked);
        setAnswer(typeof remoteAnswer === "string" ? remoteAnswer : ""); setUnsupported(payload?.evidence_status === "uncertain");
        setModelUsed(payload?.model || null);
        setLiveSources(sources);
        setSourceFilter("All");
        setSelectedId(sources[0]?.id ?? null);
        setMeta({
          retries: typeof payload.retries === "number" ? payload.retries : undefined,
          grade: typeof payload.grade === "string" && payload.grade ? payload.grade : undefined,
          seconds: (performance.now() - started) / 1000,
        });
        toast.success("Evidence packet refreshed", { description: "Live response received from VeriDoc backend." });
      } else {
        await new Promise((resolve) => window.setTimeout(resolve, 850));
        setAskedQuestion(SAMPLE_QUESTION);
        setAnswer(SAMPLE_ANSWER); setUnsupported(false);
        setModelUsed(null);
        setLiveSources(SAMPLE_SOURCES);
        setSourceFilter("All");
        setSelectedId(SAMPLE_SOURCES[0].id);
        setMeta({ sample: true });
        toast.success("Evidence packet refreshed", { description: "Demo response · add VITE_VERIDOC_API_URL for live backend calls." });
      }
      setPhase("done");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Check the API URL and CORS settings.";
      setErrorMessage(message);
      setPhase("error");
      toast.error("Backend request failed", { description: message });
    }
  }

  async function copyAnswerWithCitations() {
    const citations = visibleSources.map((source, index) => `[${index + 1}] ${source.file} - ${source.page}`).join("\n");
    const text = `${answer}\n\nSources:\n${citations || "No sources available."}`;
    try {
      await navigator.clipboard.writeText(text);
      toast.success("Answer copied with citation metadata.");
    } catch {
      toast.error("Could not copy to clipboard.", { description: "Your browser may be blocking clipboard access." });
    }
  }

  const bigStat = `${anchoredCount} of ${visibleSources.length}`;

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,580px)_minmax(0,1fr)] lg:items-start">
      {/* left: question, answer, sources */}
      <div className="flex min-w-0 flex-col gap-3">
        {/* the cobalt block */}
        {withheld || phase === "error" ? (
          <section aria-live="polite" className="border-2 border-coral bg-ink px-5 py-6 sm:px-7">
            <div className="font-mono text-[12px] uppercase tracking-[0.12em] text-coral">{phase === "error" ? "Request failed" : "No answer given"}</div>
            {askedQuestion && <p className="mt-3 text-[20px] font-extrabold leading-tight tracking-[-0.01em]">{askedQuestion}</p>}
            <div className="mt-3 text-[clamp(3rem,10vw,5.5rem)] font-black leading-[0.9] tracking-[-0.045em] text-coral">{phase === "error" ? "Failed." : "Withheld."}</div>
            <p className="mt-3 max-w-[460px] text-[15px] leading-relaxed text-soft">
              {phase === "error"
                ? errorMessage
                : "Nothing in the corpus backs an answer to this question, so none is claimed. Try rewording it, or add the document that covers it."}
            </p>
          </section>
        ) : (
          <section aria-live="polite" className="bg-cobalt px-5 py-6 text-white sm:px-7 sm:py-7">
            {phase === "idle" && (
              <>
                <div className="font-mono text-[12px] uppercase tracking-[0.12em]">Ask the corpus</div>
                <h1 className="mt-3 text-[clamp(2.75rem,8vw,5.25rem)] font-black leading-[0.95] tracking-[-0.045em]">
                  Ask. Keep
                  <br />
                  the proof.
                </h1>
                <p className="mt-4 max-w-[440px] text-[16px] leading-relaxed">
                  Search Acts, rules, judgments and filings. Every claim comes back with the page it came from.
                </p>
                <div className="mt-5 flex flex-wrap gap-x-5 gap-y-1 font-mono text-[11px] uppercase tracking-[0.08em]">
                  {statsStatus === "ready" && (
                    <>
                      <span>Indian law {formatCount(legalChunks)} chunks</span>
                      <span>Corporate {formatCount(corporateChunks)} chunks</span>
                    </>
                  )}
                  {statsStatus === "loading" && <span>Loading corpus counts</span>}
                  {statsStatus === "error" && <span>Backend unreachable</span>}
                  {statsStatus === "nobackend" && <span>Demo workspace · no backend connected</span>}
                </div>
              </>
            )}

            {phase === "running" && (
              <>
                <div className="font-mono text-[12px] uppercase tracking-[0.12em]">Tracing evidence</div>
                <p className="mt-3 text-[22px] font-extrabold leading-tight tracking-[-0.01em]">{question.trim()}</p>
                <div className="mt-5 flex gap-2" aria-hidden="true">
                  {[0, 1, 2, 3, 4].map((step) => (
                    <span key={step} className="h-3 w-full animate-pulse bg-white/80" style={{ animationDelay: `${step * 150}ms` }} />
                  ))}
                </div>
                <p className="mt-4 text-[15px]">Routing the question, retrieving passages, reranking, grading the evidence.</p>
              </>
            )}

            {phase === "done" && (
              <>
                <div className="flex flex-wrap items-center justify-between gap-2 font-mono text-[12px] uppercase tracking-[0.12em]">
                  <span>{meta.sample ? "Sample answer" : "The question"}</span>
                  {typeof meta.seconds === "number" && <span>{meta.seconds.toFixed(1)} s</span>}
                </div>
                <p className="mt-2 text-[clamp(1.35rem,3.2vw,1.75rem)] font-extrabold leading-[1.1] tracking-[-0.02em]">{askedQuestion}</p>
                <div
                  className={`mt-3 whitespace-nowrap font-black leading-[0.86] tracking-[-0.045em] ${
                    bigStat.length <= 6 ? "text-[clamp(4rem,14vw,7.5rem)]" : "text-[clamp(3rem,10vw,5rem)]"
                  }`}
                >
                  {bigStat}
                </div>
                <p className="mt-3 text-[15px] leading-snug">
                  passages anchored to a page
                  {meta.retries !== undefined && <> · {meta.retries} {meta.retries === 1 ? "retry" : "retries"}</>}
                </p>
              </>
            )}
          </section>
        )}

        {/* composer */}
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void askQuestion();
          }}
          className="border border-edge bg-panel"
        >
          <label htmlFor="question" className="sr-only">
            Your question
          </label>
          <textarea
            id="question"
            ref={textareaRef}
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
                event.preventDefault();
                void askQuestion();
              }
            }}
            rows={3}
            placeholder={phase === "idle" ? "Ask a question that deserves evidence..." : "Ask another question"}
            className="block w-full resize-none bg-transparent p-4 text-[18px] leading-snug text-fg outline-none placeholder:text-mute"
          />
          {phase === "idle" && !question && (
            <div className="flex flex-wrap gap-2 px-4 pb-3" role="group" aria-label="Example questions">
              {EXAMPLES.map((example) => (
                <button
                  key={example}
                  type="button"
                  onClick={() => {
                    setQuestion(example);
                    textareaRef.current?.focus();
                  }}
                  className="border border-edge px-3 py-1.5 text-left text-[13px] leading-snug text-soft transition-colors hover:border-lime hover:text-fg"
                >
                  {example}
                </button>
              ))}
            </div>
          )}
          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-line px-4 py-3">
            <div className="flex items-center gap-3 font-mono text-[11px] text-mute">
              {question && (
                <button type="button" onClick={() => setQuestion("")} className="flex items-center gap-1 uppercase tracking-[0.1em] hover:text-fg">
                  Clear <X className="h-3 w-3" />
                </button>
              )}
              <span className="hidden sm:inline">Ctrl + Enter to run</span>
            </div>
            <button
              type="submit"
              disabled={phase === "running" || !question.trim()}
              className="flex h-11 items-center gap-2 bg-lime px-5 text-[14px] font-extrabold uppercase tracking-[0.04em] text-lime-ink transition-colors hover:bg-[#e2ff6e] disabled:cursor-not-allowed disabled:opacity-50"
            >
              {phase === "running" ? "Tracing evidence..." : "Run research"}
              <ArrowUpRight className="h-4 w-4" />
            </button>
          </div>
        </form>

        {/* the answer text */}
        {phase === "done" && !withheld && (
          <article aria-label="Answer" className="border border-line bg-sunken">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-5 py-3 font-mono text-[11px] uppercase tracking-[0.12em]">
              <span className="text-mute">Answer</span>
              <span className={`flex items-center gap-2 ${unsupported ? "text-coral" : fullyAnchored ? "text-lime" : "text-soft"}`}>
                <span className={`h-2 w-2 ${unsupported ? "bg-coral" : fullyAnchored ? "bg-lime" : "border border-soft"}`} />
                {meta.sample ? "Sample" : unsupported ? "Not directly supported" : fullyAnchored ? "Supported" : "Partly anchored"}
              </span>
            </div>
            <div className="answer-markdown px-5 py-5 text-[17px] leading-[1.6] text-fg sm:px-6">
              <Streamdown>{answer}</Streamdown>
            </div>
            {meta.sample && (
              <p className="mx-5 mb-4 border border-dashed border-edge px-3 py-2 text-[13px] leading-snug text-mute sm:mx-6">
                This is a fixed sample about Article 21. It is shown because no backend is connected, and it does not answer the question you typed.
              </p>
            )}
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-line px-5 py-3">
              <span className="font-mono text-[11px] text-mute">
                {modelUsed ? `Generated by ${modelUsed}` : "Model not reported"}
                {meta.grade ? ` · grade ${meta.grade}` : ""}
              </span>
              <button onClick={() => void copyAnswerWithCitations()} className="h-9 border border-edge px-3 font-mono text-[11px] uppercase tracking-[0.1em] text-fg transition-colors hover:border-lime hover:text-lime">
                Copy with citations
              </button>
            </div>
          </article>
        )}

        {phase === "done" && liveSources.length > 0 && (
          <EvidenceList
            sources={visibleSources}
            allSources={liveSources}
            selectedId={selectedId}
            onSelect={setSelectedId}
            filter={sourceFilter}
            onFilter={(value) => {
              setSourceFilter(value);
              const next = value === "All" ? liveSources : liveSources.filter((source) => source.domain === value);
              setSelectedId(next[0]?.id ?? null);
            }}
          />
        )}
      </div>

      {/* right: the proof */}
      <div className="min-w-0 lg:sticky lg:top-[72px]">
        <SourceReader sources={phase === "done" ? visibleSources : []} selectedId={selectedId} onSelect={setSelectedId} />
        {!HAS_BACKEND && phase === "idle" && (
          <p className="mt-3 text-[13px] leading-snug text-mute">Demo workspace. Run research to see a fixed sample answer.</p>
        )}
      </div>
    </div>
  );
}
