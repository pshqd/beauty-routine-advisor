"""Провайдер LM Studio (локальный OpenAI-совместимый сервер)."""

import requests
from typing import Dict, List

from config import Config
from services.providers.base import BaseLLMProvider
from utils.logger import setup_logger

logger = setup_logger(__name__)


class LMStudioProvider(BaseLLMProvider):
    """Провайдер для локального LM Studio."""

    def __init__(self):
        self.url = Config.LM_STUDIO_URL
        self.model = Config.LM_STUDIO_MODEL
        self.cfg = Config.GENERATION_CONFIG
        logger.info(f"LMStudioProvider → {self.url}")

    def complete(self, messages: List[Dict[str, str]]) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.cfg["temperature"],
            "max_tokens": self.cfg["max_tokens"],
            "top_p": self.cfg["top_p"],
            "stream": False,
        }
        try:
            r = requests.post(self.url, json=payload, timeout=self.cfg["timeout"])
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                "LM Studio недоступен. Запустите сервер на порту 1234."
            )
        except requests.exceptions.Timeout:
            raise TimeoutError("LM Studio не ответил за отведённое время.")
