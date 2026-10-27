# Nila — Advanced Personal AI Foundation (v0.3.1)

Offline-first personal AI: memory, source learning, retrieval, evaluation, conversation context, goal planner, agent loop, and **human-gated** sandbox / workspace patches.

## Code run / edit — important

Nila does **not** autonomously auto-run or auto-edit its own engine.

What you *can* do (manual approval required):

| Menu | Action |
|------|--------|
| 21 | Paste a short pure-Python snippet → type `YES` → run in subprocess sandbox (timeout, blocked dangerous patterns) |
| 22 | Export a proposal markdown into `workspace/proposals/` |
| 23 | Write a file **only under `workspace/`** after typing `CONFIRM` |
| 24 | List exported proposal files |

Protected (cannot be written by patcher): `nila/`, `tests/`, `main.py`, `api.py`, `.github/`.

This is intentional safety: unrestricted self-modifying + self-executing agents are high risk.

## What v0.3+ includes
- Agent chat with gap suggestions
- Goals + planner
- Conversation memory + logs
- Tamil + English tokens
- Multi-note answers
- API: chat, learn, search, goals, conversation
- Gated sandbox + workspace patch tools

## Not AGI
No neural training, no autonomous self-rewrite of core code.

## Privacy
Never commit DB, tokens, or `workspace/` personal experiments if sensitive.

## CLI
```bash
python main.py
```

## API
```bash
export NILA_API_TOKEN='long-random-secret'
uvicorn api:app --host 0.0.0.0 --port 8000
```

## Tests
```bash
python -m unittest discover -s tests -v
```
