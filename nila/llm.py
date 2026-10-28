"""
OpenAI-compatible LLM hook + multi-provider parallel council.

Single provider (legacy):
  NILA_LLM_BASE_URL, NILA_LLM_API_KEY, NILA_LLM_MODEL

Multi providers (preferred for council):
  NILA_LLM_PROVIDERS='[
    {"name":"groq","base_url":"https://api.groq.com/openai/v1","api_key":"gsk_...","model":"llama-3.1-8b-instant"},
    {"name":"openrouter","base_url":"https://openrouter.ai/api/v1","api_key":"sk-or-...","model":"meta-llama/llama-3.3-70b-instruct:free"},
    {"name":"gemini","base_url":"https://generativelanguage.googleapis.com/v1beta/openai/","api_key":"...","model":"gemini-2.5-flash"}
  ]'

Never commit keys. Never auto-run model-generated code.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any


def _parse_providers() -> list[dict[str, str]]:
    raw = os.environ.get("NILA_LLM_PROVIDERS", "").strip()
    providers: list[dict[str, str]] = []
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                for i, item in enumerate(data):
                    if not isinstance(item, dict):
                        continue
                    base = str(item.get("base_url") or item.get("base") or "").strip().rstrip("/")
                    key = str(item.get("api_key") or item.get("key") or "").strip()
                    model = str(item.get("model") or "").strip()
                    name = str(item.get("name") or f"p{i}").strip() or f"p{i}"
                    if base and key and model:
                        providers.append(
                            {"name": name, "base_url": base, "api_key": key, "model": model}
                        )
        except json.JSONDecodeError:
            pass

    # legacy single provider
    base = os.environ.get("NILA_LLM_BASE_URL", "").strip().rstrip("/")
    key = os.environ.get("NILA_LLM_API_KEY", "").strip()
    model = os.environ.get("NILA_LLM_MODEL", "").strip()
    if base and key and model:
        names = {p["name"] for p in providers}
        if "default" not in names and base not in {p["base_url"] for p in providers}:
            providers.insert(
                0,
                {"name": "default", "base_url": base, "api_key": key, "model": model},
            )
    return providers


def llm_configured() -> bool:
    return bool(_parse_providers())


def list_providers() -> list[dict[str, str]]:
    """Public summary without secrets."""
    out = []
    for p in _parse_providers():
        out.append(
            {
                "name": p["name"],
                "base_url": p["base_url"],
                "model": p["model"],
                "has_key": bool(p["api_key"]),
            }
        )
    return out


def chat_completion_provider(
    provider: dict[str, str],
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.3,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    timeout = float(os.environ.get("NILA_LLM_TIMEOUT", "45"))
    if max_tokens is None:
        max_tokens = int(os.environ.get("NILA_LLM_MAX_TOKENS", "512"))

    base = provider["base_url"].rstrip("/")
    model = provider["model"]
    key = provider["api_key"]
    url = f"{base}/chat/completions"
    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    data = json.dumps(body).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
        "User-Agent": "NilaLLM/0.5",
    }
    # OpenRouter likes optional identity headers
    if "openrouter.ai" in base:
        headers["HTTP-Referer"] = os.environ.get("NILA_HTTP_REFERER", "https://github.com/kirushnakanthan2021-crypto/Nila")
        headers["X-Title"] = os.environ.get("NILA_APP_TITLE", "Nila")

    req = urllib.request.Request(url, data=data, method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8", errors="replace"))
        choices = payload.get("choices") or []
        if not choices:
            return {
                "ok": False,
                "provider": provider["name"],
                "model": model,
                "error": "Empty choices",
            }
        msg = choices[0].get("message") or {}
        content = (msg.get("content") or "").strip()
        return {
            "ok": True,
            "provider": provider["name"],
            "model": model,
            "content": content,
        }
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:400]
        return {
            "ok": False,
            "provider": provider["name"],
            "model": model,
            "error": f"HTTP {exc.code}: {detail}",
        }
    except Exception as exc:
        return {
            "ok": False,
            "provider": provider["name"],
            "model": model,
            "error": str(exc),
        }


def chat_completion(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.3,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    providers = _parse_providers()
    if not providers:
        return {
            "ok": False,
            "error": "LLM not configured. Set NILA_LLM_* or NILA_LLM_PROVIDERS.",
        }
    return chat_completion_provider(
        providers[0], messages, temperature=temperature, max_tokens=max_tokens
    )


def council_parallel(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.35,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    """Call ALL configured providers in parallel (one turn, all keys work together)."""
    providers = _parse_providers()
    if not providers:
        return {"ok": False, "error": "No providers configured.", "voices": []}

    voices: list[dict[str, Any]] = []
    max_workers = min(8, max(1, len(providers)))
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futs = {
            pool.submit(
                chat_completion_provider,
                p,
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
            ): p["name"]
            for p in providers
        }
        for fut in as_completed(futs):
            try:
                voices.append(fut.result())
            except Exception as exc:
                voices.append({"ok": False, "provider": futs[fut], "error": str(exc)})

    # stable order by original provider list
    order = {p["name"]: i for i, p in enumerate(providers)}
    voices.sort(key=lambda v: order.get(v.get("provider", ""), 999))

    ok_count = sum(1 for v in voices if v.get("ok"))
    return {
        "ok": ok_count > 0,
        "provider_count": len(providers),
        "ok_count": ok_count,
        "voices": voices,
    }


def synthesize_voices(
    question: str,
    voices: list[dict[str, Any]],
    *,
    prefer_tamil: bool = False,
) -> dict[str, Any]:
    """Merge successful voices into one answer using the first healthy provider."""
    successful = [v for v in voices if v.get("ok") and v.get("content")]
    if not successful:
        return {"ok": False, "error": "No successful voices to synthesize."}

    if len(successful) == 1:
        return {
            "ok": True,
            "content": successful[0]["content"],
            "synthesizer": successful[0].get("provider"),
        }

    blocks = []
    for v in successful:
        blocks.append(
            f"### {v.get('provider')} ({v.get('model')})\n{v.get('content')}"
        )
    panel = "\n\n".join(blocks)
    lang = (
        "Write the final answer primarily in clear spoken Tamil (Tanglish OK)."
        if prefer_tamil
        else "Write the final answer in the same language mix as the question."
    )
    system = (
        "You are Nila council chair. Multiple AI advisors answered the same question. "
        "Produce ONE clear final answer: merge agreements, note important disagreements briefly, "
        "do not invent facts beyond the advisors. Keep it concise. "
        + lang
    )
    user = f"Question:\n{question}\n\nAdvisor answers:\n{panel}\n\nFinal merged answer:"

    # use first successful provider as synthesizer
    providers = _parse_providers()
    by_name = {p["name"]: p for p in providers}
    synth_provider = by_name.get(successful[0]["provider"]) or providers[0]
    result = chat_completion_provider(
        synth_provider,
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.25,
        max_tokens=int(os.environ.get("NILA_LLM_MAX_TOKENS", "700")),
    )
    if result.get("ok"):
        result["synthesizer"] = result.get("provider")
    return result


def council_discuss(
    question: str,
    *,
    context_notes: str = "",
    prefer_tamil: bool = False,
    synthesize: bool = True,
) -> dict[str, Any]:
    """All providers answer in parallel; optionally merge into one output."""
    lang = (
        "Prefer clear spoken Tamil (Tanglish OK)."
        if prefer_tamil
        else "Match the user's language mix."
    )
    system = (
        "You are one advisor in Nila multi-AI council. Give a careful, helpful answer. "
        "If context notes are provided, prefer them over invention. "
        "Do not claim to be AGI. Do not output shell commands unless asked. "
        + lang
    )
    user_parts = [f"Question:\n{question}"]
    if context_notes.strip():
        user_parts.append(f"Context notes:\n{context_notes.strip()}")
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": "\n\n".join(user_parts)},
    ]

    parallel = council_parallel(messages)
    final = None
    if synthesize and parallel.get("ok"):
        final = synthesize_voices(
            question, parallel.get("voices") or [], prefer_tamil=prefer_tamil
        )

    return {
        "ok": parallel.get("ok", False),
        "provider_count": parallel.get("provider_count", 0),
        "ok_count": parallel.get("ok_count", 0),
        "voices": parallel.get("voices") or [],
        "final": (final or {}).get("content") if final and final.get("ok") else None,
        "synthesize_error": None
        if (final and final.get("ok"))
        else (final or {}).get("error"),
        "engine": "nila-council-v0.5",
    }


def polish_with_context(
    question: str,
    retrieved_notes: str,
    *,
    prefer_tamil: bool = False,
) -> dict[str, Any]:
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
