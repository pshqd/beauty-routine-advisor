"""
Сервис для работы с RAG системой (векторный поиск по базе знаний).

TODO (Неделя 2): Полная реализация с ChromaDB
"""

from typing import List
from utils.logger import setup_logger

logger = setup_logger(__name__)


class RAGService:
    """
    Сервис для семантического поиска по базе знаний.
    
    На Неделе 1: Заглушка
    На Неделе 2: Интеграция ChromaDB + sentence-transformers
    """
    
    def __init__(self):
        """Инициализация RAG сервиса."""
        logger.info("⚠️  RAGService: Заглушка (будет реализован на Неделе 2)")
    
    def search(self, query: str, top_k: int = 2) -> List[str]:
        """
        Ищет релевантные секции в базе знаний.
        
        TODO (Неделя 2): Реализовать:
        - Загрузка markdown файлов
        - Разбиение на чанки
        - Генерация эмбеддингов
        - Поиск через ChromaDB
        
        Args:
            query (str): Запрос пользователя
            top_k (int): Количество результатов
        
        Returns:
            list: Релевантные тексты из базы знаний
        """
        # Заглушка
        logger.debug(f"RAGService.search вызван с query: {query[:30]}...")
        return []
    
    def index_knowledge_base(self):
        """
        Индексирует базу знаний в ChromaDB.
        
        TODO (Неделя 2): Реализовать индексацию MD файлов
        """
        logger.info("⚠️  index_knowledge_base: Заглушка")
        pass
