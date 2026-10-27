# Nila

Nila is a personal AI learning project. The Python CLI engine stores knowledge in SQLite, learns from text/URL sources, evaluates retrieval quality, and produces **human-reviewed** improvement proposals. The mobile PWA is a separate first-stage prototype.

## Mobile app (PWA)

- App files: `index.html`, `app.js`, `styles.css`, `manifest.webmanifest`, and `sw.js`.
- Setup guide in Tamil: [PWA_SETUP_TA.md](./PWA_SETUP_TA.md).
- Mobile chat history is stored in the browser. The app can now connect to the authenticated Python/SQLite retrieval API when deployed.
- Backend setup: [API_SETUP_TA.md](./API_SETUP_TA.md). Render Blueprint: `render.yaml`; API: `api.py`.
- The app uses local-note retrieval when no backend is configured or the backend is unavailable. No external language model is connected.
- Never put API keys or secrets in frontend files or commit personal data.

## Python engine (v0.2)

See [README_TA.md](./README_TA.md) for the full Python engine setup, learning workflow, and safety rules.

Key capabilities:
- Offline memory + knowledge store
- Learn facts from pasted text or simple web pages
- Retrieval-based answers with improved scoring
- Evaluation harness
- Controlled self-improvement proposals (never auto-executed)

## GitHub Pages

To publish the mobile PWA, open **Settings → Pages** in this repository and set the source to **GitHub Actions**. The workflow in `.github/workflows/pages.yml` publishes the static app after a push to the default branch. Once the workflow finishes, GitHub will show the live Pages URL under Settings → Pages.
