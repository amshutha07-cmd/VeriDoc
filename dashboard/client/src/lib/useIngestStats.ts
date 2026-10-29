/* Chunk counts from GET {API}/ingest/stats, shared by Ask, Registry and Ingestion.
   It reloads by itself after every successful upload. */
import { useCallback, useEffect, useState } from "react";
import { useUpload } from "@/contexts/UploadContext";
import { API_BASE, HAS_BACKEND, errorDetail } from "@/lib/api";

export type IngestStats = { handbook_chunks?: number; legal_chunks?: number; chunk_count?: number };
export type StatsStatus = "loading" | "ready" | "error" | "nobackend";

export function useIngestStats() {
  const { ingestVersion } = useUpload();
  const [stats, setStats] = useState<IngestStats | null>(null);
  const [status, setStatus] = useState<StatsStatus>(HAS_BACKEND ? "loading" : "nobackend");
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    if (!API_BASE) {
      setStatus("nobackend");
      return;
    }
    let cancelled = false;
    setStatus((current) => (current === "ready" ? current : "loading"));
    fetch(`${API_BASE}/ingest/stats`)
      .then(async (response) => {
        if (!response.ok) throw new Error(await errorDetail(response));
        return response.json();
      })
      .then((data: IngestStats) => {
        if (cancelled) return;
        setStats(data);
        setError(null);
        setStatus("ready");
      })
      .catch((reason) => {
        if (cancelled) return;
        setError(reason instanceof Error ? reason.message : "Could not load corpus stats.");
        setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, [ingestVersion, tick]);

  const refresh = useCallback(() => setTick((value) => value + 1), []);

  return {
    stats,
    status,
    error,
    refresh,
    legalChunks: stats?.legal_chunks,
    corporateChunks: stats?.handbook_chunks ?? stats?.chunk_count,
  };
}
