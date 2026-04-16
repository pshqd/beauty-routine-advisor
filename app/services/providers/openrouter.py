"""Провайдер OpenRouter — доступ к сотням моделей через один API."""

import requests
from typing import Dict, List

from config import Config
from services.providers.base import BaseLLMProvider
from utils.logger import setup_logger

logger = setup_logger(__name__)


class OpenRouterProvider(BaseLLMProvider):
    """
    Провайдер OpenRouter (openrouter.ai).

    OpenAI-совместимый API, поддерживает:
    mistralai/mistral-7b-instruct, meta-llama/llama-3-8b-instruct,
    google/gemma-3-27b-it, anthropic/claude-3-haiku и др.
    """

    def __init__(self):
        if not Config.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY не задан в .env")
        self.url = Config.OPENROUTER_URL
        self.model = Config.OPENROUTER_MODEL
        self.cfg = Config.GENERATION_CONFIG
        self.headers = {
            "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            # Опционально — отображается в статистике на openrouter.ai
            "X-Title": "SkinCare Advisor",
        }
        logger.info(f"OpenRouterProvider → {self.model}")

    def complete(self, messages: List[Dict[str, str]]) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.cfg["temperature"],
            "max_tokens": self.cfg["max_tokens"],
            "top_p": self.cfg["top_p"],
        }
        try:
            r = requests.post(
                self.url,
                headers=self.headers,
                json=payload,
                timeout=self.cfg["timeout"],
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except requests.exceptions.ConnectionError:
            raise ConnectionError("OpenRouter недоступен.")
        except requests.exceptions.Timeout:
            raise TimeoutError("OpenRouter не ответил за отведённое время.")
        except requests.exceptions.HTTPError as e:
            logger.error(f"OpenRouter HTTP {r.status_code}: {r.text}")
            raise ValueError(f"OpenRouter API ошибка: {r.status_code}") from e
