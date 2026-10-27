"""
Lightweight agent loop for Nila.

Tools available to the agent (all local / safe):
- retrieve knowledge
- reflect on gaps
- suggest learning topics
- create a plan for a goal

This is NOT autonomous AGI. It does not execute shell commands or rewrite code.
"""
from __future__ import annotations
from .store import Store
from .engine import answer_with_context, rank_items, tokens
from .planner import create_planned_goal, format_plan


def run_agent(store: Store, user_message: str) -> dict:
    """One agent turn: log, retrieve, answer, optional suggestions."""
    store.add_message("user", user_message)
    store.log_interaction("agent_user", user_message[:500])

    ranked = rank_items(store, user_message, limit=5)
    answer = answer_with_context(store, user_message)

    suggestions: list[str] = []
    if not ranked or (ranked and ranked[0][0] < 0.22):
        # gap detected
        key = " ".join(tokens(user_message)[:6]) or user_message[:40]
        suggestions.append(
            f"Knowledge gap detected. Learn about: {key} (menu Learn / API learn)."
        )

    # lightweight intent hints
    lower = user_message.lower()
    if any(w in lower for w in ("plan", "goal", "steps", "plan pannu", "goal set")):
        suggestions.append("You can create a structured goal plan with the planner (menu 16).")
    if any(w in lower for w in ("learn", "kathu", "study", "url", "source")):
        suggestions.append("Use learning from text/URL to ground answers in sources.")

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
        "engine": "nila-agent-v0.3",
    }


def agent_create_goal(store: Store, title: str, description: str = "") -> dict:
    result = create_planned_goal(store, title, description)
    text = f"Goal #{result['id']}: {result['title']}\n" + format_plan(result["plan"])
    store.add_message("assistant", text, meta="planner")
    return result
