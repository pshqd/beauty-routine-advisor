"""Провайдер GigaChat (Сбер) через langchain-gigachat."""

from typing import Dict, List

from langchain_gigachat import GigaChat
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from config import Config
from services.providers.base import BaseLLMProvider
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Маппинг ролей OpenAI → LangChain message-классы
_ROLE_MAP = {
    "system": SystemMessage,
    "user": HumanMessage,
    "assistant": AIMessage,
}


class GigaChatProvider(BaseLLMProvider):
    """
    Провайдер GigaChat через официальный langchain-gigachat.

    Авторизация — через credentials (Client ID:Client Secret, base64)
    из личного кабинета developers.sber.ru.
    """

    def __init__(self):
        self._llm = GigaChat(
            credentials=Config.GIGACHAT_CREDENTIALS,
            scope=Config.GIGACHAT_SCOPE,
            model=Config.GIGACHAT_MODEL,
            temperature=Config.GENERATION_CONFIG["temperature"],
            max_tokens=Config.GENERATION_CONFIG["max_tokens"],
            verify_ssl_certs=False,  # Сбер использует собственный CA
        )
        logger.info(f"GigaChatProvider → модель: {Config.GIGACHAT_MODEL}")

    def complete(self, messages: List[Dict[str, str]]) -> str:
        """
        Конвертирует OpenAI-формат сообщений в LangChain и вызывает GigaChat.

        Args:
            messages: [{"role": ..., "content": ...}]

        Returns:
            str: Текст ответа.
        """
        lc_messages = []
        for msg in messages:
            cls = _ROLE_MAP.get(msg["role"])
            if cls is None:
                logger.warning(f"Неизвестная роль: {msg['role']}, пропускаем")
                continue
            lc_messages.append(cls(content=msg["content"]))

        try:
            response = self._llm.invoke(lc_messages)
            return response.content
        except Exception as e:
            logger.error(f"GigaChat ошибка: {e}")
            raise
