"""
Optional OpenAI-compatible chat completion hook (stdlib only).

Env (all optional — if missing, LLM is disabled):
  NILA_LLM_BASE_URL   e.g. https://api.openai.com/v1  or any compatible server
  NILA_LLM_API_KEY    bearer token
  NILA_LLM_MODEL      e.g. gpt-4o-mini, llama3.2, etc.
  NILA_LLM_TIMEOUT    seconds (default 45)
  NILA_LLM_MAX_TOKENS default 512

Never commit keys. Never auto-run model-generated code.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def llm_configured() -> bool:
    return bool(
        os.environ.get("NILA_LLM_BASE_URL", "").strip()
        and os.environ.get("NILA_LLM_API_KEY", "").strip()
        and os.environ.get("NILA_LLM_MODEL", "").strip()
    )


def chat_completion(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.3,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    if not llm_configured():
        return {"ok": False, "error": "LLM not configured (set NILA_LLM_BASE_URL, NILA_LLM_API_KEY, NILA_LLM_MODEL)."}

    base = os.environ["NILA_LLM_BASE_URL"].rstrip("/")
    model = os.environ["NILA_LLM_MODEL"].strip()
    key = os.environ["NILA_LLM_API_KEY"].strip()
    timeout = float(os.environ.get("NILA_LLM_TIMEOUT", "45"))
    if max_tokens is None:
        max_tokens = int(os.environ.get("NILA_LLM_MAX_TOKENS", "512"))

    url = f"{base}/chat/completions"
    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "User-Agent": "NilaLLM/0.4",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8", errors="replace"))
        choices = payload.get("choices") or []
        if not choices:
            return {"ok": False, "error": "Empty choices from LLM.", "raw": payload}
        msg = choices[0].get("message") or {}
        content = (msg.get("content") or "").strip()
        return {"ok": True, "content": content, "model": model, "raw": payload}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        return {"ok": False, "error": f"HTTP {exc.code}: {detail}"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def polish_with_context(
    question: str,
    retrieved_notes: str,
    *,
    prefer_tamil: bool = False,
) -> dict[str, Any]:
    """Ask the LLM to answer using only the provided notes (RAG-style)."""
    lang = (
        "Reply primarily in clear spoken Tamil (Tanglish OK) with short English terms if useful."
        if prefer_tamil
        else "Reply in the same language mix the user used (Tamil/English)."
    )
    system = (
        "You are Nila, a careful personal learning assistant. "
        "Answer ONLY using the provided notes. If notes are insufficient, say you don't know yet "
        "and suggest learning more. Do not invent facts. Do not output executable code unless asked. "
        + lang
    )
    user = (
        f"Question:\n{question}\n\n"
        f"Notes:\n{retrieved_notes}\n\n"
        f"Write a helpful answer grounded in the notes."
    )
    return chat_completion(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
    )
