# Nila — Private Self-Learning AI Foundation (v0.2)

Beginner-friendly Python foundation for memory, knowledge retrieval, learning from sources, evaluation, and controlled improvement proposals. No API key or third-party packages are required (stdlib only).

## Important limits
This is not AGI/ASI and does not train a neural language model.  
Nila can:
- store memories and verified knowledge
- learn short facts from pasted text or simple web pages
- answer by retrieving the best matching notes
- run keyword evaluation tests
- propose self-improvement ideas (including code sketches)

Nila does **not** automatically edit or execute its own code. All proposals stay in the database with status `pending` until a human reviews them.

## Privacy warning
This repository is currently PUBLIC. Anyone may read committed code.  
Never commit private notes, databases, passwords, API keys, personal data, or environment files.  
Keep your personal database outside this repository (`NILA_DB_PATH` or `.local/nila.sqlite3`).  
To make the source private, change visibility in GitHub repository Settings.

## Run on a phone using Google Colab
1. Open https://colab.research.google.com/ and create a notebook.
2. Run:

```python
!git clone https://github.com/kirushnakanthan2021-crypto/Nila.git
%cd Nila
!python main.py
```

3. For tests:

```python
!python -m unittest discover -s tests -v
```

## Keep memory between Colab sessions
Mount Google Drive first, then set the database path:

```python
from google.colab import drive
drive.mount('/content/drive')
import os
os.environ['NILA_DB_PATH'] = '/content/drive/MyDrive/NilaData/nila.sqlite3'
!python main.py
```

Create the `NilaData` folder if needed. The database must not be committed to GitHub.

## Features (v0.2)
- SQLite memory + knowledge notebook (with topics)
- Improved keyword / TF-style retrieval
- Learn from pasted text
- Learn from a URL (stdlib HTML text extraction)
- Learn from multiple sources in one session
- Evaluation cases + accuracy reports
- Mistake tracking and human-reviewed improvement suggestions
- **Self-improvement proposals** stored for manual review (never auto-applied)
- Learning session history
- Unit tests

## Suggested learning workflow
1. Add a few evaluation questions (menu 9).
2. Run a learning session on a topic (menu 5 / 6 / 7) with reliable sources.
3. Ask Nila questions (menu 4).
4. Run evaluation (menu 10) and check the report (menu 11).
5. Generate proposals (menu 13) and review them yourself (menu 14).
6. Only after review, manually improve the code if you agree with a proposal.

## Safety rules built into the design
- No `exec` / `eval` of generated code
- No automatic writing of `.py` files by the learner
- Proposals are text only, status starts as `pending`
- You decide what to apply

Next stages can add better retrieval, embeddings, or optional model adapters.  
Keep changes tested and reviewed.
