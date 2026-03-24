"""
Сервис для работы с LLM (LM Studio) с интеграцией RAG и уточняющими вопросами.
"""

import re
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from config import Config
from services.rag_service import RAGService
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Паттерны для определения типа кожи в тексте
SKIN_TYPE_PATTERNS = [
    r"жирн",
    r"сух",
    r"комбинир",
    r"норм(альн)?",
    r"чувствительн",
    r"проблемн",
]

SKIN_TYPE_MAP = {
    r"жирн": "жирная",
    r"сух": "сухая",
    r"комбинир": "комбинированная",
    r"норм(альн)?": "нормальная",
    r"чувствительн": "чувствительная",
}


class LLMService:
    """
    Сервис для генерации ответов через LM Studio с RAG-контекстом.

    Два режима работы:
    - Уточняющий: если тип кожи не упомянут в истории, задаёт уточняющий вопрос.
    - Советующий: если тип кожи известен, получает контекст из RAG и даёт совет.
    """

    def __init__(self):
        """Инициализирует LM Studio подключение и RAGService."""
        self.url = Config.LM_STUDIO_URL
        self.model = Config.LM_STUDIO_MODEL
        self.generation_config = Config.GENERATION_CONFIG
        self._rag = RAGService()
        logger.info(f"✅ LLMService инициализирован: {self.url}")

    def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Генерирует ответ от LLM на основе сообщения и истории диалога.

        Args:
            user_message (str): Сообщение пользователя.
            conversation_history (list): История диалога
                [{"role": "user"|"assistant", "content": str}].

        Returns:
            dict: {
                "response": str,   — текст ответа
                "sources": list,   — источники из RAG ['файл > раздел', ...]
                "timestamp": str   — ISO-метка времени
            }

        Raises:
            ConnectionError: Если LM Studio недоступен.
            TimeoutError: Если превышен таймаут.
        """
        history = conversation_history or []

        try:
            if self._needs_clarification(history, user_message):
                system_prompt = self._create_clarification_prompt()
                sources = []
            else:
                skin_type = self._extract_skin_type(history, user_message)
                context_text, sources = self._get_rag_context(user_message, skin_type)
                system_prompt = self._create_system_prompt(context_text)

            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(history)
            messages.append({"role": "user", "content": user_message})

            logger.info("🤖 Отправка запроса в LM Studio...")
            llm_response = self._call_lm_studio(messages)
            logger.info(f"✅ Получен ответ: {llm_response[:50]}...")

            return {
                "response": llm_response,
                "sources": sources,
                "timestamp": datetime.now().isoformat(),
            }

        except requests.exceptions.ConnectionError:
            logger.error("❌ LM Studio недоступен")
            raise ConnectionError(
                "LM Studio is not running. Start Local Server on port 1234."
            )
        except requests.exceptions.Timeout:
            logger.error("⏱️ Таймаут запроса к LM Studio")
            raise TimeoutError("Request to LM Studio timed out.")
        except Exception as e:
            logger.error(f"💥 Ошибка в LLMService: {str(e)}")
            raise

    def _needs_clarification(
        self,
        history: List[Dict[str, str]],
        user_message: str,
    ) -> bool:
        """
        Проверяет, нужен ли уточняющий вопрос о типе кожи.

        Сканирует всю историю и текущее сообщение на наличие ключевых
        слов типа кожи. Возвращает True, если тип кожи ни разу не упомянут.

        Args:
            history (list): История диалога.
            user_message (str): Текущее сообщение.

        Returns:
            bool: True если нужно уточнить тип кожи.
        """
        all_text = " ".join(m["content"] for m in history) + " " + user_message
        all_text_lower = all_text.lower()
        return not any(
            re.search(pattern, all_text_lower) for pattern in SKIN_TYPE_PATTERNS
        )

    def _extract_skin_type(
        self,
        history: List[Dict[str, str]],
        user_message: str,
    ) -> Optional[str]:
        """
        Извлекает тип кожи из истории диалога и текущего сообщения.

        Args:
            history (list): История диалога.
            user_message (str): Текущее сообщение.

        Returns:
            str | None: Нормализованный тип кожи ('жирная', 'сухая' и т.д.)
                или None, если не найден.
        """
        all_text = (
            " ".join(m["content"] for m in history) + " " + user_message
        ).lower()
        for pattern, label in SKIN_TYPE_MAP.items():
            if re.search(pattern, all_text):
                return label
        return None

    def _get_rag_context(
        self,
        query: str,
        skin_type: Optional[str],
    ) -> Tuple[str, List[str]]:
        """
        Получает релевантный контекст из базы знаний через RAGService.

        Args:
            query (str): Запрос пользователя.
            skin_type (str | None): Тип кожи для фильтрации результатов.

        Returns:
            tuple: (context_text, sources)
                - context_text (str): Пронумерованные чанки для промпта
                - sources (list[str]): ['файл > раздел', ...]
        """
        chunks = self._rag.search(query, top_k=3, skin_type=skin_type)
        if not chunks:
            return "", []

        parts = []
        sources = []
        for i, chunk in enumerate(chunks, 1):
            parts.append(f"[{i}] {chunk['text']}")
            label = chunk["source"]
            if chunk["section"]:
                label += f" > {chunk['section']}"
            sources.append(label)

        return "\n\n".join(parts), sources

    def _call_lm_studio(self, messages: List[Dict[str, str]]) -> str:
        """
        Отправляет запрос в LM Studio API.

        Args:
            messages (list): Сообщения для модели.

        Returns:
            str: Текст ответа от LLM.
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.generation_config["temperature"],
            "max_tokens": self.generation_config["max_tokens"],
            "top_p": self.generation_config["top_p"],
            "stream": False,
        }
        response = requests.post(
            self.url, json=payload, timeout=self.generation_config["timeout"]
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def _create_clarification_prompt(self) -> str:
        """
        Создаёт системный промпт для режима уточняющего вопроса.

        Returns:
            str: Системный промпт с инструкцией задать один вопрос.
        """
        return """Ты — дружелюбный эксперт по уходу за кожей.

Пользователь не указал тип кожи. Твоя единственная задача сейчас —
вежливо уточнить тип кожи одним коротким вопросом.

Типы кожи: жирная, сухая, комбинированная, нормальная, чувствительная.

Один вопрос, без советов! """

    def _create_system_prompt(self, context: str) -> str:
        """
        Создаёт системный промпт с RAG-контекстом для генерации советов.

        Args:
            context (str): Пронумерованные чанки из базы знаний.

        Returns:
            str: Системный промпт.
        """
        return f"""Ты — эксперт-дерматолог и консультант по уходу за кожей.

ЗАДАЧА: Дать конкретный совет на основе базы знаний.

СТРУКТУРА ОТВЕТА:
Пошаговая рутина (утро/вечер)
Рекомендуемые ингредиенты
Что избегать
Дополнительные советы

СТИЛЬ: дружелюбно, конкретно, умеренные эмодзи.
Если не уверен — советуй обратиться к дерматологу.

БАЗА ЗНАНИЙ:
{context}

Базируй ответ на этой информации!"""
