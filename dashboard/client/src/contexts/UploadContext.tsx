/* Upload state shared by every page, so "Add documents" works from anywhere.
   The request is the same one the app always made: POST {API}/ingest with FormData fields "domain" and "files". */
import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import { toast } from "sonner";
import { API_BASE, errorDetail } from "@/lib/api";

export type UploadDomain = "legal" | "corporate";
export type UploadStatus = "uploading" | "indexed" | "failed";

export type UploadItem = {
  id: string;
  name: string;
  domain: UploadDomain;
  status: UploadStatus;
  message?: string;
};

/** What the backend reported for the last successful upload. It is not stored on the server. */
export type UploadResult = {
  files: string[];
  domain: UploadDomain;
  pages: number;
  chunks: number;
  totalChunks?: number;
  collection?: string;
  at: Date;
};

type UploadContextValue = {
  items: UploadItem[];
  lastResult: UploadResult | null;
  uploading: boolean;
  domain: UploadDomain;
  setDomain: (domain: UploadDomain) => void;
  /** Goes up by one after every successful upload. Pages watch it to reload their counts. */
  ingestVersion: number;
  dialogOpen: boolean;
  openDialog: () => void;
  closeDialog: () => void;
  addFiles: (files: FileList | File[] | null) => Promise<void>;
};

const UploadContext = createContext<UploadContextValue | undefined>(undefined);

const ALLOWED = [".pdf", ".docx"];
const isAllowed = (name: string) => ALLOWED.some((ext) => name.toLowerCase().endsWith(ext));
let counter = 0;
const nextId = () => `upload-${Date.now()}-${counter++}`;

export function UploadProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<UploadItem[]>([]);
  const [lastResult, setLastResult] = useState<UploadResult | null>(null);
  const [uploading, setUploading] = useState(false);
  const [domain, setDomain] = useState<UploadDomain>("legal");
  const [ingestVersion, setIngestVersion] = useState(0);
  const [dialogOpen, setDialogOpen] = useState(false);

  const openDialog = useCallback(() => setDialogOpen(true), []);
  const closeDialog = useCallback(() => setDialogOpen(false), []);

  const addFiles = useCallback(
    async (input: FileList | File[] | null) => {
      if (!input || uploading) return;
      const selected = Array.from(input);
      if (!selected.length) return;

      const valid = selected.filter((file) => isAllowed(file.name));
      const rejected = selected.filter((file) => !isAllowed(file.name));

      const rejectedItems: UploadItem[] = rejected.map((file) => ({
        id: nextId(),
        name: file.name,
        domain,
        status: "failed",
        message: "Only PDF and DOCX files can be added.",
      }));
      if (rejected.length) {
        toast.error("Some files were skipped", { description: "Only PDF and DOCX files can be added." });
      }
      if (!valid.length) {
        setItems((current) => [...rejectedItems, ...current]);
        return;
      }

      const validItems: UploadItem[] = valid.map((file) => ({ id: nextId(), name: file.name, domain, status: "uploading" }));
      const ids = new Set(validItems.map((item) => item.id));
      const settle = (status: UploadStatus, message?: string) =>
        setItems((current) => current.map((item) => (ids.has(item.id) ? { ...item, status, message } : item)));

      setItems((current) => [...validItems, ...rejectedItems, ...current]);

      if (!API_BASE) {
        settle("failed", "Not sent. No backend is configured.");
        toast.error("Backend URL is not configured", {
          description: "Set VITE_VERIDOC_API_URL before uploading documents.",
        });
        return;
      }

      const formData = new FormData();
      formData.append("domain", domain);
      valid.forEach((file) => formData.append("files", file));

      setUploading(true);
      try {
        const response = await fetch(`${API_BASE}/ingest`, { method: "POST", body: formData });
        if (!response.ok) throw new Error(await errorDetail(response));

        const result = await response.json();
        settle("indexed");
        setLastResult({
          files: Array.isArray(result.files) ? result.files : valid.map((file) => file.name),
          domain,
          pages: Number(result.pages ?? 0),
          chunks: Number(result.chunks ?? 0),
          totalChunks: typeof result.total_chunks === "number" ? result.total_chunks : undefined,
          collection: typeof result.collection === "string" ? result.collection : undefined,
          at: new Date(),
        });
        setIngestVersion((version) => version + 1);
        toast.success("Documents indexed", {
          description: `${result.pages ?? 0} pages and ${result.chunks ?? 0} chunks added to VeriDoc.`,
        });
      } catch (error) {
        const message = error instanceof Error ? error.message : "Check the backend logs.";
        settle("failed", message);
        toast.error("Document ingestion failed", { description: message });
      } finally {
        setUploading(false);
      }
    },
    [domain, uploading]
  );

  const value = useMemo<UploadContextValue>(
    () => ({ items, lastResult, uploading, domain, setDomain, ingestVersion, dialogOpen, openDialog, closeDialog, addFiles }),
    [items, lastResult, uploading, domain, ingestVersion, dialogOpen, openDialog, closeDialog, addFiles]
  );

  return <UploadContext.Provider value={value}>{children}</UploadContext.Provider>;
}

export function useUpload() {
  const context = useContext(UploadContext);
  if (!context) throw new Error("useUpload must be used inside UploadProvider");
  return context;
}
