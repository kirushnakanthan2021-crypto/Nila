# Nila LLM providers

Nila supports one active OpenAI-compatible provider per process. Provider credentials are read from environment variables, not from Python source files.

## Hosted providers

- Groq: set `NILA_LLM_PROVIDER=groq` and `GROQ_API_KEY`.
- OpenRouter: set `NILA_LLM_PROVIDER=openrouter` and `OPENROUTER_API_KEY`.
- Gemini AI Studio: set `NILA_LLM_PROVIDER=gemini` and `GEMINI_API_KEY`. This uses Google's OpenAI-compatible endpoint.
- Ollama: set `NILA_LLM_PROVIDER=ollama`, start Ollama on the same machine as Nila, and pull a model (the default is `llama3.2`). A key is not normally needed for a local Ollama server.

Copy `.env.example` to `.env` for local use and fill only the provider you want. The `.env` file is ignored by Git. For hosted deployments, set the variables in the hosting platform's secret/environment-variable settings. Never paste real API keys into source code or commit them.

Optional overrides: `NILA_LLM_BASE_URL`, `NILA_LLM_API_KEY`, and `NILA_LLM_MODEL`. These take precedence over provider defaults. Only one provider is active at a time; multi-provider fallback/routing is not yet implemented. Hosted APIs may incur usage charges.

## Key safety

Keys previously pasted into chat should be treated as exposed. Revoke/rotate them in the provider dashboards, then store the replacements only in local environment variables or deployment secrets.
