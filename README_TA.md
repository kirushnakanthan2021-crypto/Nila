# Nila — Private Self-Learning AI Foundation

Beginner-friendly Python foundation for memory, knowledge retrieval, evaluation, and controlled improvement suggestions. No API key or third-party packages are required.

## Important limits
This is not AGI/ASI and does not train a neural language model. The first version retrieves saved notes and measures simple keyword-based tests. It does not automatically edit or execute its own code.

## Privacy warning
This repository is currently PUBLIC. Anyone may read committed code. Never commit private notes, databases, passwords, API keys, personal data, or environment files. Keep your personal database outside this repository. To make the source private, change visibility in GitHub repository Settings.

## Run on a phone using Google Colab
1. Open https://colab.research.google.com/ and create a notebook.
2. Run:

    !git clone https://github.com/kirushnakanthan2021-crypto/Nila.git
    %cd Nila
    !python main.py

3. For tests, run: !python -m unittest discover -s tests -v

## Keep memory between Colab sessions
Mount Google Drive first, then set the database path before starting Nila:

    from google.colab import drive
    drive.mount('/content/drive')
    import os
    os.environ['NILA_DB_PATH'] = '/content/drive/MyDrive/NilaData/nila.sqlite3'
    !python main.py

Create the NilaData folder if needed. The database must not be committed to GitHub.

## Features
- SQLite memory and knowledge notebook
- Keyword search and retrieval-based answers
- Evaluation cases and accuracy reports
- Mistake tracking and human-reviewed improvement suggestions
- Unit tests

Next stages can add better retrieval, source verification, and optional model adapters. Keep changes tested and reviewed; never run self-generated code automatically.
