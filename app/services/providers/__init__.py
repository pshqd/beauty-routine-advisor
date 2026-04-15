"""Фабрика: возвращает нужный провайдер по LLM_PROVIDER из конфига."""

from config import Config
from services.providers.base import BaseLLMProvider


def get_provider() -> BaseLLMProvider:
    """
    Создаёт и возвращает провайдер согласно Config.LLM_PROVIDER.

    Returns:
        BaseLLMProvider: Готовый к работе провайдер.

    Raises:
        ValueError: Если провайдер не поддерживается.
    """
    provider = Config.LLM_PROVIDER.lower()

    if provider == "lm_studio":
        from services.providers.lm_studio import LMStudioProvider
        return LMStudioProvider()

    if provider == "gigachat":
        from services.providers.gigachat import GigaChatProvider
        return GigaChatProvider()

    if provider == "openrouter":
        from services.providers.openrouter import OpenRouterProvider
        return OpenRouterProvider()

    raise ValueError(
        f"Неизвестный провайдер: '{provider}'. "
        "Допустимые значения: lm_studio, gigachat, openrouter"
    )