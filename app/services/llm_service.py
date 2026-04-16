"""
Сервис для работы с LLM с интеграцией RAG и уточняющими вопросами.
Провайдер модели подключается через паттерн Strategy.
"""

import re
from datetime import datetime
from typing import Dict, List, Any, Optional

from config import Config
from services.rag_service import RAGService
from services.providers import get_provider
from services.providers.base import BaseLLMProvider
from utils.logger import setup_logger

logger = setup_logger(__name__)

SKIN_TYPE_PATTERNS = [
    r"жирн", r"сух", r"комбинир",
    r"норм(альн)?", r"чувствительн", r"проблемн",
]

SKIN_TYPE_MAP = {
    r"жирн":         "жирная",
    r"сух":          "сухая",
    r"комбинир":     "комбинированная",
    r"норм(альн)?":  "нормальная",
    r"чувствительн": "чувствительная",
    r"проблемн":     "проблемная",
}

SKIN_TOPIC_PATTERNS = [
    r"кож", r"уход", r"крем", r"сывороток", r"тонер",
    r"маск", r"очищ", r"увлажн", r"спф", r"spf",
    r"акне", r"прыщ", r"пигментац", r"ретинол", r"рутин",
]


class LLMService:
    """
    Сервис генерации ответов: RAG → промпт → LLM-провайдер.

    Провайдер (GigaChat / OpenRouter / LM Studio) задаётся через
    переменную окружения LLM_PROVIDER — без изменения кода.
    """

    def __init__(self):
        self._rag: RAGService = RAGService()
        self._provider: BaseLLMProvider = get_provider()
        logger.info(f"✅ LLMService: провайдер={Config.LLM_PROVIDER}")

    def generate_response(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        history = conversation_history or []

        if self._is_skin_topic(user_message) and self._needs_clarification(history, user_message):
            system_prompt = self._create_clarification_prompt()
            sources = []
        else:
            skin_type = self._extract_skin_type(history, user_message)
            chunks = self._rag.search(user_message, top_k=Config.TOP_K_RESULTS, skin_type=skin_type)
            system_prompt = self._create_system_prompt(self._format_context(chunks))
            sources = self._format_sources(chunks)

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        logger.info(f"🤖 Запрос к провайдеру: {Config.LLM_PROVIDER}")
        response_text = self._provider.complete(messages)
        logger.info(f"✅ Ответ: {response_text[:60]}...")

        return {
            "response":  response_text,
            "sources":   sources,
            "timestamp": datetime.now().isoformat(),
        }

    # ── приватные методы (без изменений) ──────────────────────────────

    def _is_skin_topic(self, text: str) -> bool:
        return any(re.search(p, text.lower()) for p in SKIN_TOPIC_PATTERNS)

    def _needs_clarification(self, history, user_message) -> bool:
        all_text = " ".join(m["content"] for m in history) + " " + user_message
        return not any(re.search(p, all_text.lower()) for p in SKIN_TYPE_PATTERNS)

    def _extract_skin_type(self, history, user_message) -> Optional[str]:
        all_text = (" ".join(m["content"] for m in history) + " " + user_message).lower()
        for pattern, label in SKIN_TYPE_MAP.items():
            if re.search(pattern, all_text):
                return label
        return None

    def _format_context(self, chunks: List[Dict]) -> str:
        if not chunks:
            return "База знаний не содержит релевантных данных."
        parts = []
        for i, chunk in enumerate(chunks, 1):
            header = chunk.get("source", "")
            if chunk.get("section"):
                header += f" / {chunk['section']}"
            parts.append(f"[{i}] {header}\n{chunk['text'].strip()}")
        return "\n\n".join(parts)

    def _format_sources(self, chunks: List[Dict]) -> List[str]:
        seen, sources = set(), []
        for chunk in chunks:
            key = (chunk.get("source", ""), chunk.get("section", ""))
            if key not in seen:
                seen.add(key)
                label = chunk.get("source", "")
                if chunk.get("section"):
                    label += f" > {chunk['section']}"
                sources.append(label)
        return sources

    def _create_clarification_prompt(self) -> str:
        return (
            "Ты — дружелюбный эксперт по уходу за кожей.\n\n"
            "Пользователь не указал тип кожи. Задай один короткий уточняющий вопрос.\n"
            "Типы кожи: жирная, сухая, комбинированная, нормальная, чувствительная.\n\n"
            "Один вопрос, без советов!"
        )

    def _create_system_prompt(self, context: str) -> str:
        return (
            "Ты — эксперт-дерматолог и консультант по уходу за кожей.\n\n"
            "ЗАДАЧА: Дать конкретный совет на основе базы знаний.\n\n"
            "СТРУКТУРА ОТВЕТА:\n"
            "- Пошаговая рутина (утро/вечер)\n"
            "- Рекомендуемые ингредиенты\n"
            "- Что избегать\n"
            "- Дополнительные советы\n\n"
            "СТИЛЬ: дружелюбно, конкретно, умеренные эмодзи.\n"
            "Если не уверен — советуй обратиться к дерматологу.\n\n"
            f"БАЗА ЗНАНИЙ:\n{context}\n\n"
            "Базируй ответ на этой информации!"
            "Не используй HTML. Используй списки и подзаголовки."
            "Не отвечай на вопросы, не связанные напрямую со здоровьем, красотой и моральным состоянием. Говори, что не знаешь такой информации"
        )