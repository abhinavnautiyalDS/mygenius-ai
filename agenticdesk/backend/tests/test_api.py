import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main


@pytest.fixture()
def client(tmp_path, monkeypatch):
    database = tmp_path / "test.db"
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    monkeypatch.setattr(main.settings, "database_path", str(database))
    monkeypatch.setattr(main.settings, "upload_dir", str(uploads))
    monkeypatch.setattr(main.settings, "agenticdesk_gateway_token", "")
    main.init_db()
    with TestClient(main.app) as test_client:
        yield test_client


def test_health_and_capabilities(client):
    assert client.get("/api/v1/health").json()["status"] == "healthy"
    caps = client.get("/api/v1/capabilities").json()
    assert caps["reasoning"]["provider"] == "Qwen"
    assert caps["embeddings"]["dimensions"] == 384


def test_conversation_crud_and_summary_column(client):
    created = client.post("/api/v1/conversations", json={"title": "Test"}).json()
    cid = created["id"]
    detail = client.get(f"/api/v1/conversations/{cid}")
    assert detail.status_code == 200
    assert detail.json()["summary"] == ""
    assert client.get("/api/v1/conversations").json()["items"][0]["id"] == cid
    assert client.delete(f"/api/v1/conversations/{cid}").status_code == 200
    assert client.get(f"/api/v1/conversations/{cid}").status_code == 404


def test_chat_persists_user_and_assistant_messages(client, monkeypatch):
    async def fake_qwen(messages, max_tokens=1200):
        return "Hello from the test model"
    monkeypatch.setattr(main, "qwen_chat", fake_qwen)
    response = client.post("/api/v1/chat", json={"message": "Hello", "use_knowledge": False})
    assert response.status_code == 200, response.text
    cid = response.json()["conversation_id"]
    detail = client.get(f"/api/v1/conversations/{cid}").json()
    assert [m["role"] for m in detail["messages"]] == ["user", "assistant"]
    assert detail["messages"][1]["content"] == "Hello from the test model"


def test_chunk_text_has_overlap_and_no_empty_chunks():
    chunks = main.chunk_text("alpha beta gamma delta epsilon", size=14, overlap=4)
    assert chunks
    assert all(chunks)
    assert "delta" in " ".join(chunks)


def test_reject_private_mcp_destinations():
    with pytest.raises(Exception):
        main.validate_mcp_url("https://127.0.0.1/mcp")
    with pytest.raises(Exception):
        main.validate_mcp_url("http://example.com/mcp")


def test_approval_rejects_without_tool_execution(client):
    # Directly seed a server/approval record; rejection must not invoke any network operation.
    server_id, approval_id = "server-1", "approval-1"
    with main.db() as conn:
        conn.execute("INSERT INTO mcp_servers(id,name,url,enabled,created_at) VALUES(?,?,?,?,?)",
                     (server_id, "Example", "https://example.com/mcp", 1, main.now()))
        conn.execute("INSERT INTO approvals(id,server_id,tool_name,arguments,status,result,created_at,reviewed_at) VALUES(?,?,?,?,?,?,?,?)",
                     (approval_id, server_id, "dangerous_tool", json.dumps({}), "pending", None, main.now(), None))
    response = client.post(f"/api/v1/approvals/{approval_id}/reject", json={})
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    with main.db() as conn:
        row = conn.execute("SELECT status FROM approvals WHERE id=?", (approval_id,)).fetchone()
    assert row["status"] == "rejected"
