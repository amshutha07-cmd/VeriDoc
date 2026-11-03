/* Evaluation. Same calls as before: GET {API}/eval/status (polled every 3 s while running) and POST {API}/eval/run.
   Metrics are drawn to scale from the saved result. Nothing here is invented. */
import { useCallback, useEffect, useState } from "react";
import PageHero from "@/components/PageHero";

const API_URL = (import.meta.env.VITE_VERIDOC_API_URL as string | undefined)?.replace(/\/$/, "");
type Summary = { rows?: number; evidence_coverage?: number; answer_coverage?: number; citation_rate?: number; average_retries?: number; average_latency?: number };
type EvalState = { status: string; error?: string | null; result?: { completed_at?: string; test_count?: number; baseline?: Summary; crag?: Summary } | null };

const num = (value: unknown): number | undefined => (typeof value === "number" && Number.isFinite(value) ? value : undefined);
const pct = (value: number | undefined) => (value === undefined ? "—" : `${Math.round(value * 100)}%`);
const secs = (value: number | undefined) => (value === undefined ? "—" : `${value.toFixed(1)}s`);
const SHOW_RUN = import.meta.env.VITE_SHOW_EVAL_RUN === "1";
const STATUS_LABEL: Record<string, string> = { not_run: "Not run yet", running: "Running", completed: "Completed", failed: "Failed", loading: "Loading" };

const RATE_ROWS: { key: "evidence_coverage" | "answer_coverage" | "citation_rate"; label: string }[] = [
  { key: "evidence_coverage", label: "Evidence coverage" },
  { key: "answer_coverage", label: "Answer coverage" },
  { key: "citation_rate", label: "Citation rate" },
];

function Bar({ value, tone, label }: { value: number | undefined; tone: "base" | "crag"; label: string }) {
  const width = value === undefined ? 0 : Math.max(0, Math.min(1, value)) * 100;
  return (
    <div className="flex items-center gap-3">
      <span className="w-[62px] shrink-0 font-mono text-[11px] uppercase tracking-[0.08em] text-mute">{label}</span>
      <div className="relative h-7 flex-1 bg-white/[0.04]" role="img" aria-label={`${label} ${pct(value)}`}>
        <div className={`h-full ${tone === "crag" ? "bg-lime" : "bg-[#6B6E78]"}`} style={{ width: `${width}%` }} />
      </div>
      <span className={`w-12 shrink-0 text-right text-[18px] font-extrabold tabular-nums ${tone === "crag" ? "text-lime" : ""}`}>{pct(value)}</span>
    </div>
  );
}

function summarise(baseline?: Summary, crag?: Summary): string | null {
  if (!baseline || !crag) return null;
  const parts: string[] = [];
  for (const row of RATE_ROWS) {
    const a = num(baseline[row.key]);
    const b = num(crag[row.key]);
    if (a === undefined || b === undefined) continue;
    const diff = Math.round((b - a) * 100);
    parts.push(`${row.label.toLowerCase()} ${diff === 0 ? "did not change" : `${diff > 0 ? "rose" : "fell"} ${Math.abs(diff)} points`} (${pct(a)} to ${pct(b)})`);
  }
  if (parts.length === 0) return null;
  let text = `With the retry loop, ${parts.join(", ")}.`;
  const l1 = num(baseline.average_latency);
  const l2 = num(crag.average_latency);
  if (l1 !== undefined && l2 !== undefined && l1 > 0) text += ` Each answer took ${secs(l2)} instead of ${secs(l1)}.`;
  return text;
}

function formatDate(value?: string): string {
  if (!value) return "timestamp unavailable";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

export default function Evaluation() {
  const [state, setState] = useState<EvalState>({ status: "loading", result: null });
  const [running, setRunning] = useState(false);

  const loadStatus = useCallback(async () => {
    if (!API_URL) {
      setState({ status: "failed", error: "VITE_VERIDOC_API_URL is not configured." });
      return;
    }
    try {
      const response = await fetch(`${API_URL}/eval/status`);
      if (!response.ok) throw new Error(`Backend returned ${response.status}`);
      setState(await response.json());
    } catch (error) {
      setState({ status: "failed", error: error instanceof Error ? error.message : "Could not load evaluation status." });
    }
  }, []);

  useEffect(() => {
    void loadStatus();
  }, [loadStatus]);

  useEffect(() => {
    if (state.status !== "running") return;
    const timer = window.setInterval(() => {
      void loadStatus();
    }, 3000);
    return () => window.clearInterval(timer);
  }, [state.status, loadStatus]);

  async function runEvaluation() {
    if (!API_URL || running) return;
    setRunning(true);
    try {
      const response = await fetch(`${API_URL}/eval/run`, { method: "POST" });
      if (!response.ok) throw new Error(`Backend returned ${response.status}`);
      setState({ status: "running", result: null });
    } catch (error) {
      setState({ status: "failed", error: error instanceof Error ? error.message : "Could not start evaluation." });
    } finally {
      setRunning(false);
    }
  }

  const result = state.result;
  const baseline = result?.baseline;
  const crag = result?.crag;
  const busy = running || state.status === "running";
  const inShort = summarise(baseline, crag);

  return (
    <div className="flex flex-col gap-3">
      <PageHero eyebrow="Evaluation" title="Does the retry loop earn its cost?">
        Saved results from the Apple test set, comparing plain retrieval with the corrective loop.
      </PageHero>

      <div className="flex flex-wrap items-center gap-2">
        {SHOW_RUN && (<button onClick={() => void runEvaluation()} disabled={busy || !API_URL} className="h-12 bg-lime px-6 text-[13px] font-extrabold uppercase tracking-[0.04em] text-lime-ink hover:bg-[#e2ff6e] disabled:cursor-not-allowed disabled:opacity-50">
          {state.status === "running" ? "Evaluation running…" : "Run evaluation"}
        </button>)}
        <button onClick={() => void loadStatus()} className="h-12 border border-edge px-6 text-[13px] font-extrabold uppercase tracking-[0.04em] hover:border-fg">
          Refresh status
        </button>
        <span className="font-mono text-[12px] uppercase tracking-[0.1em] text-mute" aria-live="polite">
          Status: {STATUS_LABEL[state.status] ?? state.status}
        </span>
      </div>

      {state.error && (
        <div role="alert" className="border border-coral px-5 py-4 text-[15px] leading-snug text-coral">
          {state.error}
        </div>
      )}

      {!result && state.status !== "running" && !state.error && state.status !== "loading" && (
        <section className="border border-line bg-sunken px-5 py-6">
          <h2 className="text-[28px] font-extrabold tracking-[-0.02em]">Evaluation not run yet</h2>
          <p className="mt-2 max-w-[640px] text-[15px] leading-snug text-soft">No saved evaluation results are available yet.</p>
        </section>
      )}

      {state.status === "running" && (
        <section className="border border-line bg-sunken px-5 py-6" aria-live="polite">
          <h2 className="text-[28px] font-extrabold tracking-[-0.02em]">Evaluation in progress</h2>
          <div className="mt-3 flex h-2 max-w-[320px] overflow-hidden bg-white/[0.06]">
            <div className="h-full w-1/3 animate-pulse bg-lime" />
          </div>
          <p className="mt-3 max-w-[640px] text-[15px] leading-snug text-soft">The evaluator is running in the background. This may take time because it invokes the retrieval graph for each test case.</p>
        </section>
      )}

      {result && (
        <>
          <section className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 border border-line bg-panel px-5 py-4">
            <div>
              <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-mute">Completed run</div>
              <div className="mt-1 text-[22px] font-extrabold tracking-[-0.01em]">{result.test_count ?? 0} test cases evaluated</div>
            </div>
            <div className="font-mono text-[12px] text-mute">{formatDate(result.completed_at)}</div>
          </section>

          <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_340px] lg:items-start">
            <section className="border border-line bg-sunken px-5 py-5" aria-label="Retrieval and answer rates">
              <div className="flex flex-wrap items-center gap-x-5 gap-y-1 font-mono text-[11px] uppercase tracking-[0.1em] text-mute">
                <span className="flex items-center gap-2"><i className="h-3 w-3 bg-[#6B6E78]" /> Baseline</span>
                <span className="flex items-center gap-2"><i className="h-3 w-3 bg-lime" /> CRAG (with retries)</span>
                <span className="ml-auto">0 – 100%</span>
              </div>
              <div className="mt-5 flex flex-col gap-6">
                {RATE_ROWS.map((row) => (
                  <div key={row.key}>
                    <div className="mb-2 text-[18px] font-extrabold tracking-[-0.01em]">{row.label}</div>
                    <div className="flex flex-col gap-1.5">
                      <Bar value={num(baseline?.[row.key])} tone="base" label="Base" />
                      <Bar value={num(crag?.[row.key])} tone="crag" label="CRAG" />
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <aside className="flex flex-col gap-3">
              <div className="border border-line bg-panel px-5 py-4">
                <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-mute">What the loop costs</div>
                <dl className="mt-3 flex flex-col gap-3">
                  <div className="flex items-baseline justify-between gap-3">
                    <dt className="text-[14px] text-soft">Average latency</dt>
                    <dd className="text-[20px] font-extrabold tabular-nums">
                      <span className="text-mute">{secs(num(baseline?.average_latency))}</span> <span aria-hidden className="text-mute">▶</span> <span className="text-coral">{secs(num(crag?.average_latency))}</span>
                    </dd>
                  </div>
                  <div className="flex items-baseline justify-between gap-3">
                    <dt className="text-[14px] text-soft">Average retries</dt>
                    <dd className="text-[20px] font-extrabold tabular-nums">
                      <span className="text-mute">{num(baseline?.average_retries) ?? "—"}</span> <span aria-hidden className="text-mute">▶</span> {num(crag?.average_retries) ?? "—"}
                    </dd>
                  </div>
                  <div className="flex items-baseline justify-between gap-3">
                    <dt className="text-[14px] text-soft">Rows completed</dt>
                    <dd className="text-[20px] font-extrabold tabular-nums">{num(crag?.rows) ?? "—"}</dd>
                  </div>
                </dl>
              </div>

              {inShort && (
                <div className="border border-line bg-panel px-5 py-4">
                  <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-mute">In short</div>
                  <p className="mt-2 text-[15px] leading-snug">{inShort}</p>
                </div>
              )}

              <div className="border border-dashed border-edge px-5 py-4">
                <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-coral">Read with care</div>
                <p className="mt-2 text-[14px] leading-snug text-soft">{result.test_count ?? "A few"} questions is a small test. Treat these as a direction, not a guarantee.</p>
              </div>
            </aside>
          </div>
        </>
      )}
    </div>
  );
}
