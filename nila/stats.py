"""Dashboard-style summary of Nila state."""
from __future__ import annotations

from .store import Store
from . import __version__


def collect_stats(store: Store) -> dict:
    evals = store.eval_summary()
    return {
        "version": __version__,
        "knowledge_items": store.knowledge_count(),
        "eval_runs": evals["total"],
        "eval_passed": evals["passed"],
        "eval_accuracy": evals["accuracy"],
        "open_goals": len(store.list_goals(status="open")),
        "pending_proposals": len(store.pending_proposals()),
        "learning_sessions": len(store.recent_learning_sessions(limit=1000)),
        "conversation_messages": len(store.recent_messages(limit=1000)),
        "db_path": store.path,
    }


def format_stats(stats: dict) -> str:
    return (
        f"Nila v{stats['version']}\n"
        f"Knowledge items : {stats['knowledge_items']}\n"
        f"Eval runs       : {stats['eval_runs']} (pass {stats['eval_passed']}, "
        f"acc {stats['eval_accuracy']:.1%})\n"
        f"Open goals      : {stats['open_goals']}\n"
        f"Pending proposals: {stats['pending_proposals']}\n"
        f"Learning sessions: {stats['learning_sessions']}\n"
        f"Chat messages   : {stats['conversation_messages']}\n"
        f"DB path         : {stats['db_path']}"
    )
