# Nila security and permanent storage setup

## What changed

- URL learning accepts public HTTPS destinations only, checks resolved IP addresses, rejects local/private/reserved destinations, revalidates redirects, limits redirects, response size, content types, and request time.
- API CORS no longer permits every website. Configure exact trusted origins.
- The Store can use PostgreSQL when `NILA_DATABASE_URL` is configured. SQLite remains the local-development default.
- PostgreSQL tables are created automatically at API startup. The connection string is a server-side secret and must never be added to frontend files or Git.

## Activate the existing Supabase database

This repository is configured to use your existing Supabase project when you are ready. The project currently reports as **inactive**, so it must be restored in the Supabase dashboard before the API can connect.

1. Open the Supabase dashboard and restore the existing Nila database project.
2. Open **Connect** and copy the PostgreSQL connection string. Prefer the Session Pooler URI for hosted application connections.
3. In Render, open the `nila-private-api` service → **Environment**.
4. Add `NILA_DATABASE_URL` and paste the connection string as a secret value. Do not paste it into GitHub, this README, or the phone app.
5. Set `NILA_ALLOWED_ORIGINS` to the exact origin of the deployed PWA, for example `https://your-site.netlify.app` (no path and no trailing slash). If you use more than one trusted origin, separate them with commas.
6. Save and redeploy. The API will create its tables in PostgreSQL automatically.

The PostgreSQL connection uses the server-side database credential. Never expose a Supabase `service_role` key or database password in `app.js`, HTML, or browser local storage.

## Local development

Without `NILA_DATABASE_URL`, Nila continues to use the local SQLite database at `.local/nila.sqlite3` (or `NILA_DB_PATH`). To test PostgreSQL locally, set `NILA_DATABASE_URL` in your shell environment before starting the API.

## Important data migration note

Switching from SQLite to PostgreSQL changes the active storage backend; it does not automatically copy an existing SQLite database. Export/restore any important existing data before switching. Phone-local notes are a separate browser store and are not automatically imported into the server database.

## Security settings

- Keep `NILA_API_TOKEN` private and use a long random value (at least 32 characters).
- Set `NILA_ALLOWED_ORIGINS` to exact origins only; wildcard CORS is rejected.
- Keep `NILA_DATABASE_URL` only in Render's private environment variables.
- Do not expose the API token or database credentials in public frontend code.
- The phone PWA currently keeps its API token in browser local storage. Use it only on a trusted device and keep the app updated; a browser XSS compromise could expose that token.
