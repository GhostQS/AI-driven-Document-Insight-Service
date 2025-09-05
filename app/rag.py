from dataclasses import dataclass
from typing import List, Optional, Dict, Any

import numpy as np
from sentence_transformers import SentenceTransformer
try:
    import faiss  # type: ignore
    _FAISS_AVAILABLE = True
except Exception:
    faiss = None  # type: ignore
    _FAISS_AVAILABLE = False


@dataclass
class RAGChunk:
    text: str
    metadata: Dict[str, Any]


def chunk_text(text: str, chunk_size: int = 600, overlap: int = 100) -> List[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i:i + chunk_size]
        chunks.append(" ".join(chunk))
        i += chunk_size - overlap
        if i <= 0:
            break
    return chunks


class RAGIndex:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.index = None  # type: ignore
        self.embeddings: Optional[np.ndarray] = None
        self.chunks: List[RAGChunk] = []

    def add_text(self, text: str, metadata: Optional[Dict[str, Any]] = None):
        metadata = metadata or {}
        emb = self.model.encode([text], normalize_embeddings=True)
        if self.index is None:
            if _FAISS_AVAILABLE:
                d = emb.shape[1]
                self.index = faiss.IndexFlatIP(d)
            self.embeddings = emb
        else:
            self.embeddings = np.vstack([self.embeddings, emb])
        # Add to FAISS if available
        if _FAISS_AVAILABLE and self.index is not None:
            self.index.add(emb.astype(np.float32))
        self.chunks.append(RAGChunk(text=text, metadata=metadata))

    def search(self, query: str, top_k: int = 5) -> List[RAGChunk]:
        if self.embeddings is None or not self.chunks:
            return []
        q = self.model.encode([query], normalize_embeddings=True).astype(np.float32)
        if _FAISS_AVAILABLE and self.index is not None:
            scores, idxs = self.index.search(q, top_k)
            indices = [int(i) for i in idxs[0] if int(i) < len(self.chunks)]
        else:
            # NumPy cosine similarity fallback
            emb_mat = self.embeddings.astype(np.float32)
            # q is shape (1, d)
            sims = np.dot(emb_mat, q[0])  # since normalized, dot = cosine
            indices = np.argsort(-sims)[:top_k].tolist()
        results = [self.chunks[i] for i in indices]
        return results
