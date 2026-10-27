# Nila Mobile App — Setup (Tamil)

## Ippo enna ready?
- Mobile-friendly dark midnight-blue web app.
- Chat history and saved knowledge browser local storage-la save aagum.
- Learning tab-la notes add/delete pannalaam.
- Matching saved notes-ai chat-la retrieve pannalaam.
- JSON backup export/import.
- HTTPS hosting-la first open pannina piragu offline cache support.

## Phone-la use panna
1. Indha repo-oda root-la irukkura `index.html`, `app.js`, `styles.css`, `manifest.webmanifest`, `sw.js` files irukkanum.
2. GitHub repo Settings → Pages-ku po.
3. Build and deployment-la **Deploy from a branch** select pannu; branch `main`, folder `/ (root)`, Save.
4. Pages publish aana apram GitHub Pages URL-ai Android Chrome-la open pannu.
5. Chrome menu ⋮ → **Add to Home screen** / **Install app** select pannu.

## Mukkiyamaana limitation
Idhu first-stage PWA prototype. Ippo browser-la local-aa data save aagum; Python `nila/engine.py` SQLite database-oda innum connect aagala. Chat answers saved notes retrieval mattum; OpenAI/Gemini/Claude model API connect pannala. API key-ai frontend JavaScript-kulla podakoodadhu. Later secure backend (server-side secret storage + authentication) moolama Python engine-ai connect pannanum.

## Privacy
- Public repo-na source code ellaarum paarkkalaam; personal notes browser-la dhaan irukkum.
- Browser site data clear pannina local notes erase aagalaam. Backup-ai regular-aa export pannu.
- Public/shared phone-la sensitive personal data save pannaadhe.
- API keys, passwords, bank details, private personal data-ai GitHub-la commit pannaadhe.
