# Nila Mobile App ↔ Python API (Tamil/Tanglish)

Indha API, phone PWA-ai Python + SQLite retrieval engine-oda connect pannum.

## Render-la backend deploy pannuradhu
1. Render.com-la login pannunga; New → Blueprint select pannunga.
2. GitHub repository `kirushnakanthan2021-crypto/Nila` connect pannunga; `render.yaml` blueprint review pannunga.
3. Deploy mudinja service URL-ai copy pannunga (example format: `https://your-service.onrender.com`).
4. Render service → Environment-la `NILA_API_TOKEN` generate aagirukkum. Adhai secret-aa vechukkonga. Chat-la / GitHub-la paste panna vendam.
5. Free service sleep aagalam; request-ku response varathukku sila neram aagalam. SQLite file free ephemeral server restart/redeploy-la reset aagalam; persistent disk/DB configure pannama important private data store pannadheenga.

## Phone app connect
1. GitHub Pages-la Nila PWA deploy pannunga (Repo → Settings → Pages → Source: GitHub Actions).
2. Nila app open → Settings → **Python backend connection**.
3. Render URL + Render environment-la irukkura `NILA_API_TOKEN` enter panni Save & test press pannunga.
4. Connection status Connected nu vandha, Chat tab-la question kelunga. Learning tab-la pudhu note save pannunga; note server-side SQLite-kkum save aagum.
5. Token browser local storage-la save aagum. Un phone-ai vera yaarum use pannina, token share aagalaam; shared phone-la set panna vendam.

## API security
- API endpoints bearer token require pannum; health check mattum public.
- Frontend source-la token hardcode panna vendam.
- `NILA_ALLOWED_ORIGINS`-ai public PWA exact URL-ku restrict pannalaam (example: `https://OWNER.github.io`). Default `*` CORS allow pannum, aana token innum required.
- API HTTPS URL use pannunga.
- Idhu retrieval engine mattum; LLM / OpenAI / Gemini / Claude innum connect aagala.
- API endpoint: `GET /api/health`, `POST /api/chat`, `POST /api/knowledge`, `GET /api/knowledge`, `POST /api/memory`.
