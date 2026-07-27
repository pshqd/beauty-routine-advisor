"""
Shared pytest fixtures для всех тестов проекта.
Автоматически подхватывается pytest без import.
"""

import sys
import os
import pytest
from unittest.mock import MagicMock

# Добавляем app/ в sys.path для всех тестов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Мокаем тяжёлые ML-зависимости до любого импорта
sys.modules.setdefault("langchain_community", MagicMock())
sys.modules.setdefault("langchain_community.vectorstores", MagicMock())
sys.modules.setdefault("langchain_huggingface", MagicMock())
sys.modules.setdefault("sentence_transformers", MagicMock())
faiss_mock = MagicMock()
faiss_mock.IndexFlatL2 = MagicMock()
sys.modules.setdefault("faiss", faiss_mock)


# ------------------------------------------------------------------ #
# Flask test client
# ------------------------------------------------------------------ #

@pytest.fixture(scope="session")
def flask_app():
    """Flask-приложение в тестовом режиме."""
    from unittest.mock import patch, MagicMock
    with patch("services.llm_service.LLMService") as mock_llm:
        mock_llm.return_value.generate_response.return_value = {
            "response": "Тестовый ответ",
            "sources": [],
            "timestamp": "2026-01-01T00:00:00",
        }
        from app import app as flask_application
        flask_application.config["TESTING"] = True
        flask_application.config["DEBUG"] = False
        yield flask_application


@pytest.fixture()
def client(flask_app):
    """HTTP-клиент для тестов."""
    with flask_app.test_client() as c:
        yield c


# ------------------------------------------------------------------ #
# MetricsCollector fixture
# ------------------------------------------------------------------ #

@pytest.fixture()
def fresh_metrics():
    """Чистый MetricsCollector для каждого теста."""
    from utils.metrics import MetricsCollector
    return MetricsCollector()
