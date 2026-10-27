# Nila — Advanced Personal AI Foundation (v0.3)

Offline-first personal AI: memory, source learning, retrieval, evaluation, conversation context, goal planner, and a safe agent loop.

## What v0.3 adds
- **Agent chat** — answers with conversation context + knowledge-gap suggestions
- **Goals + planner** — breaks a goal into reviewable steps
- **Conversation memory** — recent turns stored in SQLite
- **Interaction logs**
- **Better tokenization** — English + Tamil unicode tokens
- **Multi-note synthesized answers**
- **Expanded API** — `/api/chat` (agent|retrieve), `/api/learn/text`, `/api/learn/url`, `/api/search`, `/api/goals`, `/api/conversation`

## Important limits
This is **not AGI/ASI** and does not train a neural language model by itself.  
It does **not** auto-edit or execute its own code. Proposals stay `pending` until you review them.

## Privacy
Repo may be public. Never commit DB files, tokens, or personal notes.  
Use `NILA_DB_PATH` and `NILA_API_TOKEN` as environment variables.

## CLI
```bash
python main.py
```

## API
```bash
export NILA_API_TOKEN='long-random-secret'
uvicorn api:app --host 0.0.0.0 --port 8000
```

## Colab
```python
!git clone https://github.com/kirushnakanthan2021-crypto/Nila.git
%cd Nila
!python main.py
!python -m unittest discover -s tests -v
```

## Safety rules
- No `exec` / `eval` of generated code
- No automatic writing of project `.py` files by the learner/agent
- Human review required for improvement proposals

## Suggested workflow
1. Learn from trusted text/URLs
2. Ask via Agent chat
3. Add evaluation questions and measure accuracy
4. Create goals when you have a project
5. Review proposals manually
