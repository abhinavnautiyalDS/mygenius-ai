from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    cors_origins: str = "http://localhost:5173"
    qwen_base_url: str = "http://127.0.0.1:8001/v1"
    qwen_model: str = "qwen"
    granite_embedding_url: str = "http://127.0.0.1:8000"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
app = FastAPI(title="AgenticDesk API", description="Multilingual Agentic AI Workspace", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.get("/")
async def root():
    return {"name": "AgenticDesk", "description": "Multilingual Agentic AI Workspace", "docs": "/docs"}

@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "service": "agenticdesk-api"}

@app.get("/api/v1/capabilities")
async def capabilities():
    return {
        "chat": {"status": "scaffold", "provider": "self-hosted-qwen"},
        "retrieval": {"status": "not_configured", "embedding_model": "IBM Granite Embedding 97M Multilingual R2"},
        "mcp": {"status": "not_configured", "approval_required": True},
        "web_search": {"status": "not_configured"},
    }

@app.post("/api/v1/chat")
async def chat(payload: dict):
    message = str(payload.get("message", "")).strip()
    if not message or len(message) > 12000:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="message must contain 1–12000 characters")
    return {
        "conversation_id": payload.get("conversation_id") or "local-demo",
        "answer": "AgenticDesk API is online. The workspace foundation is ready; live model inference will be enabled after the private Qwen endpoint is verified.",
        "status": "scaffold",
    }
