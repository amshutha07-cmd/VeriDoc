import { useCallback, useEffect, useState } from "react";
import { Link } from "wouter";

const API_URL = (import.meta.env.VITE_VERIDOC_API_URL as string | undefined)?.replace(/\/$/, "");
type Summary = { rows?: number; evidence_coverage?: number; answer_coverage?: number; citation_rate?: number; average_retries?: number; average_latency?: number };
type EvalState = { status: string; error?: string | null; result?: { completed_at?: string; test_count?: number; baseline?: Summary; crag?: Summary } | null };

function Metric({ label, value }: { label: string; value: string | number }) {
  return <article className="border border-[#d9d1c4] bg-[#f8f5ef] p-5"><div className="font-mono text-[10px] uppercase tracking-[0.14em] text-[#8c857c]">{label}</div><div className="mt-4 font-serif text-3xl">{value}</div></article>;
}

export default function Evaluation() {
  const [state, setState] = useState<EvalState>({ status: "loading", result: null });
  const [running, setRunning] = useState(false);
  const loadStatus = useCallback(async () => {
    if (!API_URL) { setState({ status: "failed", error: "VITE_VERIDOC_API_URL is not configured." }); return; }
    try { const response = await fetch(`${API_URL}/eval/status`); if (!response.ok) throw new Error(`Backend returned ${response.status}`); setState(await response.json()); } catch (error) { setState({ status: "failed", error: error instanceof Error ? error.message : "Could not load evaluation status." }); }
  }, []);
  useEffect(() => { void loadStatus(); }, [loadStatus]);
  useEffect(() => { if (state.status !== "running") return; const timer = window.setInterval(() => { void loadStatus(); }, 3000); return () => window.clearInterval(timer); }, [state.status, loadStatus]);
  async function runEvaluation() {
    if (!API_URL || running) return;
    setRunning(true);
    try { const response = await fetch(`${API_URL}/eval/run`, { method: "POST" }); if (!response.ok) throw new Error(`Backend returned ${response.status}`); setState({ status: "running", result: null }); } catch (error) { setState({ status: "failed", error: error instanceof Error ? error.message : "Could not start evaluation." }); } finally { setRunning(false); }
  }
  const result = state.result;
  const crag = result?.crag;
  return <main className="min-h-screen bg-[#f4f0e8] px-6 py-10 text-[#1e2625] sm:px-12 lg:px-20"><div className="mx-auto max-w-6xl"><div className="mb-10 flex items-start justify-between gap-6 border-b border-[#d9d1c4] pb-6"><div><div className="mb-3 font-mono text-[10px] uppercase tracking-[0.2em] text-[#b96845]">VeriDoc / Evaluation</div><h1 className="font-serif text-4xl tracking-tight">Release evidence</h1><p className="mt-3 max-w-2xl font-serif text-[16px] leading-relaxed text-[#6a706a]">Run the deterministic test set intentionally and inspect the resulting retrieval and answer metrics.</p></div><Link href="/" className="border border-[#1e2625] px-4 py-2 font-mono text-[10px] uppercase tracking-[0.14em] hover:bg-[#1e2625] hover:text-[#f8f5ef]">Back to investigation</Link></div><div className="mb-8 flex flex-wrap items-center gap-3"><button onClick={() => void runEvaluation()} disabled={running || state.status === "running"} className="bg-[#1e2625] px-5 py-3 font-mono text-[10px] uppercase tracking-[0.14em] text-[#f8f5ef] disabled:cursor-not-allowed disabled:opacity-50">{state.status === "running" ? "Evaluation running…" : "Run evaluation"}</button><button onClick={() => void loadStatus()} className="border border-[#1e2625] px-5 py-3 font-mono text-[10px] uppercase tracking-[0.14em]">Refresh status</button><span className="font-mono text-[10px] uppercase tracking-[0.14em] text-[#6e8b78]">Status: {state.status}</span></div>{state.error && <div className="mb-8 border border-[#b96845] bg-[#f8f5ef] p-5 text-sm text-[#8b3f2b]">{state.error}</div>}{!result && state.status !== "running" && !state.error && <section className="border border-[#d9d1c4] bg-[#f8f5ef] p-8"><h2 className="font-serif text-3xl">Evaluation not run yet</h2><p className="mt-4 max-w-2xl font-serif text-[17px] leading-relaxed text-[#4c514d]">Click Run evaluation to execute the existing deterministic Apple test set. Results will be saved by the backend and shown here after completion.</p></section>}{state.status === "running" && <section className="border border-[#d9d1c4] bg-[#f8f5ef] p-8"><h2 className="font-serif text-3xl">Evaluation in progress</h2><p className="mt-4 font-serif text-[17px] text-[#4c514d]">The evaluator is running in the background. This may take time because it invokes the retrieval graph for each test case.</p></section>}{result && <><section className="mb-8 border border-[#d9d1c4] bg-[#f8f5ef] p-6"><div className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#b96845]">Completed run</div><div className="mt-3 font-serif text-2xl">{result.test_count ?? 0} test cases evaluated</div><div className="mt-2 font-mono text-[10px] text-[#8c857c]">{result.completed_at ?? "timestamp unavailable"}</div></section><h2 className="mb-4 font-serif text-2xl">CRAG results</h2><div className="grid gap-4 md:grid-cols-3"><Metric label="Evidence coverage" value={crag?.evidence_coverage ?? "—"} /><Metric label="Answer coverage" value={crag?.answer_coverage ?? "—"} /><Metric label="Citation rate" value={crag?.citation_rate ?? "—"} /><Metric label="Average retries" value={crag?.average_retries ?? "—"} /><Metric label="Average latency" value={crag?.average_latency ? `${crag.average_latency}s` : "—"} /><Metric label="Rows completed" value={crag?.rows ?? "—"} /></div></>}</div></main>;
}
