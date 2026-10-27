# Nila — Advanced Personal AI Foundation (v0.4)

Offline-first personal AI + optional semantic embeddings + optional OpenAI-compatible LLM polish.

## Core (always works)
```bash
pip install -r requirements.txt   # only needed for API (fastapi/uvicorn)
python main.py
```

## Optional embeddings
```bash
pip install -r requirements-optional.txt
export NILA_EMBEDDINGS=st
```
Default without install: hash embeddings (no extra pip).
Disable: `export NILA_EMBEDDINGS=off`

## Optional LLM (OpenAI-compatible)
```bash
export NILA_LLM_BASE_URL=https://api.openai.com/v1
export NILA_LLM_API_KEY=sk-...
export NILA_LLM_MODEL=gpt-4o-mini
```
Works with OpenAI / Groq / Ollama OpenAI mode / vLLM, etc. **Never commit keys.**

## Tamil templates
User message Tamil/Tanglish-ஆ இருந்தா reply templates automatic-ஆ shift ஆகும்.

## Daily learn reminder
Grok Automation **Nila daily learn reminder** — every day 09:00 Asia/Kolkata.

## Human-gated code tools
| Menu | Action |
|------|--------|
| 21 | Sandbox run (type YES) |
| 22–24 | Workspace proposal export / apply (CONFIRM) |

Protected: `nila/`, `tests/`, `main.py`, `api.py`.

## Safety
Not AGI. No autonomous core self-edit. LLM should stay grounded in retrieved notes.

See [README_OPTIONAL.md](./README_OPTIONAL.md).
