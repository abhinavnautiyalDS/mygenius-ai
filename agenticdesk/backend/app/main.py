from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator

import httpx
from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    cors_origins: str = "http://localhost:5173"
    qwen_base_url: str = "http://127.0.0.1:8001/v1"
    qwen_model: str = "qwen"
    qwen_api_key: str = ""
    granite_embedding_url: str = "http://127.0.0.1:8000"
    granite_api_key: str = ""
    agenticdesk_gateway_token: str = ""
    tavily_api_key: str = ""
    database_path: str = "./data/agenticdesk.db"
    upload_dir: str = "./data/uploads"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
app = FastAPI(title="AgenticDesk API", description="Multilingual Agentic AI Workspace", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "x-agenticdesk-token"],
)


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS conversations(id TEXT PRIMARY KEY, title TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS messages(id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS documents(id TEXT PRIMARY KEY, filename TEXT NOT NULL, content TEXT NOT NULL, chunks TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS mcp_servers(id TEXT PRIMARY KEY, name TEXT NOT NULL, url TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS approvals(id TEXT PRIMARY KEY, server_id TEXT NOT NULL, tool_name TEXT NOT NULL, arguments TEXT NOT NULL, status TEXT NOT NULL, result TEXT, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS workflow_runs(id TEXT PRIMARY KEY, task TEXT NOT NULL, status TEXT NOT NULL, result TEXT, created_at TEXT NOT NULL);
        """)
init_db()


@app.middleware("http")
async def gateway_auth(request, call_next):
    if settings.agenticdesk_gateway_token and request.url.path.startswith("/api/v1/"):
        if request.url.path not in {"/api/v1/health", "/api/v1/capabilities"}:
            supplied = request.headers.get("x-agenticdesk-token", "")
            if supplied != settings.agenticdesk_gateway_token:
                return __import__("starlette.responses").responses.JSONResponse({"detail": "Unauthorized"}, status_code=401)
    return await call_next(request)


class ChatPayload(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    conversation_id: str | None = None
    web_search: bool = False
    use_knowledge: bool = True


class ServerPayload(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    url: str = Field(min_length=8, max_length=1000)


class ToolPayload(BaseModel):
    arguments: dict[str, Any] = Field(default_factory=dict)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def qwen_chat(messages: list[dict[str, str]]) -> str:
    headers = {"Content-Type": "application/json"}
    if settings.qwen_api_key:
        headers["Authorization"] = f"Bearer {settings.qwen_api_key}"
    payload = {"model": settings.qwen_model, "messages": messages, "temperature": 0.25, "stream": False}
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(settings.qwen_base_url.rstrip("/") + "/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
