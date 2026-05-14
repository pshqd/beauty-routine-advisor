"""
Автотесты для LLMService (app/services/llm_service.py).
Покрывают: определение темы кожи, уточняющие вопросы, извлечение типа кожи,
форматирование контекста/источников, генерацию промптов, generate_response.
"""

import pytest
import re
from unittest.mock import MagicMock, patch, PropertyMock

# ── патчим тяжёлые импорты ──────────────────────────────────────────────────
import sys

# Заглушки для зависимостей, требующих ML-библиотек / FAISS-индекса
sys.modules.setdefault("langchain_community", MagicMock())
sys.modules.setdefault("langchain_community.vectorstores", MagicMock())
sys.modules.setdefault("langchain_huggingface", MagicMock())

# Пропатчим RAGService и get_provider ещё до импорта LLMService
rag_mock_cls = MagicMock()
rag_instance = MagicMock()
rag_mock_cls.return_value = rag_instance

provider_mock = MagicMock()
provider_mock.complete.return_value = "Используйте мягкий тоник."

with patch.dict(
    "sys.modules",
    {
        "services.rag_service": MagicMock(RAGService=rag_mock_cls),
        "services.providers": MagicMock(get_provider=lambda: provider_mock),
        "services.providers.base": MagicMock(),
    },
):
    from services.llm_service import LLMService, SKIN_TYPE_PATTERNS, SKIN_TYPE_MAP, SKIN_TOPIC_PATTERNS


# ── фикстура ─────────────────────────────────────────────────────────────────

@pytest.fixture
def svc():
    """Создаём LLMService с мок-зависимостями."""
    service = LLMService.__new__(LLMService)
    service._rag = rag_instance
    service._provider = provider_mock
    rag_instance.search.return_value = []
    provider_mock.complete.return_value = "Совет по уходу."
    return service


# ── _is_skin_topic ────────────────────────────────────────────────────────────

class TestIsSkinTopic:
    def test_detects_kremy(self, svc):
        assert svc._is_skin_topic("посоветуй крем для лица") is True

    def test_detects_akne(self, svc):
        assert svc._is_skin_topic("у меня акне, что делать?") is True

    def test_detects_spf(self, svc):
        assert svc._is_skin_topic("нужен SPF 50") is True

    def test_detects_uvlajnenie(self, svc):
        assert svc._is_skin_topic("нужно увлажнение кожи") is True

    def test_ignores_unrelated(self, svc):
        assert svc._is_skin_topic("расскажи про рецепт борща") is False

    def test_empty_string(self, svc):
        assert svc._is_skin_topic("") is False

    def test_case_insensitive(self, svc):
        # паттерн "кож" должен срабатывать независимо от регистра
        assert svc._is_skin_topic("КОЖА") is True


# ── _needs_clarification ──────────────────────────────────────────────────────

class TestNeedsClarification:
    def test_needs_when_no_skin_type(self, svc):
        assert svc._needs_clarification([], "посоветуй крем") is True

    def test_no_need_when_type_in_message(self, svc):
        assert svc._needs_clarification([], "у меня жирная кожа, посоветуй") is False

    def test_no_need_when_type_in_history(self, svc):
        history = [{"role": "user", "content": "у меня сухая кожа"}]
        assert svc._needs_clarification(history, "что посоветуешь?") is False

    def test_needs_when_unrelated_history(self, svc):
        history = [{"role": "assistant", "content": "привет, чем могу помочь?"}]
        assert svc._needs_clarification(history, "крем какой выбрать?") is True


# ── _extract_skin_type ────────────────────────────────────────────────────────

class TestExtractSkinType:
    @pytest.mark.parametrize("text,expected", [
        ("у меня жирная кожа", "жирная"),
        ("кожа сухая и стянутая", "сухая"),
        ("комбинированная кожа Т-зоны", "комбинированная"),
        ("у меня нормальная кожа", "нормальная"),
        ("чувствительная кожа реагирует", "чувствительная"),
        ("проблемная кожа с высыпаниями", "проблемная"),
    ])
    def test_extracts_type(self, svc, text, expected):
        assert svc._extract_skin_type([], text) == expected

    def test_returns_none_when_no_type(self, svc):
        assert svc._extract_skin_type([], "посоветуй тоник") is None

    def test_extracts_from_history(self, svc):
        history = [{"role": "user", "content": "у меня жирная кожа"}]
        result = svc._extract_skin_type(history, "что посоветуешь?")
        assert result == "жирная"


# ── _format_context ───────────────────────────────────────────────────────────

class TestFormatContext:
    def test_empty_chunks(self, svc):
        result = svc._format_context([])
        assert "не содержит" in result

    def test_formats_one_chunk(self, svc):
        chunks = [{"source": "oily.md", "section": "Очищение", "text": "Используйте гель."}]
        result = svc._format_context(chunks)
        assert "[1]" in result
        assert "oily.md" in result
        assert "Очищение" in result
        assert "Используйте гель." in result

    def test_formats_multiple_chunks(self, svc):
        chunks = [
            {"source": "a.md", "section": "", "text": "Текст 1"},
            {"source": "b.md", "section": "Раздел", "text": "Текст 2"},
        ]
        result = svc._format_context(chunks)
        assert "[1]" in result and "[2]" in result

    def test_no_section_still_works(self, svc):
        chunks = [{"source": "file.md", "section": "", "text": "Совет"}]
        result = svc._format_context(chunks)
        assert "Совет" in result


# ── _format_sources ───────────────────────────────────────────────────────────

class TestFormatSources:
    def test_deduplicates(self, svc):
        chunks = [
            {"source": "oily.md", "section": "Уход"},
            {"source": "oily.md", "section": "Уход"},
        ]
        result = svc._format_sources(chunks)
        assert len(result) == 1

    def test_unique_sources(self, svc):
        chunks = [
            {"source": "oily.md", "section": ""},
            {"source": "dry.md", "section": ""},
        ]
        assert len(svc._format_sources(chunks)) == 2

    def test_section_appended(self, svc):
        chunks = [{"source": "file.md", "section": "Очищение"}]
        result = svc._format_sources(chunks)
        assert "Очищение" in result[0]

    def test_empty_chunks(self, svc):
        assert svc._format_sources([]) == []


# ── _create_clarification_prompt ─────────────────────────────────────────────

class TestClarificationPrompt:
    def test_contains_skin_types(self, svc):
        prompt = svc._create_clarification_prompt()
        assert "жирная" in prompt
        assert "сухая" in prompt

    def test_one_question_instruction(self, svc):
        prompt = svc._create_clarification_prompt()
        assert "один" in prompt.lower() or "вопрос" in prompt.lower()

    def test_returns_string(self, svc):
        assert isinstance(svc._create_clarification_prompt(), str)


# ── _create_system_prompt ─────────────────────────────────────────────────────

class TestSystemPrompt:
    def test_contains_context(self, svc):
        prompt = svc._create_system_prompt("Текст из базы знаний")
        assert "Текст из базы знаний" in prompt

    def test_contains_structure_keywords(self, svc):
        prompt = svc._create_system_prompt("")
        # Проверяем слова, которые реально есть в актуальном промпте
        assert "задача" in prompt.lower() or "совет" in prompt.lower() or "база знаний" in prompt.lower()

    def test_returns_string(self, svc):
        assert isinstance(svc._create_system_prompt("ctx"), str)

    def test_no_html_note(self, svc):
        prompt = svc._create_system_prompt("")
        assert "HTML" in prompt  # инструкция «не используй HTML»


# ── generate_response (интеграционный) ───────────────────────────────────────

class TestGenerateResponse:
    def test_returns_required_keys(self, svc):
        rag_instance.search.return_value = []
        result = svc.generate_response("рекомендации по уходу для жирной кожи")
        assert "response" in result
        assert "sources" in result
        assert "timestamp" in result

    def test_calls_provider(self, svc):
        provider_mock.complete.reset_mock()
        rag_instance.search.return_value = []
        svc.generate_response("посоветуй крем для жирной кожи")
        provider_mock.complete.assert_called_once()

    def test_clarification_no_rag_call(self, svc):
        """Если тема кожная, но тип не указан → RAG не вызывается."""
        rag_instance.search.reset_mock()
        svc.generate_response("посоветуй крем")
        rag_instance.search.assert_not_called()

    def test_rag_called_when_skin_type_known(self, svc):
        rag_instance.search.reset_mock()
        rag_instance.search.return_value = []
        svc.generate_response("крем для жирной кожи")
        rag_instance.search.assert_called_once()

    def test_unrelated_topic_calls_rag(self, svc):
        """Нескиновая тема всё равно идёт через RAG (clarification не нужен)."""
        rag_instance.search.reset_mock()
        rag_instance.search.return_value = []
        svc.generate_response("расскажи анекдот")
        rag_instance.search.assert_called_once()

    def test_response_is_string(self, svc):
        provider_mock.complete.return_value = "Хороший ответ"
        result = svc.generate_response("уход для сухой кожи")
        assert isinstance(result["response"], str)

    def test_with_conversation_history(self, svc):
        history = [{"role": "user", "content": "у меня сухая кожа"}]
        rag_instance.search.return_value = []
        result = svc.generate_response("посоветуй крем", history)
        assert "response" in result
