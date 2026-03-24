"""
Сервис для работы с RAG системой (векторный поиск по базе знаний).
Использует ChromaDB и SentenceTransformer для семантического поиска.
"""

import pathlib
from typing import List, Dict, Optional

import chromadb
from sentence_transformers import SentenceTransformer

from utils.logger import setup_logger
from config import Config

logger = setup_logger(__name__)

CHROMA_DIR = Config.EMBEDDINGS_DB_PATH
COLLECTION_NAME = Config.COLLECTION_KB
EMBED_MODEL = Config.EMBEDDING_MODEL


class RAGService:
    """
    Сервис для семантического поиска по базе знаний.

    Подключается к ChromaDB, генерирует эмбеддинг запроса и возвращает
    топ-k релевантных чанков, опционально фильтруя по типу кожи.
    """

    def __init__(self):
        """
        Инициализирует ChromaDB клиент и модель эмбеддингов.

        Raises:
            RuntimeError: Если база знаний не проиндексирована.
        """
        if not CHROMA_DIR.exists():
            raise RuntimeError(
                f"База знаний не найдена: {CHROMA_DIR}. "
                "Запустите сначала: python init_kb.py"
            )
        self._client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self._collection = self._client.get_collection(COLLECTION_NAME)
        self._model = SentenceTransformer(EMBED_MODEL)
        logger.info(
            f"RAGService инициализирован. "
            f"Чанков в коллекции: {self._collection.count()}"
        )

    def search(
        self,
        query: str,
        top_k: int = 3,
        skin_type: Optional[str] = None,
    ) -> List[Dict]:
        """
        Выполняет семантический поиск по базе знаний.

        Args:
            query (str): Запрос пользователя.
            top_k (int): Количество результатов (по умолчанию 3).
            skin_type (str, optional): Фильтр по типу кожи.
                Допустимые значения: 'жирная', 'сухая', 'комбинированная',
                'нормальная', 'чувствительная', 'all'.

        Returns:
            list[dict]: Список словарей:
                - text (str): Текст чанка
                - source (str): Имя исходного файла
                - section (str): Заголовок раздела
                - score (float): Косинусное сходство (0–1)
        """
        logger.debug(f"RAG поиск: '{query[:40]}', skin_type={skin_type}")
        embedding = self._model.encode(query, normalize_embeddings=True).tolist()

        where_filter = None
        if skin_type and skin_type != "all":
            where_filter = {
                "$or": [
                    {"skin_type": {"$eq": skin_type}},
                    {"skin_type": {"$eq": "all"}},
                ]
            }

        results = self._collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        chunks = []
        for i in range(len(results["documents"][0])):
            score = 1.0 - results["distances"][0][i]
            meta = results["metadatas"][0][i]
            chunks.append({
                "text": results["documents"][0][i],
                "source": meta.get("source", ""),
                "section": meta.get("section", ""),
                "score": round(score, 3),
            })

        logger.debug(f"Найдено {len(chunks)} чанков")
        return chunks
