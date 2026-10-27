# Nila

Personal self-learning AI foundation (v0.3.1).

Python engine: SQLite memory, source learning, retrieval agent, planner, evaluation, human-reviewed proposals, **gated sandbox** (run approved snippets) and **workspace-only** file writes after `CONFIRM`.

Core paths (`nila/`, `main.py`, `api.py`, …) are never auto-edited.

```bash
python main.py
```

API:
```bash
export NILA_API_TOKEN='long-random-secret'
uvicorn api:app --host 0.0.0.0 --port 8000
```

See [README_TA.md](./README_TA.md) for safety rules and full workflow.
