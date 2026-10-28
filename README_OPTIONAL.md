# Nila optional features (v0.5)

## Multi-AI council (all keys in one turn)

Set several OpenAI-compatible providers. Nila calls **all of them in parallel**, shows each voice, then merges into one final answer.

```bash
export NILA_LLM_PROVIDERS='[
  {"name":"groq","base_url":"https://api.groq.com/openai/v1","api_key":"gsk_YOUR_KEY","model":"llama-3.1-8b-instant"},
  {"name":"openrouter","base_url":"https://openrouter.ai/api/v1","api_key":"sk-or-YOUR_KEY","model":"meta-llama/llama-3.3-70b-instruct:free"},
  {"name":"gemini","base_url":"https://generativelanguage.googleapis.com/v1beta/openai/","api_key":"YOUR_GEMINI_KEY","model":"gemini-2.5-flash"}
]'
```

CLI: menu **28**  
API: `POST /api/council` with `{"message":"...", "synthesize": true}`

**Never commit keys.** Use shell env or a local `.env` ignored by git.

### Single provider (still works)

```bash
export NILA_LLM_BASE_URL=https://api.groq.com/openai/v1
export NILA_LLM_API_KEY=gsk_...
export NILA_LLM_MODEL=llama-3.1-8b-instant
```

## Embeddings

```bash
pip install -r requirements-optional.txt
export NILA_EMBEDDINGS=st
```

Default without install: hash embeddings.

## Safety

Council discusses and answers. It does **not** auto-edit core Nila code.
