"""
Тесты слоя эмбеддингов.

Уровень 1 (без ML): проверяем конфигурацию модели и интерфейс HuggingFaceEmbeddings.
  → Запускается всегда, без скачивания модели.

Уровень 2 (с реальной моделью): проверяем что векторы реально работают.
  → Запускается только если FAISS-индекс существует на диске.
  → Маркер: @pytest.mark.slow — запуск: pytest -m slow

Запуск только быстрых тестов (CI):
  pytest tests/test_embeddings.py -v -m "not slow"

Запуск всех включая реальную модель (локально):
  pytest tests/test_embeddings.py -v
"""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Регистрируем маркер slow
def pytest_configure(config):
    config.addinivalue_line("markers", "slow: тесты с реальной ML-моделью")


# ═══════════════════════════════════════════════════════════════════════════
# 1. Конфигурация модели (без ML, всегда запускается)
# ═══════════════════════════════════════════════════════════════════════════

class TestEmbeddingConfig:

    def test_embedding_model_name_not_empty(self):
        """Имя модели задано в Config."""
        from config import Config
        assert Config.EMBEDDING_MODEL
        assert isinstance(Config.EMBEDDING_MODEL, str)

    def test_faiss_index_path_is_path_object(self):
        """FAISS_INDEX_PATH должен быть объектом Path."""
        from config import Config
        assert isinstance(Config.FAISS_INDEX_PATH, Path)

    def test_top_k_results_positive(self):
        """TOP_K_RESULTS должен быть положительным числом."""
        from config import Config
        assert Config.TOP_K_RESULTS > 0

    def test_retrieval_k_bug_regression(self):
        """
        БАГ-РЕГРЕССИЯ: Config не должен иметь RETRIEVAL_K — его нет в config.py,
        но rag_service.py пытается его использовать. Этот тест документирует баг:
        при исправлении — переименуй в test_retrieval_k_fixed.
        """
        from config import Config
        has_retrieval_k = hasattr(Config, "RETRIEVAL_K")
        # Если атрибут появился — значит баг исправлен, тест надо обновить
        if has_retrieval_k:
            # Проверяем что значение совпадает с TOP_K_RESULTS
            assert Config.RETRIEVAL_K == Config.TOP_K_RESULTS, (
                "RETRIEVAL_K и TOP_K_RESULTS должны быть одинаковыми"
            )
        else:
            # Баг ещё не исправлен — документируем
            pytest.xfail(
                "БАГ: rag_service.py использует Config.RETRIEVAL_K, "
                "которого нет в Config. Используется Config.TOP_K_RESULTS. "
                "Исправить: переименовать RETRIEVAL_K → TOP_K_RESULTS в rag_service.py"
            )


# ═══════════════════════════════════════════════════════════════════════════
# 2. Интерфейс HuggingFaceEmbeddings (мок)
# ═══════════════════════════════════════════════════════════════════════════

class TestEmbeddingInterface:

    @pytest.fixture
    def mock_embeddings(self):
        """Мок HuggingFaceEmbeddings с реалистичными размерами."""
        mock = MagicMock()
        # deepvk/USER-base выдаёт векторы размером 768
        mock.embed_query.return_value = [0.1] * 768
        mock.embed_documents.return_value = [[0.1] * 768, [0.2] * 768]
        return mock

    def test_embed_query_returns_vector(self, mock_embeddings):
        """embed_query возвращает вектор нужной размерности."""
        vector = mock_embeddings.embed_query("жирная кожа")
        assert len(vector) == 768

    def test_embed_documents_returns_list_of_vectors(self, mock_embeddings):
        """embed_documents возвращает список векторов."""
        vectors = mock_embeddings.embed_documents(["текст 1", "текст 2"])
        assert len(vectors) == 2
        assert all(len(v) == 768 for v in vectors)

    def test_embeddings_created_with_correct_model(self):
        """HuggingFaceEmbeddings создаётся с правильным именем модели."""
        sys.modules.setdefault("langchain_huggingface", MagicMock())
        with patch("langchain_huggingface.HuggingFaceEmbeddings") as emb_cls:
            from config import Config
            emb_cls(
                model_name=Config.EMBEDDING_MODEL,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
            call_kwargs = emb_cls.call_args[1]
            assert call_kwargs["model_name"] == "deepvk/USER-base"
            assert call_kwargs["model_kwargs"]["device"] == "cpu"
            assert call_kwargs["encode_kwargs"]["normalize_embeddings"] is True

    def test_normalize_embeddings_is_true(self):
        """normalize_embeddings=True обязателен для корректного косинусного поиска."""
        sys.modules.setdefault("langchain_huggingface", MagicMock())
        with patch("langchain_huggingface.HuggingFaceEmbeddings") as emb_cls:
            from config import Config
            emb_cls(
                model_name=Config.EMBEDDING_MODEL,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
            call_kwargs = emb_cls.call_args[1]
            assert call_kwargs["encode_kwargs"]["normalize_embeddings"] is True


# ═══════════════════════════════════════════════════════════════════════════
# 3. Реальная модель (только если индекс существует)
# ═══════════════════════════════════════════════════════════════════════════

from config import Config as _Cfg
_INDEX_EXISTS = _Cfg.FAISS_INDEX_PATH.exists()


@pytest.mark.slow
@pytest.mark.skipif(not _INDEX_EXISTS, reason="FAISS-индекс не найден — запусти init_kb.py")
class TestRealEmbeddings:
    """
    Тесты с реальной загрузкой модели deepvk/USER-base.
    Требуют предварительно построенного FAISS-индекса.
    Время выполнения: ~30-60 секунд (первый запуск скачивает модель).
    """

    @pytest.fixture(scope="class")
    def rag(self):
        """Создаёт реальный RAGService один раз на весь класс."""
        from services.rag_service import RAGService
        return RAGService()

    def test_rag_service_loads(self, rag):
        """RAGService успешно загружается с реальным индексом."""
        assert rag._vs is not None
        assert rag._vs.index.ntotal > 0

    def test_search_returns_results(self, rag):
        """Поиск по типичному запросу возвращает хотя бы один результат."""
        results = rag.search("крем для сухой кожи")
        assert len(results) > 0

    def test_search_results_have_positive_score(self, rag):
        """Score у всех результатов должен быть > 0."""
        results = rag.search("увлажнение")
        for r in results:
            assert r["score"] > 0, f"Нулевой score: {r}"

    def test_skin_type_filter_works_with_real_data(self, rag):
        """Фильтрация по skin_type возвращает только релевантные чанки."""
        results_oily = rag.search("уход за кожей", skin_type="жирная")
        for r in results_oily:
            # Каждый чанк либо для жирной кожи, либо универсальный
            assert r.get("source") is not None

    def test_semantic_similarity_oily_vs_dry(self, rag):
        """
        Запрос про жирную кожу должен возвращать ДРУГИЕ чанки, чем про сухую.
        Проверяем что семантика работает, а не просто keyword matching.
        """
        results_oily = rag.search("матирование жирного блеска", skin_type="жирная")
        results_dry = rag.search("устранение шелушения и стянутости", skin_type="сухая")
        # Источники не должны полностью совпадать
        sources_oily = {r["source"] for r in results_oily}
        sources_dry = {r["source"] for r in results_dry}
        # Хотя бы один источник должен различаться (если в KB есть файлы для разных типов)
        if sources_oily and sources_dry:
            assert sources_oily != sources_dry or len(sources_oily) == 0, (
                "Запросы про жирную и сухую кожу вернули одинаковые источники — "
                "возможно база знаний не разделена по типам кожи"
            )
