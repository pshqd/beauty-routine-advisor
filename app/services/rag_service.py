# app/services/rag_service.py
"""RAG: FAISS-поиск с LangChain retriever."""

from typing import List, Dict, Optional
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class RAGService:
    """Семантический поиск по базе знаний через FAISS."""

    def __init__(self):
        if not Config.FAISS_INDEX_PATH.exists():
            raise RuntimeError(
                f"Индекс не найден: {Config.FAISS_INDEX_PATH}. "
                "Запустите: python init_kb.py"
            )
        self._embeddings = HuggingFaceEmbeddings(
            model_name=Config.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        self._vs = FAISS.load_local(
            str(Config.FAISS_INDEX_PATH),
            self._embeddings,
            allow_dangerous_deserialization=True,
        )
        logger.info(f"✅ RAGService: {self._vs.index.ntotal} векторов")

    def search(
        self, query: str, top_k: int = None, skin_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Семантический поиск, опциональная пост-фильтрация по skin_type.

        Returns:
            list[dict]: text, source, section, score
        """
        k = top_k or Config.RETRIEVAL_K
        # Берём больше, чтобы после фильтрации осталось достаточно
        fetch_k = k * 3 if skin_type else k
        results = self._vs.similarity_search_with_score(query, k=fetch_k)

        chunks = []
        for doc, dist in results:
            meta = doc.metadata
            if skin_type and skin_type != "all":
                st = meta.get("skin_type", "all")
                if st not in (skin_type, "all", ""):
                    continue
            chunks.append({
                "text": doc.page_content,
                "source": meta.get("source", ""),
                "section": meta.get("h2") or meta.get("h1", ""),
                "score": round(1.0 - float(dist), 3),
            })
            if len(chunks) == k:
                break

        logger.debug(f"RAG: {len(chunks)} чанков для '{query[:40]}'")
        return chunks