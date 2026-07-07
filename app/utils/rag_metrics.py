"""
Метрики качества RAG-системы.

Поддерживаемые метрики:
- Precision@K  : доля релевантных документов в топ-K
- Recall@K     : доля найденных релевантных из всех релевантных
- MRR          : Mean Reciprocal Rank
- Hit Rate@K   : есть ли хоть один релевантный в топ-K (бинарно)
- NDCG@K       : Normalized Discounted Cumulative Gain
- Mean Score   : среднее cosine-similarity чанков из RAG

Пример:
    from utils.rag_metrics import evaluate_retrieval

    results = evaluate_retrieval(
        retrieved=["doc_a", "doc_b", "doc_c"],
        relevant={"doc_a", "doc_d"},
        k=3,
    )
    # → {"precision@3": 0.333, "recall@3": 0.5, "mrr": 1.0, ...}
"""

import math
from typing import Sequence, Set


def precision_at_k(retrieved: Sequence[str], relevant: Set[str], k: int) -> float:
    """
    Precision@K = |retrieved[:k] ∩ relevant| / k

    Args:
        retrieved: Список ID документов в порядке ранжирования
        relevant:  Множество ID релевантных документов
        k:         Глубина отсечки

    Returns:
        float в [0, 1]
    """
    if k <= 0:
        return 0.0
    top_k = retrieved[:k]
    hits = sum(1 for doc in top_k if doc in relevant)
    return hits / k


def recall_at_k(retrieved: Sequence[str], relevant: Set[str], k: int) -> float:
    """
    Recall@K = |retrieved[:k] ∩ relevant| / |relevant|

    Returns:
        float в [0, 1]. 0.0 если relevant пустой.
    """
    if not relevant:
        return 0.0
    top_k = retrieved[:k]
    hits = sum(1 for doc in top_k if doc in relevant)
    return hits / len(relevant)


def reciprocal_rank(retrieved: Sequence[str], relevant: Set[str]) -> float:
    """
    RR = 1 / rank первого релевантного документа.
    0.0 если ни одного релевантного не найдено.
    """
    for rank, doc in enumerate(retrieved, start=1):
        if doc in relevant:
            return 1.0 / rank
    return 0.0


def hit_rate_at_k(retrieved: Sequence[str], relevant: Set[str], k: int) -> float:
    """
    Hit Rate@K = 1 если есть хоть один релевантный в топ-K, иначе 0.
    """
    top_k = retrieved[:k]
    return float(any(doc in relevant for doc in top_k))


def ndcg_at_k(retrieved: Sequence[str], relevant: Set[str], k: int) -> float:
    """
    NDCG@K с бинарной релевантностью.

    DCG  = Σ rel_i / log2(i+1), i от 1 до k
    IDCG = DCG при идеальном ранжировании (все релевантные сначала)
    NDCG = DCG / IDCG
    """
    if k <= 0 or not relevant:
        return 0.0

    top_k = retrieved[:k]
    dcg = sum(
        1.0 / math.log2(i + 2)
        for i, doc in enumerate(top_k)
        if doc in relevant
    )

    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_hits))

    return round(dcg / idcg, 4) if idcg > 0 else 0.0


def mean_retrieval_score(scores: Sequence[float]) -> float:
    """
    Среднее cosine-similarity чанков, возвращённых RAGService.search().

    Args:
        scores: Список значений chunk["score"] из RAGService.search()

    Returns:
        float — среднее, 0.0 если список пустой
    """
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 4)


def evaluate_retrieval(
    retrieved: Sequence[str],
    relevant: Set[str],
    k: int,
    scores: Sequence[float] | None = None,
) -> dict[str, float]:
    """
    Вычисляет все retrieval-метрики за один вызов.

    Args:
        retrieved: Упорядоченный список ID/source документов из RAG
        relevant:  Множество эталонных релевантных документов
        k:         Глубина отсечки для метрик @K
        scores:    Опциональные cosine-scores из RAG (chunk["score"])

    Returns:
        dict со всеми метриками:
            precision@k, recall@k, mrr, hit_rate@k, ndcg@k, mean_score
    """
    result: dict[str, float] = {
        f"precision@{k}": round(precision_at_k(retrieved, relevant, k), 4),
        f"recall@{k}": round(recall_at_k(retrieved, relevant, k), 4),
        "mrr": round(reciprocal_rank(retrieved, relevant), 4),
        f"hit_rate@{k}": hit_rate_at_k(retrieved, relevant, k),
        f"ndcg@{k}": ndcg_at_k(retrieved, relevant, k),
    }
    if scores is not None:
        result["mean_score"] = mean_retrieval_score(scores)
    return result
