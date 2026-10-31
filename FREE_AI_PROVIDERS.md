# Nila: Groq and Gemini setup

Nila supports Groq and Google Gemini through OpenAI-compatible chat-completions endpoints. API keys are read only by the Python backend from environment variables. Never put keys in app.js, HTML, Git, or phone local storage.

## Render environment variables

In Render → nila-private-api → Environment, add one or both secrets, then save and redeploy:

- GROQ_API_KEY: create at https://console.groq.com/keys
- GEMINI_API_KEY: create at https://aistudio.google.com/app/apikey

Optional model overrides:
- GROQ_MODEL (default: openai/gpt-oss-20b)
- GEMINI_MODEL (default: gemini-3.8-flash)

Endpoints:
- Groq: https://api.groq.com/openai/v1
- Gemini: https://generativelanguage.googleapis.com/v1beta/openai

Existing NILA_LLM_PROVIDERS JSON and legacy NILA_LLM_* configuration remain supported.

## Behaviour

- Normal chat uses the first configured provider. NILA_LLM_PROVIDERS entries are processed first, then built-in Groq, then built-in Gemini, then the legacy single provider.
- The existing Council endpoint can query all configured providers in parallel and synthesize their answers.
- The /api/health endpoint returns provider names/models only; it never returns API keys.
- Free-tier quotas, model availability, and policies can change. A free key does not mean unlimited usage; check each provider's dashboard.

## Verify

1. Set provider keys as Render environment secrets and redeploy.
2. Open https://YOUR-API/api/health and check the providers list.
3. In Nila app → Settings → Python backend connection, save/test the backend URL and private token.
4. Send a chat message to test the configured LLM.

If a provider returns quota/model errors, check its current model list and quota dashboard, then set the model override.