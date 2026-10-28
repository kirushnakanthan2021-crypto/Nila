"""Lightweight retrieval and memory helpers for Nila.

These helpers are deterministic and dependency-light. They do not pretend to be
a trained model: they improve normalization, duplicate detection and ranking.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter
from difflib import SequenceMatcher

# Extend this map as the user's preferred Tanglish vocabulary becomes known.
SYNONYMS = {
    "enna": "what", "ennna": "what", "eppadi": "how", "epdi": "how",
    "pannu": "do", "pannunga": "do", "seyyu": "do", "seiya": "do",
    "theriyum": "know", "therium": "know", "venum": "want", "vendum": "want",
    "illa": "no", "illai": "no", "irukku": "have", "irukkum": "have",
    "ninaivu": "memory", "nyabagam": "memory", "padikka": "learn",
    "kathu": "learn", "katrukkol": "learn",
}
TAMIL_RANGE = ("\u0B80", "\u0BFF")


def normalize_text(value: str) -> str:
    """Normalize Unicode, case, punctuation, and common Tanglish variants."""
    value = unicodedata.normalize("NFKC", str(value or "")).casefold()
    value = value.replace("’", "'").replace("‘", "'")
    value = re.sub(r"[^\w\s\u0B80-\u0BFF']", " ", value, flags=re.UNICODE)
    tokens = re.findall(r"[a-z0-9']+|[\u0B80-\u0BFF]+", value)
    normalized = [SYNONYMS.get(token, token) for token in tokens]
    return " ".join(normalized)


def token_counts(value: str) -> Counter[str]:
    return Counter(normalize_text(value).split())


def lexical_score(query: str, document: str) -> float:
    """Simple BM25-like lexical score suitable as a fallback, not true BM25."""
    q = token_counts(query)
    d = token_counts(document)
    if not q or not d:
        return 0.0
    overlap = sum(min(count, d[token]) for token, count in q.items())
    coverage = overlap / max(1, sum(q.values()))
    length_penalty = 1.0 / (1.0 + abs(sum(d.values()) - 80) / 160)
    return round(coverage * length_penalty, 6)


def is_duplicate_fact(candidate: str, existing: list[str], threshold: float = 0.92) -> bool:
    """Detect exact/near duplicates after normalization; never deletes data."""
    normalized = normalize_text(candidate)
    if not normalized:
        return False
    for fact in existing:
        other = normalize_text(fact)
        if normalized == other:
            return True
        if len(normalized) >= 24 and len(other) >= 24:
            if SequenceMatcher(None, normalized, other).ratio() >= threshold:
                return True
    return False


def summarize_messages(messages: list[dict], max_chars: int = 1200) -> str:
    """Create a deterministic extractive summary from a conversation batch."""
    selected: list[str] = []
    seen: set[str] = set()
    for item in messages:
        role = str(item.get("role", ""))
        content = re.sub(r"\s+", " ", str(item.get("content", item.get("text", "")))).strip()
        if role not in {"user", "assistant"} or len(content) < 12:
            continue
        key = normalize_text(content)
        if key and key not in seen:
            seen.add(key)
            selected.append(f"{role}: {content}")
    summary = "\n".join(selected)
    if len(summary) > max_chars:
        summary = summary[: max_chars - 1].rsplit(" ", 1)[0] + "…"
    return summary
