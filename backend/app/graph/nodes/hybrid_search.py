# backend/app/graph/nodes/hybrid_search.py
import math
import re
from collections import Counter
from typing import Any, Dict, List, Tuple


class BM25Index:
    """Lightweight in-memory BM25Okapi implementation for statutory and lexical retrieval."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus: List[str] = []
        self.doc_ids: List[str] = []
        self.doc_len: List[int] = []
        self.avg_dl: float = 0.0
        self.doc_freqs: List[Counter] = []
        self.idf: Dict[str, float] = {}

    @staticmethod
    def tokenize(text: str) -> List[str]:
        return re.findall(r"\b[A-Za-z0-9_]{2,}\b", text.lower())

    def fit(self, docs: List[str], doc_ids: List[str]):
        self.corpus = docs
        self.doc_ids = doc_ids
        self.doc_len = []
        self.doc_freqs = []
        df: Counter = Counter()

        for doc in docs:
            tokens = self.tokenize(doc)
            self.doc_len.append(len(tokens))
            freq = Counter(tokens)
            self.doc_freqs.append(freq)
            for t in freq:
                df[t] += 1

        n_docs = len(docs)
        self.avg_dl = sum(self.doc_len) / max(n_docs, 1)

        for term, freq in df.items():
            # Standard Lucene/BM25 IDF smoothing
            self.idf[term] = math.log(1.0 + (n_docs - freq + 0.5) / (freq + 0.5))

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float, int]]:
        query_tokens = self.tokenize(query)
        scores: List[float] = [0.0] * len(self.corpus)

        for q in query_tokens:
            if q not in self.idf:
                continue
            idf_val = self.idf[q]
            for idx, freq in enumerate(self.doc_freqs):
                tf = freq.get(q, 0)
                if tf == 0:
                    continue
                num = tf * (self.k1 + 1.0)
                denom = tf + self.k1 * (1.0 - self.b + self.b * (self.doc_len[idx] / self.avg_dl))
                scores[idx] += idf_val * (num / denom)

        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return [(self.doc_ids[idx], score, idx) for idx, score in ranked[:top_k] if score > 0.0]


def reciprocal_rank_fusion(
    dense_ranked_ids: List[str],
    sparse_ranked_ids: List[str],
    k: int = 60,
    top_n: int = 5,
) -> List[Tuple[str, float]]:
    """Combines dense vector ranks and BM25 ranks via Reciprocal Rank Fusion (RRF)."""
    rrf_scores: Dict[str, float] = {}

    for rank, doc_id in enumerate(dense_ranked_ids, start=1):
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k + rank))

    for rank, doc_id in enumerate(sparse_ranked_ids, start=1):
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k + rank))

    ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return ranked[:top_n]
