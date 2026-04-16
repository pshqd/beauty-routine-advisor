# app/tests/test_api.py
import pytest
from app import app as flask_app
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json["status"] == "ok"


def test_chat_missing_message(client):
    r = client.post("/api/chat", json={})
    assert r.status_code == 400


def test_chat_empty_message(client):
    r = client.post("/api/chat", json={"message": ""})
    assert r.status_code == 400


@patch("services.llm_service.LLMService.generate_response")
def test_chat_returns_response(mock_gen, client):
    mock_gen.return_value = {
        "response": "Тест",
        "sources": [],
        "timestamp": "2026-01-01T00:00:00",
    }
    r = client.post("/api/chat", json={"message": "привет"})
    assert r.status_code == 200
    assert "response" in r.json
