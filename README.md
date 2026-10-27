# Nila

Personal self-learning AI foundation (v0.3).

Python engine: SQLite memory, source learning, retrieval agent, planner, evaluation, human-reviewed improvement proposals.  
Mobile PWA + authenticated API for phone access.

## Core (CLI)
```bash
python main.py
```

## API (for PWA)
```bash
export NILA_API_TOKEN='long-random-secret'
uvicorn api:app --host 0.0.0.0 --port 8000
```

See [README_TA.md](./README_TA.md) for full Tamil/English setup, safety rules, and workflow.

## Not AGI
Nila is an advanced personal retrieval/learning agent foundation. It does not train large neural models or autonomously rewrite itself.
