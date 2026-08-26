import { useState } from "react";
import { askStream, ingestFiles } from "./api/ragApi";
import type { NodeEvent } from "./types/rag";

function App() {
    const [question, setQuestion] = useState("");
    const [trace, setTrace] = useState<NodeEvent[]>([]);
    const [answer, setAnswer] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const handleAsk = () => {
        setTrace([]);
        setAnswer("");
        setError("");
        setLoading(true);
        askStream(
            question,
            "session-1",
            (event: NodeEvent) => {
                setTrace((prev) => [...prev, event]);
                if (event.answer) setAnswer(event.answer);
            },
            () => setLoading(false),
            (message: string) => {
                setError(message);
                setLoading(false);
            }
        );
    };

    const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!e.target.files) return;
        const result = await ingestFiles(e.target.files);
        alert(`Ingested ${result.pages} pages, ${result.chunks} chunks`);
    };

    return (
        <div style={{ maxWidth: 700, margin: "2rem auto", fontFamily: "sans-serif" }}>
            <h1>Self-Correcting RAG</h1>

            <input type="file" multiple accept=".pdf" onChange={handleUpload} />

            <div style={{ marginTop: 20 }}>
                <input
                    style={{ width: "70%" }}
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="Ask a question..."
                />
                <button onClick={handleAsk} disabled={loading}>
                    {loading ? "Thinking..." : "Ask"}
                </button>
            </div>

            <div style={{ marginTop: 20 }}>
                <h3>Trace</h3>
                {trace.map((t, i) => (
                    <div key={i}>
                        <b>{t.node}</b>{t.grade ? ` — grade: ${t.grade}` : ""}{t.retries !== undefined ? ` — retries: ${t.retries}` : ""}
                    </div>
                ))}
            </div>

            {error && (
                <div style={{ marginTop: 20, padding: 12, background: "#fee", color: "#900" }}>
                    <b>Error:</b> {error}
                </div>
            )}

            {answer && (
                <div style={{ marginTop: 20, padding: 12, background: "#f0f0f0" }}>
                    <b>Answer:</b>
                    <p>{answer}</p>
                </div>
            )}
        </div>
    );
}

export default App;