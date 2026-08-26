export interface NodeEvent {
    node: "retrieve" | "rerank" | "grade_docs" | "rewrite" | "generate";
    docs?: { source: string; page: string }[];
    grade?: string;
    retries?: number;
    answer?: string;
}

export interface IngestResponse {
    pages: number;
    chunks: number;
}