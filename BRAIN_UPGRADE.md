# Nila Brain Upgrade (Phase 1)

This branch adds deterministic building blocks for a stronger personal assistant. It is not a claim of AGI or a newly trained foundation model.

## Included
- Unicode/Tanglish normalization and a small editable synonym map.
- Lexical retrieval scoring and near-duplicate fact detection.
- Extractive conversation summarization helper.
- URL validation that rejects localhost, private IP ranges, and non-HTTP schemes before web learning.
- Basic per-process API rate limiting and safer CORS defaults (wildcard origins are ignored).
- Unit tests for the new helpers.

## Important limitations
- The lexical score is a lightweight fallback, **not true BM25**. SQLite FTS5 and embedding retrieval still need integration.
- Summarization is extractive and deterministic; no LLM summary is generated.
- Rate limits are per-process and reset on restart; multi-instance deployment needs shared storage.
- SQLite on an ephemeral host is not durable. PostgreSQL/Turso migration and full phone/backend sync are not included in this phase.
- CORS must be configured to the exact deployed phone-app origin with `NILA_ALLOWED_ORIGINS` (comma-separated). Do not use `*`.
- Human approval remains required before applying proposed code changes.

## Run tests
```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

## Next phases
1. Wire FTS5 and optionally embeddings into `Store.search`.
2. Add profile, tagged note edit/delete, and spaced-repetition tables/endpoints.
3. Move persistence to managed Postgres/Turso and add migration/backup checks.
4. Sync phone conversations/notes through the backend; add markdown, voice, theme, and note search.
5. Add agent tools behind an approval queue and audit log.
