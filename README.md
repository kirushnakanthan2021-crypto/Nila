# Nila

Personal self-learning AI foundation (v0.3.1).

Python engine: SQLite memory, source learning, retrieval agent, planner, evaluation, human-reviewed proposals, **gated sandbox** (run approved snippets) and **workspace-only** file writes after `CONFIRM`.

Core paths (`nila/`, `main.py`, `api.py`, …) are never auto-edited.

## AI provider API keys

Nila reads provider keys from **server-side environment variables**. The keys must never be placed in browser/mobile JavaScript, committed to GitHub, or pasted into source files.

Supported providers:
- Groq: `GROQ_API_KEY` and optional `GROQ_MODEL`
- Gemini: `GEMINI_API_KEY` and optional `GEMINI_MODEL`

See [`.env.example`](./.env.example) for variable names and default model names (it contains no real secrets).

For the deployed phone app, open your backend service's hosting dashboard and add the variables under its Environment/Secrets settings, then redeploy. If you use Render, add them to the **Nila backend web service**, not the static frontend. GitHub repository secrets are only automatically available to GitHub Actions workflows; they do not automatically become Render runtime variables.

For local development, set the variables in your shell before starting the server:
```bash
export GROQ_API_KEY="your-groq-key"
export GEMINI_API_KEY="your-gemini-key"
python main.py
```
Set only the provider(s) you actually use. Never commit actual values.

## Run

```bash
python main.py
```

API:
```bash
export NILA_API_TOKEN='long-random-secret'
uvicorn api:app --host 0.0.0.0 --port 8000
```

See [README_TA.md](./README_TA.md) for safety rules and full workflow.
