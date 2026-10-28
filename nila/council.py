"""High-level multi-AI council for Nila (uses all configured LLM keys in parallel)."""
from __future__ import annotations

from .store import Store
from .engine import rank_items
from .tamil_templates import looks_tamil
from .llm import council_discuss, list_providers, llm_configured


def run_council(store: Store, question: str, *, synthesize: bool = True) -> dict:
    if not llm_configured():
        return {
            "ok": False,
            "error": (
                "No LLM providers configured. Set NILA_LLM_PROVIDERS JSON "
                "(or NILA_LLM_BASE_URL + KEY + MODEL)."
            ),
            "voices": [],
            "final": None,
        }

    ranked = rank_items(store, question, limit=4)
    notes = "\n".join(
        f"- {it.get('title')}: {it.get('content')}" for _, it in ranked[:4]
    )
    tamil = looks_tamil(question)
    result = council_discuss(
        question,
        context_notes=notes,
        prefer_tamil=tamil,
        synthesize=synthesize,
    )

    store.add_message("user", question)
    final_text = result.get("final") or ""
    if not final_text and result.get("voices"):
        # fallback: concatenate ok voices
        parts = []
        for v in result["voices"]:
            if v.get("ok") and v.get("content"):
                parts.append(f"[{v.get('provider')}]\n{v['content']}")
        final_text = "\n\n".join(parts) if parts else (result.get("error") or "Council failed.")
    store.add_message("assistant", final_text[:8000], meta="council")
    store.log_interaction(
        "council",
        f"ok={result.get('ok_count')}/{result.get('provider_count')} q={question[:120]}",
    )

    result["answer"] = final_text
    result["providers"] = list_providers()
    result["retrieved"] = [
        {"score": round(sc, 3), "title": it.get("title")} for sc, it in ranked[:3]
    ]
    return result


def format_council_result(result: dict) -> str:
    lines = []
    lines.append(
        f"Council: {result.get('ok_count', 0)}/{result.get('provider_count', 0)} providers OK"
    )
    for v in result.get("voices") or []:
        name = v.get("provider", "?")
        model = v.get("model", "")
        if v.get("ok"):
            lines.append(f"\n=== {name} ({model}) ===\n{v.get('content', '')}")
        else:
            lines.append(f"\n=== {name} FAILED ===\n{v.get('error', '')}")
    if result.get("final"):
        lines.append("\n=== MERGED FINAL ===\n" + result["final"])
    elif result.get("synthesize_error"):
        lines.append("\n(Merge skipped: " + str(result["synthesize_error"]) + ")")
    return "\n".join(lines)
