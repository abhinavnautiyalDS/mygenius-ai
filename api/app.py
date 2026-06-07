
# ==================================================
# app.py
# MyGenius AI - FastAPI Backend
# Built by Abhinav Nautiyal
# ==================================================

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form
)

from fastapi.middleware.cors import (
    CORSMiddleware
)

import tempfile
import shutil

from agents.chatbot_agent import (
    ChatbotAgent
)

from agents.finance_agent import (
    FinanceAgent
)

from agents.rag_agent import (
    RAGAgent
)

from agents.sql_agent import (
    SQLAgent
)

from agents.summarizer_agent import (
    SummarizerAgent
)

from router.routing_logic import (
    Router
)

router = Router()

# ==========================================
# FastAPI App
# ==========================================

app = FastAPI(
    title="MyGenius AI",
    version="1.0.0"
)

# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ==========================================
# Load Agents Once
# ==========================================

chatbot_agent = ChatbotAgent()

finance_agent = FinanceAgent()

rag_agent = RAGAgent()

sql_agent = SQLAgent()

summarizer_agent = SummarizerAgent()

# ==========================================
# Health Check
# ==========================================

@app.get("/")
def home():

    return {
        "message": "MyGenius AI API Running"
    }


# ==========================================
# Universal Chat Endpoint
# ==========================================

@app.post("/ask")
def ask(
    query: str = Form(...),
    session_id: str = Form("default")
):

    try:

        result = router.route(
            query=query,
            session_id=session_id
        )

        return {
            "success": True,
            "response": result
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


# ==========================================
# Upload PDF for RAG
# ==========================================

@app.post("/upload-rag")
async def upload_rag(
    file: UploadFile = File(...),
    session_id: str = Form(...)
):

    try:

        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf"
        )

        shutil.copyfileobj(
            file.file,
            temp_file
        )

        temp_file.close()

        rag_agent.load_document(
            temp_file.name,
            session_id
        )

        return {
            "success": True,
            "message": "Document loaded successfully."
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


# ==========================================
# Ask RAG
# ==========================================

@app.post("/rag")
def ask_rag(
    query: str = Form(...),
    session_id: str = Form(...)
):

    try:

        result = rag_agent.invoke(
            query,
            session_id
        )

        return result

    except Exception as e:

        return {
            "answer": str(e),
            "sources": []
        }


# ==========================================
# Summarize Document
# ==========================================

@app.post("/summarize")
async def summarize_document(
    file: UploadFile = File(...)
):

    try:

        suffix = (
            "." +
            file.filename.split(".")[-1]
        )

        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        )

        shutil.copyfileobj(
            file.file,
            temp_file
        )

        temp_file.close()

        result = summarizer_agent.invoke(
            temp_file.name
        )

        return result

    except Exception as e:

        return {
            "summary": str(e),
            "chunks": 0
        }


# ==========================================
# SQL Endpoint
# ==========================================

@app.post("/sql")
def sql_query(
    query: str = Form(...)
):

    try:

        result = sql_agent.invoke(query)

        return {
            "result": result
        }

    except Exception as e:

        return {
            "error": str(e)
        }


# ==========================================
# Finance Endpoint
# ==========================================

@app.post("/finance")
def finance_query(
    query: str = Form(...),
    session_id: str = Form("default")
):

    try:

        result = finance_agent.invoke(
            query,
            session_id
        )

        return {
            "result": result
        }

    except Exception as e:

        return {
            "error": str(e)
        }

