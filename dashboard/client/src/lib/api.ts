// One place that reads VITE_VERIDOC_API_URL, so every page talks to the backend the same way.
const raw = import.meta.env.VITE_VERIDOC_API_URL as string | undefined;

/** Backend base URL without a trailing slash, or undefined when none is configured. */
export const API_BASE: string | undefined = raw ? raw.replace(/\/$/, "") : undefined;
export const HAS_BACKEND = Boolean(API_BASE);

/** FastAPI sends { detail } on errors. Show that when present, otherwise the status code. */
export async function errorDetail(response: Response): Promise<string> {
  try {
    const body = await response.clone().json();
    if (typeof body?.detail === "string" && body.detail.trim()) return body.detail;
  } catch {
    // Not JSON. Fall through to the status code.
  }
  return `Backend returned ${response.status}`;
}

/** 12480 becomes 12,480. Indian digit grouping is used (1,24,800), as the corpus is Indian law. */
export function formatCount(value: number | string | null | undefined): string {
  if (typeof value === "number" && Number.isFinite(value)) return value.toLocaleString("en-IN");
  if (typeof value === "string" && value.trim() && !Number.isNaN(Number(value))) return Number(value).toLocaleString("en-IN");
  return "—";
}
