"""
Lightweight agent loop for Nila.

Optional LLM polish when NILA_LLM_* env vars are set.
Still does not execute shell or rewrite core code.
"""
from __future__ import annotations
import os
from .store import Store
from .engine import answer_with_context, rank_items, tokens
from .planner import create_planned_goal, format_plan
from .tamil_templates import (
    looks_tamil,
    tpl_gap_suggestion,
    tpl_plan_hint,
    tpl_learn_hint,
)
from .llm import llm_configured, polish_with_context
from .embeddings import backend_name as embedding_backend


def run_agent(store: Store, user_message: str) -> dict:
    store.add_message("user", user_message)
    store.log_interaction("agent_user", user_message[:500])

    tamil = looks_tamil(user_message)
    ranked = rank_items(store, user_message, limit=5)
    base_answer = answer_with_context(store, user_message)

    notes_blob = "\n".join(
        f"- {it.get('title')}: {it.get('content')}" for _, it in ranked[:4]
    )
    answer = base_answer
    engine = f"nila-agent-v0.4+embed:{embedding_backend()}"
    llm_meta = None

    use_llm = llm_configured() and os.environ.get("NILA_LLM_AGENT", "1").strip() not in {
        "0",
        "off",
        "false",
    }
    if use_llm:
        context = notes_blob or 'No matching saved notes yet.'
        polished = polish_with_context(
            user_message, context, prefer_tamil=tamil
        )
        if polished.get("ok") and polished.get("content"):
            answer = polished["content"]
            engine = f"nila-agent-v0.4+llm+embed:{embedding_backend()}"
            llm_meta = {"provider": polished.get("provider"), "model": polished.get("model")}
        else:
            llm_meta = {"error": polished.get("error")}

    suggestions: list[str] = []
    if not ranked or (ranked and ranked[0][0] < 0.22):
        key = " ".join(tokens(user_message)[:6]) or user_message[:40]
        suggestions.append(tpl_gap_suggestion(key, tamil))

    lower = user_message.lower()
    if any(w in lower for w in ("plan", "goal", "steps", "plan pannu", "goal set")):
        suggestions.append(tpl_plan_hint(tamil))
    if any(w in lower for w in ("learn", "kathu", "study", "url", "source", "கத்து")):
        suggestions.append(tpl_learn_hint(tamil))

    store.add_message("assistant", answer, meta="agent")
    store.log_interaction("agent_answer", answer[:500])

    return {
        "answer": answer,
        "retrieved": [
            {
                "score": round(sc, 3),
                "title": it.get("title"),
                "kind": it.get("kind"),
                "source": it.get("source"),
            }
            for sc, it in ranked[:3]
        ],
        "suggestions": suggestions,
        "engine": engine,
        "llm": llm_meta,
    }


def agent_create_goal(store: Store, title: str, description: str = "") -> dict:
    result = create_planned_goal(store, title, description)
    text = f"Goal #{result['id']}: {result['title']}\n" + format_plan(result["plan"])
    store.add_message("assistant", text, meta="planner")
    return result
