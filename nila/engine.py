"""Transparent offline retrieval baseline; not a neural language model."""
from __future__ import annotations
import re
from .store import Store

STOPWORDS = {"the","and","for","with","that","this","what","when","where","who","are","was","is","a","an","to","of","in","on","my","your","it","how","do","does","can","i","you","me","we","our","about","from"}


def tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-zA-Z0-9_]+", text.lower()) if len(t) > 1 and t not in STOPWORDS]


def answer_from_memory(store: Store, question: str) -> str:
    query_tokens = set(tokens(question))
    if not query_tokens:
        return "I need a few meaningful keywords. Please rephrase."
    candidates = []
    for item in store.search("", limit=1000):
        words = set(tokens(f"{item['title']} {item['content']} {item['source']}"))
        overlap = len(query_tokens & words)
        if overlap:
            score = overlap / len(query_tokens)
            candidates.append((score, item))
    if not candidates:
        return "I don't know yet. Add a reliable memory or learning fact first."
    candidates.sort(key=lambda x: x[0], reverse=True)
    score, item = candidates[0]
    if score < 0.2:
        return "I could not find a sufficiently relevant saved note."
    return f"Retrieved {item['kind']} (keyword match {score:.2f}): {item['title']}\n{item['content']}\nSource: {item['source']}"


def evaluation_passed(answer: str, expected_keywords: str) -> bool:
    options = [x.strip().lower() for x in expected_keywords.split("|") if x.strip()]
    return bool(options) and any(option in answer.lower() for option in options)


def suggest_improvements(store: Store) -> list[str]:
    summary = store.eval_summary()
    failed = store.failed_runs(limit=3)
    ideas = []
    if summary["total"] == 0:
        ideas.append("Create at least five representative evaluation cases before judging quality.")
    elif summary["accuracy"] < 0.8:
        ideas.append("Review failed tests and correct the knowledge base before rerunning evaluation.")
    if failed:
        ideas.append("Add a verified knowledge note for questions the current knowledge base cannot answer.")
    ideas.append("Keep a fixed test set and compare scores before and after every change.")
    ideas.append("Review proposed code changes manually; never execute self-generated code automatically.")
    for idea in ideas:
        store.add_idea(idea)
    return ideas
