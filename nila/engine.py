"""Transparent offline retrieval + evaluation baseline. Not a neural language model."""
from __future__ import annotations
import math
import re
from .store import Store
from .embeddings import semantic_score, backend_name as embedding_backend
from .tamil_templates import (
    looks_tamil,
    tpl_need_keywords,
    tpl_unknown,
    tpl_low_relevance,
    tpl_answer_header,
)

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "what", "when", "where", "who",
    "are", "was", "is", "a", "an", "to", "of", "in", "on", "my", "your", "it",
    "how", "do", "does", "can", "i", "you", "me", "we", "our", "about", "from",
    "or", "as", "by", "at", "be", "if", "not", "but", "so", "than", "then",
    "enna", "epdi", "eppadi", "yen", "yaar", "enge", "eppo", "oru", "inda",
    "adhu", "idhu", "naan", "neenga", "unga", "ennoda",
}


def tokens(text: str) -> list[str]:
    latin = re.findall(r"[a-zA-Z0-9_]+", text.lower())
    tamil = re.findall(r"[\u0B80-\u0BFF]+", text)
    out = []
    for t in latin:
        if len(t) > 1 and t not in STOPWORDS:
            out.append(t)
    for t in tamil:
        if len(t) > 1:
            out.append(t)
    return out


def _keyword_score(query_tokens: list[str], item: dict) -> float:
    if not query_tokens:
        return 0.0
    text = (
        f"{item.get('title', '')} {item.get('content', '')} "
        f"{item.get('source', '')} {item.get('topic', '')}"
    )
    item_tokens = tokens(text)
    if not item_tokens:
        return 0.0
    qset = set(query_tokens)
    overlap = len(qset & set(item_tokens))
    if overlap == 0:
        return 0.0
    coverage = overlap / len(qset)
    tf = sum(1 for t in item_tokens if t in qset)
    score = coverage * 0.7 + (tf / (len(item_tokens) + 1)) * 0.3
    if item.get("kind") == "knowledge" and item.get("verified"):
        score *= 1.15
    return score


def rank_items(store: Store, question: str, limit: int = 8) -> list[tuple[float, dict]]:
    query_tokens = tokens(question)
    candidates: list[tuple[float, dict]] = []
    for item in store.all_items(limit=1500):
        kw = _keyword_score(query_tokens, item) if query_tokens else 0.0
        doc = f"{item.get('title', '')} {item.get('content', '')} {item.get('topic', '')}"
        sem = semantic_score(question, doc)
        # hybrid: keyword primary, semantic boost
        if kw <= 0 and sem < 0.25:
            continue
        score = kw * 0.65 + sem * 0.35
        if item.get("kind") == "knowledge" and item.get("verified"):
            score *= 1.08
        if score > 0:
            candidates.append((score, item))
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[:limit]


def answer_from_memory(store: Store, question: str, top_k: int = 3) -> str:
    tamil = looks_tamil(question)
    query_tokens = tokens(question)
    if not query_tokens and not question.strip():
        return tpl_need_keywords(tamil)

    candidates = rank_items(store, question, limit=max(top_k, 5))
    if not candidates:
        return tpl_unknown(tamil)

    best_score, best = candidates[0]
    if best_score < 0.16:
        return tpl_low_relevance(tamil)

    lines = [tpl_answer_header(best_score, tamil)]
    used = 0
    for sc, it in candidates:
        if sc < 0.12 and used > 0:
            break
        snippet = it["content"].strip()
        if len(snippet) > 350:
            snippet = snippet[:347] + "..."
        lines.append(f"• {snippet}")
        src = it.get("source") or ""
        if src:
            lines.append(f"  source: {src}" if not tamil else f"  மூலம்: {src}")
        used += 1
        if used >= top_k:
            break

    if best.get("topic"):
        lines.append(("Topic: " if not tamil else "தலைப்பு: ") + str(best["topic"]))
    lines.append(f"[embed:{embedding_backend()}]")
    return "\n".join(lines)


def answer_with_context(store: Store, question: str, history_limit: int = 6) -> str:
    history = store.recent_messages(limit=history_limit)
    context_bits = [m["content"] for m in history if m["role"] in ("user", "assistant")]
    blended = " ".join(context_bits[-4:] + [question])
    return answer_from_memory(store, blended if context_bits else question)


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
        ideas.append(
            "Review failed tests and correct / expand the knowledge base before rerunning evaluation."
        )

    if failed:
        ideas.append("Add verified knowledge notes for questions the current base cannot answer well.")
        for row in failed[:2]:
            ideas.append(f"Failed case needs knowledge: {row['question'][:80]}")

    if not store.recent_learning_sessions(limit=1):
        ideas.append("Run a learning session on a core topic so Nila has grounded sources.")

    ideas.append("Keep a fixed test set and compare scores before and after every change.")
    ideas.append(
        "Review proposed code changes manually; never execute self-generated code automatically."
    )

    for idea in ideas:
        store.add_idea(idea)
    return ideas


def propose_self_improvements(store: Store) -> list[dict]:
    proposals: list[dict] = []
    summary = store.eval_summary()
    failed = store.failed_runs(limit=3)
    knowledge_count = store.knowledge_count()

    if knowledge_count < 5:
        proposals.append(
            {
                "title": "Bootstrap core knowledge",
                "description": "Knowledge base is still thin. Run learning sessions on fundamental topics.",
                "proposed_code": "",
                "reason": f"Only ~{knowledge_count} knowledge items present.",
            }
        )

    if summary["total"] >= 3 and summary["accuracy"] < 0.75:
        proposals.append(
            {
                "title": "Improve retrieval ranking",
                "description": (
                    "Accuracy is below 75%. Add verified notes; optional sentence-transformers "
                    "via NILA_EMBEDDINGS=st can help semantic match."
                ),
                "proposed_code": "# pip install -r requirements-optional.txt\n# export NILA_EMBEDDINGS=st\n",
                "reason": f"Current accuracy {summary['accuracy']:.1%} after {summary['total']} runs.",
            }
        )

    if failed:
        proposals.append(
            {
                "title": "Add knowledge for failed evaluation cases",
                "description": "Create verified knowledge entries that answer recent failed questions.",
                "proposed_code": "",
                "reason": f"{len(failed)} recent failed runs need supporting facts.",
            }
        )

    proposals.append(
        {
            "title": "Safety gate for any future code generation",
            "description": "Never exec/eval model output; proposals stay pending until human review.",
            "proposed_code": "# Policy unchanged in v0.4\n",
            "reason": "Hard safety rule for self-learning systems.",
        }
    )

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
