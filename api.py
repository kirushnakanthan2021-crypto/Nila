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

from nila import __version__
from nila.agent import run_agent, agent_create_goal
from nila.council import run_council
from nila.engine import answer_from_memory
from nila.learner import learn_from_text, learn_from_url
from nila.llm import list_providers, llm_configured
from nila.planner import format_plan
from nila.stats import collect_stats
from nila.store import Store

API_TOKEN = os.environ.get("NILA_API_TOKEN", "")
if not API_TOKEN:
    raise RuntimeError("Set NILA_API_TOKEN to a long random secret before starting Nila API.")

allowed_origins = [
    item.strip()
    for item in os.environ.get("NILA_ALLOWED_ORIGINS", "*").split(",")
    if item.strip()
]
app = FastAPI(title="Nila Private API", version=__version__)
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
    mode: str = Field(default="agent", description="agent | retrieve")


class CouncilRequest(BaseModel):
    message: str = Field(min_length=1, max_length=3000)
    synthesize: bool = True


class MemoryRequest(BaseModel):
    content: str = Field(min_length=1, max_length=6000)
    tags: str = Field(default="", max_length=300)


class KnowledgeRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=10000)
    source: str = Field(default="phone app note", max_length=1000)
    verified: bool = False
    topic: str = Field(default="", max_length=200)


class LearnTextRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=20, max_length=50000)
    source: str = Field(default="api text", max_length=1000)
    verified: bool = False


class LearnUrlRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=200)
    url: str = Field(min_length=8, max_length=2000)
    verified: bool = False


class GoalRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(default="", max_length=2000)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "Nila API",
        "version": __version__,
        "llm_configured": llm_configured(),
        "providers": list_providers(),
    }


@app.get("/api/stats", dependencies=[Depends(require_token)])
def stats():
    store = Store()
    try:
        return collect_stats(store)
    finally:
        store.close()


@app.post("/api/chat", dependencies=[Depends(require_token)])
def chat(payload: ChatRequest):
    store = Store()
    try:
        if payload.mode == "retrieve":
            answer = answer_from_memory(store, payload.message)
            store.add_message("user", payload.message)
            store.add_message("assistant", answer, meta="retrieve")
            return {"answer": answer, "engine": "nila-retrieval", "suggestions": []}
        result = run_agent(store, payload.message)
        return result
    finally:
        store.close()


@app.post("/api/council", dependencies=[Depends(require_token)])
def council(payload: CouncilRequest):
    store = Store()
    try:
        result = run_council(store, payload.message, synthesize=payload.synthesize)
        if not result.get("ok") and result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    finally:
        store.close()


@app.get("/api/knowledge", dependencies=[Depends(require_token)])
def list_knowledge():
    store = Store()
    try:
        return {"items": store.recent_knowledge(limit=100)}
    finally:
        store.close()


@app.post("/api/knowledge", dependencies=[Depends(require_token)])
def add_knowledge(payload: KnowledgeRequest):
    store = Store()
    try:
        item_id = store.add_knowledge(
            title=payload.title,
            content=payload.content,
            source=payload.source,
            verified=payload.verified,
            topic=payload.topic,
        )
    finally:
        store.close()
    return {"id": item_id, "saved": True}


@app.post("/api/memory", dependencies=[Depends(require_token)])
def add_memory(payload: MemoryRequest):
    store = Store()
    try:
        item_id = store.add_memory(payload.content, payload.tags)
    finally:
        store.close()
    return {"id": item_id, "saved": True}


@app.post("/api/learn/text", dependencies=[Depends(require_token)])
def learn_text(payload: LearnTextRequest):
    store = Store()
    try:
        result = learn_from_text(
            store,
            topic=payload.topic,
            text=payload.text,
            source=payload.source,
            verified=payload.verified,
        )
        return result
    finally:
        store.close()


@app.post("/api/learn/url", dependencies=[Depends(require_token)])
def learn_url(payload: LearnUrlRequest):
    store = Store()
    try:
        result = learn_from_url(
            store, topic=payload.topic, url=payload.url, verified=payload.verified
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        store.close()


@app.get("/api/search", dependencies=[Depends(require_token)])
def search(q: str = "", limit: int = 10):
    store = Store()
    try:
        return {"items": store.search(q, limit=min(limit, 50))}
    finally:
        store.close()


@app.post("/api/goals", dependencies=[Depends(require_token)])
def create_goal(payload: GoalRequest):
    store = Store()
    try:
        result = agent_create_goal(store, payload.title, payload.description)
        result["plan_text"] = format_plan(result["plan"])
        return result
    finally:
        store.close()


@app.get("/api/goals", dependencies=[Depends(require_token)])
def list_goals():
    store = Store()
    try:
        return {"goals": store.list_goals(status=None)}
    finally:
        store.close()


@app.get("/api/conversation", dependencies=[Depends(require_token)])
def conversation(limit: int = 30):
    store = Store()
    try:
        return {"messages": store.recent_messages(limit=min(limit, 100))}
    finally:
        store.close()
