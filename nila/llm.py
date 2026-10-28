"""
Optional multi-provider chat-completion hook (stdlib only).

Set NILA_LLM_PROVIDER to groq, openrouter, gemini, ollama, or custom.
Secrets are read from environment variables; never put keys in source control.
Generic NILA_LLM_BASE_URL / NILA_LLM_API_KEY / NILA_LLM_MODEL override provider defaults.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

_PROVIDER_DEFAULTS = {
    "groq": {
        "base": "https://api.groq.com/openai/v1",
        "key_env": "GROQ_API_KEY",
        "model": "openai/gpt-oss-20b",
    },
    "openrouter": {
        "base": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
        "model": "openai/gpt-oss-20b",
    },
    "gemini": {
        "base": "https://generativelanguage.googleapis.com/v1beta/openai",
        "key_env": "GEMINI_API_KEY",
        "model": "gemini-2.5-flash",
    },
    "ollama": {
        "base": "http://localhost:11434/v1",
        "key_env": "",
        "model": "llama3.2",
    },
}


def _config() -> tuple[str, str, str]:
    provider = os.environ.get("NILA_LLM_PROVIDER", "groq").strip().lower()
    if provider not in {*_PROVIDER_DEFAULTS, "custom"}:
        raise ValueError("NILA_LLM_PROVIDER must be groq, openrouter, gemini, ollama, or custom.")
    defaults = _PROVIDER_DEFAULTS.get(provider, {})
    base = os.environ.get("NILA_LLM_BASE_URL", defaults.get("base", "")).strip().rstrip("/")
    key_env = defaults.get("key_env", "")
    key = os.environ.get("NILA_LLM_API_KEY", "").strip()
    if not key and key_env:
        key = os.environ.get(key_env, "").strip()
    model = os.environ.get("NILA_LLM_MODEL", defaults.get("model", "")).strip()
    return base, key, model


def llm_configured() -> bool:
    try:
        base, key, model = _config()
    except ValueError:
        return False
    provider = os.environ.get("NILA_LLM_PROVIDER", "groq").strip().lower()
    # Ollama commonly runs without authentication; other providers require a key.
    return bool(base and model and (key or provider == "ollama"))


def chat_completion(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.3,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    try:
        base, key, model = _config()
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    provider = os.environ.get("NILA_LLM_PROVIDER", "groq").strip().lower()
    if not base or not model or (not key and provider != "ollama"):
        return {
            "ok": False,
            "error": "LLM not configured. Set NILA_LLM_PROVIDER and its provider key in environment secrets.",
        }

    timeout = float(os.environ.get("NILA_LLM_TIMEOUT", "45"))
    if max_tokens is None:
        max_tokens = int(os.environ.get("NILA_LLM_MAX_TOKENS", "512"))

    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {key}"} if key else {}),
            "User-Agent": "NilaLLM/0.5",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8", errors="replace"))
        choices = payload.get("choices") or []
        if not choices:
            return {"ok": False, "error": "Empty choices from LLM."}
        msg = choices[0].get("message") or {}
        content = (msg.get("content") or "").strip()
        return {"ok": True, "content": content, "model": model}
    except urllib.error.HTTPError as exc:
        # Do not return provider response bodies: they can contain sensitive request metadata.
        return {"ok": False, "error": f"LLM provider returned HTTP {exc.code}."}
    except Exception as exc:
        return {"ok": False, "error": f"LLM request failed: {type(exc).__name__}."}


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
        f"Question:\\n{question}\\n\\n"
        f"Notes:\\n{retrieved_notes}\\n\\n"
        "Write a helpful answer grounded in the notes."
    )
    return chat_completion(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
    )
