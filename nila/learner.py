"""
Controlled learning module.

Nila can ingest text or simple web pages (stdlib only), extract short facts,
and store them as knowledge with source attribution.
It does NOT automatically rewrite its own source code.
"""
from __future__ import annotations
import re
import urllib.request
from html.parser import HTMLParser
from typing import Iterable
from .store import Store
from .security import validate_public_http_url
from .brain import is_duplicate_fact
from .engine import tokens


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._chunks: list[str] = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self._skip = True

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"}:
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            text = data.strip()
            if text:
                self._chunks.append(text)

    def get_text(self) -> str:
        return " ".join(self._chunks)


def fetch_url_text(url: str, timeout: int = 12, max_chars: int = 12000) -> str:
    validate_public_http_url(url)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "NilaLearner/0.3 (personal research; contact via GitHub)"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        charset = "utf-8"
        ctype = resp.headers.get_content_charset()
        if ctype:
            charset = ctype
        html = raw.decode(charset, errors="replace")
    parser = _TextExtractor()
    parser.feed(html)
    text = parser.get_text()
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


def split_into_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    # also split on Tamil danda if present
    more: list[str] = []
    for p in parts:
        more.extend(re.split(r"[\u0964\u0965]", p))
    return [p.strip() for p in more if len(p.strip()) > 25]


def extract_candidate_facts(text: str, topic: str, max_facts: int = 8) -> list[str]:
    topic_tokens = set(tokens(topic))
    sentences = split_into_sentences(text)
    scored: list[tuple[int, str]] = []
    for s in sentences:
        stoks = set(tokens(s))
        overlap = len(topic_tokens & stoks)
        lower = s.lower()
        bonus = 0
        if any(
            k in lower
            for k in (" is ", " are ", " means ", " defined as ", " refers to ", " என்பது", " ஆகும்")
        ):
            bonus += 2
        if overlap or bonus:
            scored.append((overlap + bonus, s))
    scored.sort(key=lambda x: x[0], reverse=True)
    facts = []
    seen = set()
    for _, sent in scored:
        key = sent[:80].lower()
        if key in seen:
            continue
        seen.add(key)
        facts.append(sent if len(sent) <= 400 else sent[:397] + "...")
        if len(facts) >= max_facts:
            break
    return facts


def learn_from_text(
    store: Store,
    topic: str,
    text: str,
    source: str,
    verified: bool = False,
    max_facts: int = 8,
) -> dict:
    facts = extract_candidate_facts(text, topic, max_facts=max_facts)
    existing = [str(item.get("content", "")) for item in store.all_items(limit=2000)]
    unique_facts = [fact for fact in facts if not is_duplicate_fact(fact, existing)]
    ids = []
    for i, fact in enumerate(unique_facts, start=1):
        title = f"{topic} — fact {i}"
        kid = store.add_knowledge(
            title=title,
            content=fact,
            source=source,
            verified=verified,
            topic=topic,
        )
        ids.append(kid)
    summary = f"Extracted {len(facts)} candidate facts; skipped {len(facts) - len(unique_facts)} duplicates."
    sid = store.add_learning_session(
        topic=topic,
        summary=summary,
        sources_used=source,
        facts_added=len(unique_facts),
    )
    store.log_interaction("learn_text", f"{topic}:{len(facts)}")
    return {
        "session_id": sid,
        "topic": topic,
        "facts_added": len(unique_facts),
        "knowledge_ids": ids,
        "facts": unique_facts,
        "summary": summary,
    }


def learn_from_url(
    store: Store,
    topic: str,
    url: str,
    verified: bool = False,
    max_facts: int = 8,
) -> dict:
    text = fetch_url_text(url)
    if len(text) < 80:
        raise ValueError("Page text too short or could not be extracted usefully.")
    return learn_from_text(
        store,
        topic=topic,
        text=text,
        source=url,
        verified=verified,
        max_facts=max_facts,
    )


def learn_from_multiple_sources(
    store: Store,
    topic: str,
    sources: Iterable[str],
    verified: bool = False,
    max_facts_per_source: int = 5,
) -> dict:
    all_facts: list[str] = []
    all_ids: list[int] = []
    used: list[str] = []
    errors: list[str] = []

    for src in sources:
        src = src.strip()
        if not src:
            continue
        try:
            if src.startswith("http://") or src.startswith("https://"):
                result = learn_from_url(
                    store, topic, src, verified=verified, max_facts=max_facts_per_source
                )
            else:
                result = learn_from_text(
                    store,
                    topic,
                    src,
                    source="user-provided text",
                    verified=verified,
                    max_facts=max_facts_per_source,
                )
            all_facts.extend(result["facts"])
            all_ids.extend(result["knowledge_ids"])
            used.append(src if len(src) < 120 else src[:117] + "...")
        except Exception as exc:
            errors.append(f"{src[:60]}... -> {exc}")

    summary = (
        f"Learned from {len(used)} source(s). "
        f"Added {len(all_facts)} facts. "
        + (f"Errors: {len(errors)}." if errors else "")
    )
    sid = store.add_learning_session(
        topic=topic,
        summary=summary,
        sources_used="; ".join(used)[:2000],
        facts_added=len(all_facts),
    )
    return {
        "session_id": sid,
        "topic": topic,
        "facts_added": len(all_facts),
        "knowledge_ids": all_ids,
        "facts": all_facts,
        "sources_used": used,
        "errors": errors,
        "summary": summary,
    }
