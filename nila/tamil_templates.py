"""Bilingual (Tamil / English / Tanglish) reply templates for Nila."""
from __future__ import annotations

import re


def looks_tamil(text: str) -> bool:
    if re.search(r"[\u0B80-\u0BFF]", text):
        return True
    # common romanized Tamil markers
    lower = text.lower()
    markers = (
        "enna", "epdi", "eppadi", "sollu", "pannu", "irukku", "illa",
        "naan", "neenga", "chellam", "vanakkam", "kathu", "theriyala",
        "romba", "konjam", "seri", "aama", "illaya",
    )
    return any(m in lower for m in markers)


def tpl_need_keywords(tamil: bool) -> str:
    if tamil:
        return "கொஞ்சம் clear-ஆ keywords போடுங்க chellam. அப்பத்தான் notes-ல தேடி சொல்ல முடியும்."
    return "I need a few meaningful keywords. Please rephrase. / கொஞ்சம் keywords வேணும்."


def tpl_unknown(tamil: bool) -> str:
    if tamil:
        return (
            "இன்னும் எனக்கு இது தெரியல chellam. "
            "Learning-ல reliable note/source add பண்ணுங்க — அப்புறம் தேடி சொல்றேன்."
        )
    return (
        "I don't know yet. Add a reliable memory or learning fact first. / "
        "இன்னும் தெரியல. முதல்ல knowledge add பண்ணுங்க."
    )


def tpl_low_relevance(tamil: bool) -> str:
    if tamil:
        return (
            "இந்தக் கேள்விக்கு match ஆகிற note பலமா இல்ல. "
            "இந்த topic-ல learn session ஓட்டுங்க (text/URL)."
        )
    return (
        "I could not find a sufficiently relevant saved note. "
        "Try learning about this topic first. / இந்த topic-ல learn பண்ணுங்க."
    )


def tpl_answer_header(score: float, tamil: bool) -> str:
    if tamil:
        return f"பதில் (retrieval score {score:.2f}):"
    return f"Answer (retrieval score {score:.2f}):"


def tpl_gap_suggestion(topic: str, tamil: bool) -> str:
    if tamil:
        return f"Knowledge gap தெரியுது. இதைப் பத்தி learn பண்ணுங்க: {topic} (menu Learn / API learn)."
    return f"Knowledge gap detected. Learn about: {topic} (menu Learn / API learn)."


def tpl_plan_hint(tamil: bool) -> str:
    if tamil:
        return "Goal/plan வேணுமா? Menu 16-ல structured plan உருவாக்கலாம்."
    return "You can create a structured goal plan with the planner (menu 16)."


def tpl_learn_hint(tamil: bool) -> str:
    if tamil:
        return "Text/URL-ல இருந்து learn பண்ணி sources-ஓட knowledge வளர்க்கலாம்."
    return "Use learning from text/URL to ground answers in sources."
