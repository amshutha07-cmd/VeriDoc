/* Reads the backend's answer packet. extractSsePayload and normalizeEvidence are the same parsing the app always used. */

export type EvidenceSource = {
  id: string;
  source?: string;
  domain: string;
  title: string;
  file: string;
  page: string;
  tag: string;
  excerpt: string;
  organization?: string;
  documentType?: string;
  year?: string;
};

export function extractSsePayload(raw: string): any | null {
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

const known = (value: unknown): string | undefined => {
  if (value === null || value === undefined) return undefined;
  const text = String(value).trim();
  return text && text.toLowerCase() !== "unknown" ? text : undefined;
};

export function normalizeEvidence(payload: any): EvidenceSource[] {
  const items = payload?.evidence ?? payload?.docs ?? payload?.result?.evidence ?? payload?.result?.docs ?? payload?.data?.evidence ?? payload?.data?.docs ?? [];
  if (!Array.isArray(items)) return [];

  return items.map((item: any, index: number) => {
    const metadata = item?.metadata ?? item ?? {};
    const file = String(metadata.source ?? metadata.file ?? "source");
    const rawPage = String(metadata.page_label ?? metadata.page ?? "?");
    const page = rawPage.toLowerCase().startsWith("p") ? rawPage : `p. ${rawPage}`;
    const category = String(metadata.category ?? metadata.document_type ?? "Evidence");

    return {
      id: String(index + 1).padStart(2, "0"),
      domain: category,
      title: String(metadata.title ?? metadata.document_title ?? file),
      file,
      page,
      tag: String(item?.tag ?? item?.support ?? "Evidence"),
      source: file,
      excerpt: String(item?.excerpt ?? item?.page_content ?? metadata.excerpt ?? "No excerpt returned."),
      organization: known(metadata.organization),
      documentType: known(metadata.document_type),
      year: known(metadata.publication_year),
    };
  });
}

/** The first sentence of a passage, used as the one-line claim in the source list. */
export function claimText(excerpt: string): string {
  const raw = (excerpt || "").replace(/^[\s\d.,;:()\-]+/, "");
  const first = raw.split(/[.!?]/)[0].trim();
  return first.length >= 12 ? first : raw.slice(0, 140).trim() || "Passage retrieved from the corpus.";
}

/** Splits a passage into its first sentence (highlighted in the reader) and the rest. */
export function splitLead(text: string): [string, string] {
  const match = text.match(/^(.{20,}?[.!?])(\s|$)/s);
  if (!match) return [text, ""];
  return [match[1], text.slice(match[1].length)];
}

export const hasPage = (source: EvidenceSource) => Boolean(source.page) && source.page !== "p. ?";

/** Shown only when no backend is configured. It is a fixed sample and says so on screen. */
export const SAMPLE_QUESTION = "What does Article 21 of the Constitution say?";
export const SAMPLE_ANSWER =
  "Article 21 of the Constitution of India says that **no person shall be deprived of his life or personal liberty except according to procedure established by law**.";
export const SAMPLE_SOURCES: EvidenceSource[] = [
  {
    id: "01",
    domain: "Legal",
    title: "Constitution of India",
    file: "Constitution of India",
    source: "Constitution of India",
    page: "sample",
    tag: "Sample",
    excerpt: "21. Protection of life and personal liberty.—No person shall be deprived of his life or personal liberty except according to procedure established by law.",
    documentType: "Constitution",
  },
];
