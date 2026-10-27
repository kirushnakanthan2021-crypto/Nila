"""Authenticated HTTP API for connecting the Nila PWA to the Python/SQLite engine.

Run with: uvicorn api:app --host 0.0.0.0 --port 8000
Required environment variable: NILA_API_TOKEN (use a long random secret).
Do not expose this token in source code or commit it to GitHub.
"""
from __future__ import annotations

import hmac
import os
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from nila.engine import answer_from_memory
from nila.store import Store

API_TOKEN = os.environ.get("NILA_API_TOKEN", "")
if not API_TOKEN:
    raise RuntimeError("Set NILA_API_TOKEN to a long random secret before starting Nila API.")

allowed_origins = [
    item.strip()
    for item in os.environ.get("NILA_ALLOWED_ORIGINS", "*").split(",")
    if item.strip()
]
app = FastAPI(title="Nila Private API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


def require_token(authorization: Optional[str] = Header(default=None)) -> None:
    expected = f"Bearer {API_TOKEN}"
    if not authorization or not hmac.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing Nila access token")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=3000)


class MemoryRequest(BaseModel):
    content: str = Field(min_length=1, max_length=6000)
    tags: str = Field(default="", max_length=300)


class KnowledgeRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=10000)
    source: str = Field(default="phone app note", max_length=1000)
    verified: bool = False
    topic: str = Field(default="", max_length=200)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "Nila API", "version": "0.1.0"}


@app.post("/api/chat", dependencies=[Depends(require_token)])
def chat(payload: ChatRequest):
    with Store() as store:
        answer = answer_from_memory(store, payload.message)
    return {"answer": answer, "engine": "nila-retrieval-v0.1"}


@app.get("/api/knowledge", dependencies=[Depends(require_token)])
def list_knowledge():
    with Store() as store:
        return {"items": store.recent_knowledge(limit=100)}


@app.post("/api/knowledge", dependencies=[Depends(require_token)])
def add_knowledge(payload: KnowledgeRequest):
    with Store() as store:
        item_id = store.add_knowledge(
            title=payload.title,
            content=payload.content,
            source=payload.source,
            verified=payload.verified,
            topic=payload.topic,
        )
    return {"id": item_id, "saved": True}


@app.post("/api/memory", dependencies=[Depends(require_token)])
def add_memory(payload: MemoryRequest):
    with Store() as store:
        item_id = store.add_memory(payload.content, payload.tags)
    return {"id": item_id, "saved": True}
