"""Transparent offline retrieval + evaluation baseline. Not a neural language model."""
from __future__ import annotations
import math
import re
from collections import Counter
from .store import Store

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "what", "when", "where", "who",
    "are", "was", "is", "a", "an", "to", "of", "in", "on", "my", "your", "it",
    "how", "do", "does", "can", "i", "you", "me", "we", "our", "about", "from",
    "or", "as", "by", "at", "be", "if", "not", "but", "so", "than", "then",
}


def tokens(text: str) -> list[str]:
    return [
        t
        for t in re.findall(r"[a-zA-Z0-9_]+", text.lower())
        if len(t) > 1 and t not in STOPWORDS
    ]


def _tf(tokens_list: list[str]) -> Counter:
    return Counter(tokens_list)


def _score_item(query_tokens: list[str], item: dict) -> float:
    """Simple TF-style overlap score with mild length normalization."""
    if not query_tokens:
        return 0.0
    text = f"{item.get('title', '')} {item.get('content', '')} {item.get('source', '')} {item.get('topic', '')}"
    item_tokens = tokens(text)
    if not item_tokens:
        return 0.0
    qset = set(query_tokens)
    iset = set(item_tokens)
    overlap = len(qset & iset)
    if overlap == 0:
        return 0.0
    # reward coverage of the query + a bit of term frequency
    coverage = overlap / len(qset)
    tf = sum(1 for t in item_tokens if t in qset)
    length_norm = 1.0 / math.sqrt(len(item_tokens) + 1)
    score = coverage * 0.7 + (tf / (len(item_tokens) + 1)) * 0.3
    # small boost for verified knowledge
    if item.get("kind") == "knowledge" and item.get("verified"):
        score *= 1.15
    return score


def answer_from_memory(store: Store, question: str, top_k: int = 3) -> str:
    query_tokens = tokens(question)
    if not query_tokens:
        return "I need a few meaningful keywords. Please rephrase."

    candidates: list[tuple[float, dict]] = []
    for item in store.all_items(limit=1500):
        score = _score_item(query_tokens, item)
        if score > 0:
            candidates.append((score, item))

    if not candidates:
        return "I don't know yet. Add a reliable memory or learning fact first."

    candidates.sort(key=lambda x: x[0], reverse=True)
    best_score, best = candidates[0]
    if best_score < 0.18:
        return "I could not find a sufficiently relevant saved note. Try learning about this topic first."

    lines = [
        f"Retrieved {best['kind']} (score {best_score:.2f}): {best['title']}",
        best["content"],
        f"Source: {best['source']}",
    ]
    if best.get("topic"):
        lines.append(f"Topic: {best['topic']}")

    # optional supporting notes
    if top_k > 1 and len(candidates) > 1:
        support = []
        for sc, it in candidates[1:top_k]:
            if sc < 0.15:
                break
            support.append(f"- [{it['kind']}] {it['title']} (score {sc:.2f})")
        if support:
            lines.append("Related notes:")
            lines.extend(support)

    return "\n".join(lines)


def evaluation_passed(answer: str, expected_keywords: str) -> bool:
    options = [x.strip().lower() for x in expected_keywords.split("|") if x.strip()]
    return bool(options) and any(option in answer.lower() for option in options)


def suggest_improvements(store: Store) -> list[str]:
    summary = store.eval_summary()
    failed = store.failed_runs(limit=5)
    ideas: list[str] = []

    if summary["total"] == 0:
        ideas.append("Create at least five representative evaluation cases before judging quality.")
    elif summary["accuracy"] < 0.8:
        ideas.append("Review failed tests and correct / expand the knowledge base before rerunning evaluation.")

    if failed:
        ideas.append("Add verified knowledge notes for questions the current base cannot answer well.")
        for row in failed[:2]:
            q = row["question"][:80]
            ideas.append(f"Failed case needs knowledge: {q}")

    sessions = store.recent_learning_sessions(limit=3)
    if not sessions:
        ideas.append("Run a learning session on a core topic so Nila has grounded sources.")

    ideas.append("Keep a fixed test set and compare scores before and after every change.")
    ideas.append("Review proposed code changes manually; never execute self-generated code automatically.")

    for idea in ideas:
        store.add_idea(idea)
    return ideas


def propose_self_improvements(store: Store) -> list[dict]:
    """
    Generate controlled, human-reviewable code / architecture proposals.
    These are stored as pending proposals — they are never applied automatically.
    """
    proposals: list[dict] = []
    summary = store.eval_summary()
    failed = store.failed_runs(limit=3)
    knowledge_count = len(store.recent_knowledge(limit=1000))

    if knowledge_count < 5:
        prop = {
            "title": "Bootstrap core knowledge",
            "description": (
                "Knowledge base is still thin. Run learning sessions on 3–5 fundamental topics "
                "(Python, SQLite, retrieval, evaluation, safety) and mark sources as verified."
            ),
            "proposed_code": "",
            "reason": f"Only ~{knowledge_count} knowledge items present.",
        }
        proposals.append(prop)

    if summary["total"] >= 3 and summary["accuracy"] < 0.75:
        prop = {
            "title": "Improve retrieval ranking",
            "description": (
                "Accuracy is below 75%. Consider stronger term weighting, synonym expansion, "
                "or storing short embeddings later. For now keep the TF-style scorer and add "
                "more verified notes for failed questions."
            ),
            "proposed_code": (
                "# Example direction (do not auto-apply):\n"
                "# - Expand STOPWORDS / add language-specific tokenizers\n"
                "# - Add simple synonym map for domain terms\n"
                "# - Weight verified knowledge higher than raw memories\n"
            ),
            "reason": f"Current accuracy {summary['accuracy']:.1%} after {summary['total']} runs.",
        }
        proposals.append(prop)

    if failed:
        prop = {
            "title": "Add knowledge for failed evaluation cases",
            "description": "Create verified knowledge entries that directly answer the recent failed questions.",
            "proposed_code": "",
            "reason": f"{len(failed)} recent failed runs need supporting facts.",
        }
        proposals.append(prop)

    # Always remind about safety
    prop = {
        "title": "Safety gate for any future code generation",
        "description": (
            "Any module that writes or patches source files must require explicit human approval "
            "and must never call exec/eval on generated code. Keep proposals in the "
            "proposed_changes table only."
        ),
        "proposed_code": (
            "# Policy (already followed in v0.2):\n"
            "# 1. Generate proposal text\n"
            "# 2. Store in proposed_changes with status='pending'\n"
            "# 3. Human reviews and applies manually if desired\n"
            "# 4. Never auto-write to .py files or run generated code\n"
        ),
        "reason": "Hard safety rule for self-learning systems.",
    }
    proposals.append(prop)

    stored = []
    for p in proposals:
        pid = store.add_proposed_change(
            title=p["title"],
            description=p["description"],
            proposed_code=p.get("proposed_code", ""),
            reason=p.get("reason", ""),
        )
        stored.append({"id": pid, **p})
    return stored
