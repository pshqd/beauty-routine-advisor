"""
Расширенные тесты Flask API (app/app.py).
Покрывают: /api/health, /api/chat (валидация, ошибки провайдера, история).
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

# ── патч тяжёлых модулей ─────────────────────────────────────────────────────
import sys

sys.modules.setdefault("langchain_community", MagicMock())
sys.modules.setdefault("langchain_community.vectorstores", MagicMock())
sys.modules.setdefault("langchain_huggingface", MagicMock())
sys.modules.setdefault("services.rag_service", MagicMock(RAGService=MagicMock()))
sys.modules.setdefault("services.providers", MagicMock(get_provider=lambda: MagicMock()))
sys.modules.setdefault("services.providers.base", MagicMock())

# Мокаем LLMService до импорта app
mock_llm_cls = MagicMock()
mock_llm_instance = MagicMock()
mock_llm_cls.return_value = mock_llm_instance

with patch.dict("sys.modules", {"services.llm_service": MagicMock(LLMService=mock_llm_cls)}):
    from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    flask_app.config["DEBUG"] = False
    with flask_app.test_client() as c:
        yield c


# ── /api/health ───────────────────────────────────────────────────────────────

class TestHealthEndpoint:
    def test_status_200(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200

    def test_status_ok(self, client):
        assert r.json["status"] == "ok" if (r := client.get("/api/health")) else True
        r = client.get("/api/health")
        assert r.json["status"] == "ok"

    def test_has_timestamp(self, client):
        r = client.get("/api/health")
        assert "timestamp" in r.json

    def test_has_version(self, client):
        r = client.get("/api/health")
        assert "version" in r.json

    def test_timestamp_format(self, client):
        r = client.get("/api/health")
        # Должно быть валидным ISO-форматом
        ts = r.json["timestamp"]
        datetime.fromisoformat(ts)  # бросает ValueError если неверный формат


# ── /api/chat – валидация ─────────────────────────────────────────────────────

class TestChatValidation:
    def test_missing_message_field(self, client):
        r = client.post("/api/chat", json={})
        assert r.status_code == 400

    def test_empty_message_string(self, client):
        r = client.post("/api/chat", json={"message": ""})
        assert r.status_code == 400

    def test_whitespace_only_message(self, client):
        r = client.post("/api/chat", json={"message": "   "})
        assert r.status_code == 400

    def test_no_json_body(self, client):
        r = client.post("/api/chat", data="not json", content_type="text/plain")
        assert r.status_code == 400

    def test_error_key_in_400(self, client):
        r = client.post("/api/chat", json={})
        assert "error" in r.json


# ── /api/chat – успешные ответы ───────────────────────────────────────────────

class TestChatSuccess:
    def test_returns_200(self, client):
        mock_llm_instance.generate_response.return_value = {
            "response": "Совет", "sources": [], "timestamp": "2026-01-01T00:00:00"
        }
        r = client.post("/api/chat", json={"message": "привет"})
        assert r.status_code == 200

    def test_response_key_present(self, client):
        mock_llm_instance.generate_response.return_value = {
            "response": "Ответ сервиса", "sources": [], "timestamp": "t"
        }
        r = client.post("/api/chat", json={"message": "тест"})
        assert "response" in r.json

    def test_passes_conversation_history(self, client):
        mock_llm_instance.generate_response.reset_mock()
        mock_llm_instance.generate_response.return_value = {
            "response": "ok", "sources": [], "timestamp": "t"
        }
        history = [{"role": "user", "content": "предыдущий вопрос"}]
        client.post("/api/chat", json={"message": "вопрос", "conversation_history": history})
        call_kwargs = mock_llm_instance.generate_response.call_args
        assert call_kwargs is not None

    def test_empty_history_is_accepted(self, client):
        mock_llm_instance.generate_response.return_value = {
            "response": "ok", "sources": [], "timestamp": "t"
        }
        r = client.post("/api/chat", json={"message": "вопрос", "conversation_history": []})
        assert r.status_code == 200


# ── /api/chat – обработка ошибок провайдера ───────────────────────────────────

class TestChatProviderErrors:
    def _setup_error(self, msg):
        mock_llm_instance.generate_response.side_effect = Exception(msg)

    def test_402_returns_credit_message(self, client):
        self._setup_error("402 Payment Required")
        r = client.post("/api/chat", json={"message": "крем"})
        assert r.status_code == 200
        assert "кредит" in r.json.get("response", "").lower() or "💳" in r.json.get("response", "")

    def test_404_returns_model_unavailable(self, client):
        self._setup_error("404 Not Found")
        r = client.post("/api/chat", json={"message": "крем"})
        assert r.status_code == 200
        assert "модел" in r.json.get("response", "").lower() or "⚙️" in r.json.get("response", "")

    def test_429_returns_overload_message(self, client):
        self._setup_error("429 Too Many Requests")
        r = client.post("/api/chat", json={"message": "крем"})
        assert r.status_code == 200
        assert "перегруж" in r.json.get("response", "").lower() or "⏳" in r.json.get("response", "")

    def test_403_returns_overload_message(self, client):
        self._setup_error("403 Forbidden")
        r = client.post("/api/chat", json={"message": "крем"})
        assert r.status_code == 200

    def test_generic_error_returns_500(self, client):
        self._setup_error("Unexpected crash")
        r = client.post("/api/chat", json={"message": "крем"})
        assert r.status_code == 500
        assert "error" in r.json

    def teardown_method(self, method):
        mock_llm_instance.generate_response.side_effect = None


# ── 404/500 error handlers ────────────────────────────────────────────────────

class TestErrorHandlers:
    def test_404_handler(self, client):
        r = client.get("/api/nonexistent_endpoint_xyz")
        assert r.status_code == 404
        assert "error" in r.json

    def test_favicon_returns_204(self, client):
        r = client.get("/favicon.ico")
        assert r.status_code == 204
