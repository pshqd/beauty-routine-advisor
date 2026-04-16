"""Базовый интерфейс для всех LLM-провайдеров."""

from abc import ABC, abstractmethod
from typing import Dict, List


class BaseLLMProvider(ABC):
    """
    Абстрактный провайдер LLM.
    Каждый провайдер реализует один метод — complete().
    """

    @abstractmethod
    def complete(self, messages: List[Dict[str, str]]) -> str:
        """
        Отправляет список сообщений в LLM и возвращает текст ответа.

        Args:
            messages: [{"role": "system"|"user"|"assistant", "content": str}]

        Returns:
            str: Текст ответа модели.

        Raises:
            ConnectionError: Провайдер недоступен.
            TimeoutError: Превышен таймаут.
            ValueError: Неверный ответ от API.
        """
        ...
