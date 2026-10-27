# Nila optional features (v0.4)

## 1. Embeddings

Default uses **hash embeddings** (no install).

Better semantic search:

```bash
pip install -r requirements-optional.txt
export NILA_EMBEDDINGS=st
# optional model override:
# export NILA_ST_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

Disable: `export NILA_EMBEDDINGS=off`

## 2. OpenAI-compatible LLM

Works with OpenAI, Groq, Together, Ollama (OpenAI mode), vLLM, etc.

```bash
export NILA_LLM_BASE_URL=https://api.openai.com/v1
export NILA_LLM_API_KEY=sk-...
export NILA_LLM_MODEL=gpt-4o-mini
# optional:
# export NILA_LLM_MAX_TOKENS=512
# export NILA_LLM_AGENT=1   # set 0 to disable LLM in agent
```

Agent will RAG-polish answers using retrieved notes only. **Never put keys in the repo.**

## 3. Tamil templates

Automatic Tanglish/Tamil phrasing when the user message looks Tamil.

## 4. Learn reminders

Use Grok Automations (daily) — created separately in chat — or set your own cron reminding you to run a Nila learn session.
