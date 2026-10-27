"""
Optional semantic embeddings for better retrieval ranking.

Default: deterministic hash embedding (no pip packages).
Upgrade: pip install sentence-transformers  (see requirements-optional.txt)

Env:
  NILA_EMBEDDINGS=off|hash|st   (default: hash; st = sentence-transformers if installed)
"""
from __future__ import annotations

import hashlib
import math
import os
import re
from functools import lru_cache
from typing import Iterable

_DIM = 256


def embedding_mode() -> str:
    mode = (os.environ.get("NILA_EMBEDDINGS") or "hash").strip().lower()
    if mode in {"off", "0", "false", "none"}:
        return "off"
    if mode in {"st", "sentence", "sentence-transformers", "transformer"}:
        return "st"
    return "hash"


def _tokenize(text: str) -> list[str]:
    latin = re.findall(r"[a-zA-Z0-9_]+", text.lower())
    tamil = re.findall(r"[\u0B80-\u0BFF]+", text)
    return [t for t in latin + tamil if len(t) > 1]


def _hash_embed(text: str, dim: int = _DIM) -> list[float]:
    vec = [0.0] * dim
    for tok in _tokenize(text):
        h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if (h // dim) % 2 == 0 else -1.0
        vec[idx] += sign
    # L2 normalize
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


@lru_cache(maxsize=1)
def _st_model():
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
    except Exception:
        return None
    # small multilingual model works better with Tamil+English mix
    name = os.environ.get("NILA_ST_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    try:
        return SentenceTransformer(name)
    except Exception:
        return None


def embed_text(text: str) -> list[float] | None:
    mode = embedding_mode()
    if mode == "off":
        return None
    if mode == "st":
        model = _st_model()
        if model is not None:
            try:
                vec = model.encode([text], normalize_embeddings=True)[0]
                return [float(x) for x in vec]
            except Exception:
                pass
        # fall through to hash
    return _hash_embed(text)


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    return float(sum(x * y for x, y in zip(a, b)))


def semantic_score(query: str, document: str) -> float:
    q = embed_text(query)
    d = embed_text(document)
    if q is None or d is None:
        return 0.0
    return max(0.0, cosine(q, d))


def backend_name() -> str:
    mode = embedding_mode()
    if mode == "off":
        return "off"
    if mode == "st" and _st_model() is not None:
        return "sentence-transformers"
    return "hash"
