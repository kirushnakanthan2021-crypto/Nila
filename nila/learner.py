"""
Controlled learning module.

Nila can ingest text or simple web pages (stdlib only), extract short facts,
and store them as knowledge with source attribution.
It does NOT automatically rewrite its own source code.
"""
from __future__ import annotations
import re
import urllib.request
import urllib.error
import ipaddress
import socket
import time
from urllib.parse import urljoin, urlsplit
from html.parser import HTMLParser
from typing import Iterable
from .store import Store
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


def _validate_public_https_url(url: str) -> str:
    """Reject non-HTTPS URLs and any host resolving to a non-public IP."""
    try:
        parsed = urlsplit(url)
        if parsed.scheme.lower() != "https" or not parsed.hostname:
            raise ValueError("Only public HTTPS URLs are allowed.")
        if parsed.username or parsed.password:
            raise ValueError("URLs containing credentials are not allowed.")
        if parsed.port not in (None, 443):
            raise ValueError("Only the standard HTTPS port is allowed.")
        host = parsed.hostname.rstrip(".").encode("idna").decode("ascii")
        if host.lower() in {"localhost", "localhost.localdomain"}:
            raise ValueError("Private or local network destinations are blocked.")
        addresses = {item[4][0] for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)}
        if not addresses:
            raise ValueError("Could not resolve URL host.")
        for address in addresses:
            ip = ipaddress.ip_address(address.split("%", 1)[0])
            if not ip.is_global:
                raise ValueError("Private, reserved, and local network destinations are blocked.")
        return url
    except (socket.gaierror, UnicodeError, ValueError) as exc:
        if isinstance(exc, ValueError) and str(exc).startswith(("Only ", "URLs ", "Private ", "Could not ")):
            raise
        raise ValueError("Invalid or unsafe URL.") from exc


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_url_text(url: str, timeout: int = 12, max_chars: int = 12000) -> str:
    """Fetch a bounded public HTTPS page; validate every redirect target."""
    current = _validate_public_https_url(url)
    opener = urllib.request.build_opener(_NoRedirect)
    deadline = time.monotonic() + timeout
    for _ in range(4):
        remaining = max(1, deadline - time.monotonic())
        req = urllib.request.Request(
            current,
            headers={"User-Agent": "NilaLearner/0.5 (+https://github.com/kirushnakanthan2021-crypto/Nila)",
                     "Accept": "text/html,text/plain"},
        )
        try:
            with opener.open(req, timeout=remaining) as resp:
                content_type = resp.headers.get_content_type().lower()
                if content_type not in {"text/html", "text/plain", "application/xhtml+xml"}:
                    raise ValueError("Only HTML or plain-text pages can be learned.")
                raw = resp.read(1_000_001)
                if len(raw) > 1_000_000:
                    raise ValueError("Web page exceeds the 1 MB learning limit.")
                charset = resp.headers.get_content_charset() or "utf-8"
                html = raw.decode(charset, errors="replace")
                break
        except urllib.error.HTTPError as exc:
            if exc.code not in {301, 302, 303, 307, 308}:
                raise ValueError(f"Page request failed with HTTP {exc.code}.") from exc
            location = exc.headers.get("Location")
            if not location:
                raise ValueError("Redirect did not include a destination.")
            current = _validate_public_https_url(urljoin(current, location))
        except TimeoutError as exc:
            raise ValueError("Page request timed out.") from exc
    else:
        raise ValueError("Too many redirects while fetching page.")

    parser = _TextExtractor()
    parser.feed(html)
    text = parser.get_text()
    text = re.sub(r"\\s+", " ", text).strip()
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
    ids = []
    for i, fact in enumerate(facts, start=1):
        title = f"{topic} — fact {i}"
        kid = store.add_knowledge(
            title=title,
            content=fact,
            source=source,
            verified=verified,
            topic=topic,
        )
        ids.append(kid)
    summary = f"Extracted {len(facts)} candidate facts from provided text."
    sid = store.add_learning_session(
        topic=topic,
        summary=summary,
        sources_used=source,
        facts_added=len(facts),
    )
    store.log_interaction("learn_text", f"{topic}:{len(facts)}")
    return {
        "session_id": sid,
        "topic": topic,
        "facts_added": len(facts),
        "knowledge_ids": ids,
        "facts": facts,
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
