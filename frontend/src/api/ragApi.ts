const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function ingestFiles(files: FileList): Promise<{ pages: number; chunks: number }> {
    const formData = new FormData();
    Array.from(files).forEach((f) => formData.append("files", f));
    const res = await fetch(`${API_BASE}/ingest`, { method: "POST", body: formData });
    if (!res.ok) throw new Error(`Ingest failed: ${res.status}`);
    return res.json();
}

function processBuffer(
    buffer: string,
    onNode: (event: any) => void,
    onError?: (message: string) => void
): string {
    const lines = buffer.split(/\r?\n\r?\n/);

    const remaining = lines.pop() || "";

    for (const chunk of lines) {
        if (!chunk.trim()) continue;
        console.log("RAW CHUNK:", JSON.stringify(chunk));
        const parts = chunk.split(/\r?\n/);

        const eventLine = parts.find((l) => l.startsWith("event:"));
        const dataLine = parts.find((l) => l.startsWith("data:"));
        const eventType = eventLine ? eventLine.replace("event:", "").trim() : "node";
        console.log("PARSED eventType:", eventType);

        if (dataLine) {
            try {
                const data = JSON.parse(dataLine.replace("data:", "").trim());
                if (eventType === "error" && onError) {
                    onError(data.message);
                } else {
                    onNode(data);
                }
            } catch (e) {
                console.error("JSON parse error:", e, "raw:", dataLine);
            }
        }
    }
    return remaining;
}

export function askStream(
    question: string,
    threadId: string,
    onNode: (event: any) => void,
    onDone: () => void,
    onError?: (message: string) => void
) {
    fetch(`${API_BASE}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, thread_id: threadId }),
    })
        .then(async (res) => {
            const reader = res.body!.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    // process anything left in buffer when stream closes
                    if (buffer.trim()) {
                        processBuffer(buffer + "\n\n", onNode, onError);
                    }
                    break;
                }
                buffer += decoder.decode(value, { stream: true });
                buffer = processBuffer(buffer, onNode, onError);
            }
            onDone();
        })
        .catch((err) => {
            console.error("fetch error:", err);
            if (onError) onError(err.message);
        });
}