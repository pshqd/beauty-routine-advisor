"""
Расширенные тесты конфигурации (app/config.py).
"""

import pytest
from pathlib import Path
from config import Config, DevelopmentConfig, ProductionConfig


class TestConfigDefaults:
    def test_version_is_string(self):
        assert isinstance(Config.VERSION, str)

    def test_port_is_int(self):
        assert isinstance(Config.PORT, int)

    def test_port_is_positive(self):
        assert Config.PORT > 0

    def test_top_k_positive(self):
        assert Config.TOP_K_RESULTS > 0

    def test_temperature_in_range(self):
        t = Config.GENERATION_CONFIG["temperature"]
        assert 0.0 <= t <= 2.0

    def test_max_tokens_positive(self):
        assert Config.GENERATION_CONFIG["max_tokens"] > 0

    def test_knowledge_base_path_is_path(self):
        assert isinstance(Config.KNOWLEDGE_BASE_PATH, Path)

    def test_embeddings_db_path_is_path(self):
        assert isinstance(Config.EMBEDDINGS_DB_PATH, Path)

    def test_faiss_index_path_is_path(self):
        assert isinstance(Config.FAISS_INDEX_PATH, Path)

    def test_collection_name_alphanumeric(self):
        # FAISS/ChromaDB требует ASCII без пробелов
        import re
        assert re.match(r"^[a-zA-Z0-9_]+$", Config.COLLECTION_KB)


class TestDevelopmentConfig:
    def test_debug_is_true(self):
        assert DevelopmentConfig.DEBUG is True


class TestProductionConfig:
    def test_debug_is_false(self):
        assert ProductionConfig.DEBUG is False

    def test_log_level_is_warning_or_higher(self):
        allowed = {"WARNING", "ERROR", "CRITICAL"}
        assert ProductionConfig.LOG_LEVEL in allowed


class TestLLMProviderConfig:
    def test_valid_llm_provider(self):
        allowed = {"lm_studio", "gigachat", "openrouter"}
        # default значение должно быть одним из допустимых
        assert Config.LLM_PROVIDER in allowed

    def test_openrouter_url_starts_with_https(self):
        assert Config.OPENROUTER_URL.startswith("https://")

    def test_lm_studio_url_non_empty(self):
        assert len(Config.LM_STUDIO_URL) > 0
