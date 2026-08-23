"""Vector store service (ChromaDB) with a dict fallback.

ChromaDB may not be installed in minimal environments; we fall back to an
in-process cosine-similarity store so the app still runs (used for similar-error
recall and is fully replaced once ChromaDB is present).

Embeddings: when no DeepSeek key is configured we use a deterministic hashing
bag-of-words embedding so similarity still works locally without network calls.
"""
from __future__ import annotations

import hashlib
import math
import threading
from typing import Optional

from app.core.config import settings

_lock = threading.Lock()
_fallback_store: dict[int, list[float]] = {}


def _get_collection():
    try:
        import chromadb

        client = chromadb.PersistentClient(path=str(settings.chroma_dir))
        return client.get_or_create_collection(name="recall_errors")
    except Exception:
        return None


_COLLECTION = None


def _collection():
    global _COLLECTION
    if _COLLECTION is None:
        _COLLECTION = _get_collection()
    return _COLLECTION


def _hash_embedding(text: str, dim: int = 256) -> list[float]:
    """Deterministic local embedding (hashing trick)."""
    vec = [0.0] * dim
    tokens = [t for t in text.lower().replace("\n", " ").split() if t]
    for tok in tokens:
        h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
        vec[h % dim] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def embed_text(text: str) -> list[float]:
    return _hash_embedding(text or "")


def add_vector(error_id: int, text: str) -> None:
    vec = embed_text(text)
    collection = _collection()
    if collection is not None:
        try:
            collection.upsert(
                ids=[str(error_id)],
                embeddings=[vec],
                metadatas=[{"error_id": error_id}],
                documents=[text],
            )
            return
        except Exception:
            pass
    with _lock:
        _fallback_store[error_id] = vec


def update_vector(error_id: int, text: str) -> None:
    add_vector(error_id, text)


def delete_vector(error_id: int) -> None:
    collection = _collection()
    if collection is not None:
        try:
            collection.delete(ids=[str(error_id)])
        except Exception:
            pass
    with _lock:
        _fallback_store.pop(error_id, None)


def delete_notebook_vectors(notebook_id: int) -> None:
    """Best-effort bulk delete by metadata filter (Chroma) or no-op fallback."""
    collection = _collection()
    if collection is not None:
        try:
            collection.delete(where={"notebook_id": notebook_id})
        except Exception:
            pass


def search_similar(text: str, top_k: int = 5, notebook_id: Optional[int] = None) -> list[int]:
    vec = embed_text(text)
    collection = _collection()
    if collection is not None:
        try:
            kwargs = {"query_embeddings": [vec], "n_results": top_k}
            if notebook_id is not None:
                kwargs["where"] = {"notebook_id": notebook_id}
            res = collection.query(**kwargs)
            ids = (res.get("ids") or [[]])[0]
            return [int(i) for i in ids]
        except Exception:
            pass
    # Fallback: cosine over in-memory store.
    with _lock:
        scored = []
        for eid, ev in _fallback_store.items():
            dot = sum(a * b for a, b in zip(vec, ev))
            scored.append((eid, dot))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [eid for eid, _ in scored[:top_k]]
