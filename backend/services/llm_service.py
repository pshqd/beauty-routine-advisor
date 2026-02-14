"""
Сервис для работы с LLM (LM Studio).

TODO (Неделя 2): Интеграция с RAG системой
"""

import requests
from datetime import datetime
from typing import Dict, List, Any

from config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class LLMService:
    """
    Сервис для генерации ответов через LM Studio.
    
    На Неделе 1: Базовая интеграция без RAG
    На Неделе 2: Добавится интеграция с RAGService
    """
    
    def __init__(self):
        """Инициализация сервиса."""
        self.url = Config.LM_STUDIO_URL
        self.model = Config.LM_STUDIO_MODEL
        self.generation_config = Config.GENERATION_CONFIG
        
        logger.info(f"✅ LLMService инициализирован: {self.url}")
    
    def generate_response(
        self, 
        user_message: str, 
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Генерирует ответ от LLM на основе сообщения пользователя.
        
        Args:
            user_message (str): Сообщение пользователя
            conversation_history (list): История диалога
        
        Returns:
            dict: {
                "response": str,
                "sources": list,
                "timestamp": str
            }
        
        Raises:
            ConnectionError: Если LM Studio недоступен
            TimeoutError: Если превышен таймаут
        """
        try:
            # TODO (Неделя 2): Получить контекст из RAG
            context = self._get_context_stub()
            
            # Формируем промпт
            system_prompt = self._create_system_prompt(context)
            
            # Подготовка сообщений
            messages = [{"role": "system", "content": system_prompt}]
            
            if conversation_history:
                messages.extend(conversation_history)
            
            messages.append({"role": "user", "content": user_message})
            
            # Запрос в LM Studio
            logger.info("🤖 Отправка запроса в LM Studio...")
            llm_response = self._call_lm_studio(messages)
            
            logger.info(f"✅ Получен ответ: {llm_response[:50]}...")
            
            return {
                "response": llm_response,
                "sources": [context[:200]] if context else [],
                "timestamp": datetime.now().isoformat()
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
    
    def _call_lm_studio(self, messages: List[Dict[str, str]]) -> str:
        """
        Отправляет запрос в LM Studio API.
        
        Args:
            messages (list): Список сообщений
        
        Returns:
            str: Ответ от LLM
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.generation_config["temperature"],
            "max_tokens": self.generation_config["max_tokens"],
            "top_p": self.generation_config["top_p"],
            "stream": False
        }
        
        response = requests.post(
            self.url,
            json=payload,
            timeout=self.generation_config["timeout"]
        )
        
        response.raise_for_status()
        data = response.json()
        
        return data['choices'][0]['message']['content']
    
    def _get_context_stub(self) -> str:
        """
        Временная заглушка для контекста из базы знаний.
        
        TODO (Неделя 2): Заменить на RAGService.search()
        
        Returns:
            str: Базовый контекст
        """
        return """
        БАЗОВАЯ ИНФОРМАЦИЯ ПО УХОДУ ЗА КОЖЕЙ:
        
        Основные правила:
        1. Очищение 2 раза в день
        2. Увлажнение обязательно
        3. SPF защита каждый день
        4. Подбор средств по типу кожи
        
        Типы кожи: жирная, сухая, комбинированная, нормальная
        """
    
    def _create_system_prompt(self, context: str) -> str:
        """
        Создает системный промпт для LLM.
        
        Args:
            context (str): Контекст из базы знаний
        
        Returns:
            str: Системный промпт
        """
        return f"""Ты — эксперт-дерматолог и консультант по уходу за кожей.

ЗАДАЧА:

1. Если информации недостаточно — задай уточняющие вопросы:
   - Тип кожи (жирная, сухая, комбинированная, нормальная)
   - Основные проблемы (акне, морщины, пигментация)
   - Возраст
   - Текущий уход (если есть)

2. Когда информации достаточно — дай структурированные советы:
   ✅ Пошаговая рутина (утро/вечер)
   ✅ Рекомендуемые ингредиенты
   ✅ Что избегать
   ✅ Дополнительные советы

СТИЛЬ:
- Дружелюбный тон
- Эмодзи умеренно (1-2 на сообщение)
- Конкретные советы
- Если не уверен — советуй обратиться к дерматологу

БАЗА ЗНАНИЙ:
{context}

Базируй советы на этой информации!"""
