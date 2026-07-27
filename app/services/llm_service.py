"""
LLMService — основной сервис генерации ответов.

Логика:
  1. Если тема скиновая, но тип кожи не известен → задаём уточняющий вопрос (RAG не вызываем)
  2. Если тип известен → ищём через RAG и генерируем ответ
  3. Нескиновая тема → RAG + ответ (без уточнения)
"""

import re
from datetime import datetime
from typing import Dict, List, Any, Optional

from config import Config
from utils.logger import setup_logger
from services.rag_service import RAGService
from services.providers import get_provider

logger = setup_logger(__name__)

# ===== ПАТТЕРНЫ =====

# Ключевые слова для определения скиновых тем
_SKIN_TOPIC_KEYWORDS = [
    r"кож", r"крем", r"уход", r"увлажн", r"очищ", r"тоник",
    r"серум", r"спф", r"spf", r"акне", r"прыщ", r"морщ", r"высып",
    r"пигмент", r"ретинол", r"ниацин", r"гиалурон", r"пелинг",
    r"сух", r"жир", r"комбин", r"нормаль", r"чувств",
    r"дерматол", r"косметол", r"бьют",
]
SKIN_TOPIC_PATTERNS = re.compile(
    "|".join(_SKIN_TOPIC_KEYWORDS), re.IGNORECASE
)

# Типы кожи — ключ для FAISS-фильтрации и уточнений
SKIN_TYPE_MAP = {
    "жирная":        "жирная",
    "жирной":        "жирная",
    "жирную":        "жирная",
    "сухая":          "сухая",
    "сухой":          "сухая",
    "сухую":          "сухая",
    "комбинированная": "комбинированная",
    "комбинированной": "комбинированная",
    "нормальная":     "нормальная",
    "нормальной":     "нормальная",
    "чувствительная": "чувствительная",
    "чувствительной": "чувствительная",
    "проблемная":    "проблемная",
    "проблемной":    "проблемная",
}
SKIN_TYPE_PATTERNS = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in SKIN_TYPE_MAP) + r")\b",
    re.IGNORECASE,
)


class LLMService:
    """
    Сервис генерации ответов через LLM + RAG.

    Интегрирует RAGService (поиск по FAISS-индексу) и
    провайдер LLM (GigaChat / OpenRouter / LM Studio).
    """

    def __init__(self):
        self._rag = RAGService()
        self._provider = get_provider()
        logger.info(f"LLMService: provider={type(self._provider).__name__}")

    # ================================================================ #
    # ПУБЛИЧНЫЕ МЕТОДЫ
    # ================================================================ #

    def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Генерирует ответ LLM с RAG-контекстом.

        Returns:
            {"response": str, "sources": list, "timestamp": str}
        """
        history = conversation_history or []

        # 1. Определяем: нужно ли уточнять тип кожи
        if self._is_skin_topic(user_message) and self._needs_clarification(history, user_message):
            clarification_system = self._create_clarification_prompt()
            messages = [
                {"role": "system", "content": clarification_system},
                *history,
                {"role": "user", "content": user_message},
            ]
            response_text = self._provider.complete(messages)
            return {
                "response": response_text,
                "sources": [],
                "timestamp": datetime.now().isoformat(),
            }

        # 2. Извлекаем тип кожи из истории/сообщения для FAISS-фильтра
        skin_type = self._extract_skin_type(history, user_message)

        # 3. RAG-поиск
        chunks = self._rag.search(user_message, skin_type=skin_type)
        sources = self._format_sources(chunks)
        context = self._format_context(chunks)

        # 4. Генерация
        system_prompt = self._create_system_prompt(context)
        messages = [
            {"role": "system", "content": system_prompt},
            *history,
            {"role": "user", "content": user_message},
        ]
        response_text = self._provider.complete(messages)

        logger.info(f"✓ Ответ сгенерирован, чанков: {len(chunks)}, skin_type: {skin_type}")

        return {
            "response": response_text,
            "sources": sources,
            "timestamp": datetime.now().isoformat(),
        }

    # ================================================================ #
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ================================================================ #

    def _is_skin_topic(self, message: str) -> bool:
        """
        True если сообщение относится к уходу за кожей.
        """
        return bool(SKIN_TOPIC_PATTERNS.search(message))

    def _needs_clarification(
        self,
        history: List[Dict[str, str]],
        user_message: str,
    ) -> bool:
        """
        True если тип кожи не упомянут нигде в диалоге.
        """
        all_text = " ".join(
            m.get("content", "") for m in history
        ) + " " + user_message
        return not bool(SKIN_TYPE_PATTERNS.search(all_text))

    def _extract_skin_type(
        self,
        history: List[Dict[str, str]],
        user_message: str,
    ) -> Optional[str]:
        """
        Извлекает нормализованный тип кожи из истории + текущего сообщения.
        """
        all_text = " ".join(
            m.get("content", "") for m in history
        ) + " " + user_message
        match = SKIN_TYPE_PATTERNS.search(all_text)
        if not match:
            return None
        return SKIN_TYPE_MAP.get(match.group(0).lower())

    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Форматирует чанки в нумерованный текстовый блок для промпта.
        """
        if not chunks:
            return "База знаний не содержит релевантных разделов."
        lines = []
        for i, chunk in enumerate(chunks, start=1):
            source = chunk.get("source", "")
            section = chunk.get("section", "")
            text = chunk.get("text", "")
            header = f"[{i}] {source}" + (f" — {section}" if section else "")
            lines.append(f"{header}\n{text}")
        return "\n\n".join(lines)

    def _format_sources(self, chunks: List[Dict[str, Any]]) -> List[str]:
        """
        Дедуплицирует чанки и возвращает список уникальных строк-источников.
        """
        seen: set = set()
        sources: List[str] = []
        for chunk in chunks:
            source = chunk.get("source", "")
            section = chunk.get("section", "")
            key = (source, section)
            if key in seen:
                continue
            seen.add(key)
            label = source + (f" ({section})" if section else "")
            sources.append(label)
        return sources

    def _create_clarification_prompt(self) -> str:
        """
        Системный промпт для уточнения типа кожи у пользователя.
        """
        return (
            "Ты — эксперт по уходу за кожей. "
            "Чтобы дать персонализированный совет, задай один уточняющий вопрос: "
            "какой у пользователя тип кожи? "
            "(жирная, сухая, комбинированная, нормальная, чувствительная или проблемная)."
        )

    def _create_system_prompt(self, context: str) -> str:
        """
        Системный промпт для генерации ответа на основе RAG-контекста.
        """
        return f"""Ты — дружелюбный эксперт по уходу за кожей и косметологии.

ЗАДАЧА:
- Давай персонализированные советы по уходу за кожей
- Базируйся на БАЗУ ЗНАНИЙ ниже
- Не используй HTML в ответе
- Если не уверен — советуй обратиться к дерматологу

БАЗА ЗНАНИЙ:
{context}
"""
