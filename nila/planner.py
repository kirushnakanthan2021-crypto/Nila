"""Simple goal planner — breaks a goal into human-reviewable steps."""
from __future__ import annotations
import json
from .store import Store
from .engine import tokens


def plan_goal(title: str, description: str = "") -> list[dict]:
    """Heuristic plan. Not AGI planning — useful checklist generation."""
    text = f"{title} {description}".lower()
    steps: list[dict] = []

    steps.append(
        {
            "step": 1,
            "action": "clarify",
            "detail": f"Clarify success criteria for: {title}",
            "status": "pending",
        }
    )
    steps.append(
        {
            "step": 2,
            "action": "gather_knowledge",
            "detail": "Collect reliable notes/sources and run a learning session on the topic.",
            "status": "pending",
        }
    )
    steps.append(
        {
            "step": 3,
            "action": "evaluate",
            "detail": "Add 3–5 evaluation questions and measure current accuracy.",
            "status": "pending",
        }
    )

    if any(k in text for k in ("code", "python", "app", "api", "bug", "fix")):
        steps.append(
            {
                "step": 4,
                "action": "implement",
                "detail": "Implement the smallest working change; keep tests green.",
                "status": "pending",
            }
        )
        steps.append(
            {
                "step": 5,
                "action": "review_safety",
                "detail": "Review any generated patches manually; never auto-execute.",
                "status": "pending",
            }
        )
    else:
        steps.append(
            {
                "step": 4,
                "action": "synthesize",
                "detail": "Ask Nila, refine answers, and store verified conclusions.",
                "status": "pending",
            }
        )
        steps.append(
            {
                "step": 5,
                "action": "reflect",
                "detail": "Generate improvement suggestions and update the knowledge base.",
                "status": "pending",
            }
        )

    steps.append(
        {
            "step": len(steps) + 1,
            "action": "done_check",
            "detail": "Mark goal complete only after evaluation looks acceptable.",
            "status": "pending",
        }
    )
    return steps


def create_planned_goal(store: Store, title: str, description: str = "") -> dict:
    steps = plan_goal(title, description)
    plan_json = json.dumps(steps, ensure_ascii=False)
    gid = store.add_goal(title=title, description=description, plan_json=plan_json)
    store.log_interaction("goal_created", f"{gid}:{title}")
    return {"id": gid, "title": title, "description": description, "plan": steps}


def format_plan(plan: list[dict]) -> str:
    lines = []
    for s in plan:
        lines.append(f"{s['step']}. [{s['action']}] {s['detail']} ({s.get('status', 'pending')})")
    return "\n".join(lines)
