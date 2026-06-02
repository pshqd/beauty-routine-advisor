import requests
from datetime import datetime
from typing import Dict, List, Any
from services.rag_service import RAGService

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
        self._rag = RAGService()

        logger.info(f"LLMService инициализирован: {self.url}")

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
                "sources": list[dict],
                "timestamp": str
            }

        Raises:
            ConnectionError: Если LM Studio недоступен
            TimeoutError: Если превышен таймаут
        """
        try:
            raw_chunks = self._rag.search(user_message)

            # Форматируем источники в структурированные объекты
            sources = self._format_sources(raw_chunks)

            # Собираем текстовый контекст для промпта
            context = "\n\n".join(c["text"] for c in raw_chunks) if raw_chunks else ""

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
                "sources": sources,
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

    def _format_sources(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Преобразует сырые чанки из RAG в структурированные объекты источников.
        Дедуплицирует по (source, section).

        Args:
            chunks (list): Список чанков вида {text, source, section, score}

        Returns:
            list[dict]: [
                {
                    "title": str,   — заголовок секции или имя файла
                    "file": str,    — относительный путь к файлу в БЗ
                    "preview": str, — первые ~200 символов текста чанка
                    "score": float  — релевантность 0..1
                },
                ...
            ]
        """
        seen = set()
        sources = []

        for chunk in chunks:
            source = chunk.get("source", "")
            section = chunk.get("section", "")
            key = (source, section)

            if key in seen:
                continue
            seen.add(key)

            title = section if section else source
            preview_text = chunk.get("text", "")
            preview = (preview_text[:1000] + "...") if len(preview_text) > 500 else preview_text

            sources.append({
                "title": title,
                "file": source,
                "preview": preview,
                "score": round(chunk.get("score", 0.0), 2)
            })

        return sources

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

    def _get_context_stub(self, query: str = "") -> List[Dict[str, Any]]:
        """
        Временная заглушка: возвращает чанки в формате, совместимом
        с будущим RAGService.search().

        TODO (Неделя 2): Заменить на RAGService.search(query)

        Args:
            query (str): Запрос пользователя (пока не используется)

        Returns:
            list[dict]: Список чанков с полями text/source/section/score
        """
        return [
            {
                "text": (
                    "Основные правила ухода за кожей:\n"
                    "1. Очищение 2 раза в день\n"
                    "2. Увлажнение обязательно\n"
                    "3. SPF защита каждый день\n"
                    "4. Подбор средств по типу кожи\n"
                    "Типы кожи: жирная, сухая, комбинированная, нормальная"
                ),
                "source": "skincare_kb/06_procedures_and_techniques/01_daily_skincare_rituals.md",
                "section": "Базовые правила ухода",
                "score": 0.91
            }
        ]

    def _create_system_prompt(self, context: str) -> str:
        """
        Создает системный промпт для LLM.

        Args:
            context (str): Контекст из базы знаний

        Returns:
            str: Системный промпт
        """
        context_block = (
            f"## База знаний\n{context}"
            if context.strip()
            else "## База знаний\nКонтекст не найден. Опирайся на общие знания о дерматологии."
        )

        return f"""Ты — AI-консультант по уходу за кожей и дерматологии. \
Ты помогаешь пользователям подобрать персональный уход, разобраться с проблемами кожи и составить бьюти-рутину.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
ГРАНИЦЫ РОЛИ (строго)
━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Отвечаешь ТОЛЬКО на темы:
   — уход за кожей лица и тела
   - лысость, здоровье
   — дерматологические проблемы (акне, пигментация, розацеа, сухость, жирность и др.)
   — бьюти-рутина, косметические ингредиенты, средства
   — питание и образ жизни в контексте здоровья кожи
   — общее самочувствие, если оно влияет на состояние кожи

❌ Если вопрос НЕ связан с этими темами — вежливо откажись:
   «Я специализируюсь только на уходе за кожей и дерматологии. \
Чем могу помочь по этой теме? 😊»
   НЕ отвечай на вопросы про политику, технологии, историю, кулинарию и любые другие темы.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
ЛОГИКА ДИАЛОГА
━━━━━━━━━━━━━━━━━━━━━━━━━━━
ШАГ 1 — Сбор информации (если её недостаточно):
Задай уточняющие вопросы (не все сразу, только недостающие):
   • Тип кожи: жирная / сухая / комбинированная / нормальная / чувствительная
   • Основная проблема: акне, морщины, пигментация, сухость, поры и т.д.
   • Возраст (влияет на подбор активных ингредиентов)
   • Текущий уход: что уже используешь?
   • Аллергии или непереносимости (если есть)

ШАГ 2 — Рекомендация (когда информации достаточно):
Дай структурированный ответ:
   🌅 Утренняя рутина — пошаговый порядок средств
   🌙 Вечерняя рутина — пошаговый порядок средств
   ✅ Рекомендуемые ингредиенты — с коротким объяснением зачем
   ❌ Что избегать — конкретные ингредиенты или привычки
   💡 Дополнительные советы — образ жизни, питание, частота процедур

━━━━━━━━━━━━━━━━━━━━━━━━━━━
СТИЛЬ ОТВЕТА
━━━━━━━━━━━━━━━━━━━━━━━━━━━
— Тон: дружелюбный, но профессиональный
— Эмодзи: 10-20 на сообщение, много
— Длина: ёмко и по делу, без воды
— Используй markdown: заголовки, списки, **жирный** для ключевых слов
— Если рекомендация требует осмотра врача — обязательно скажи об этом:
  «Для точной диагностики лучше обратиться к дерматологу»
— Не ставь диагнозы. Ты консультант, не врач.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
{context_block}

Базируй советы на информации из базы знаний. \
Если в базе знаний нет точного ответа — используй общепризнанные дерматологические рекомендации \
и обязательно уточни, что это общая информация.
"""