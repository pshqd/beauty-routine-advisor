"""
Тесты RAG retrieval-метрик.

RAG метрики проверяются на синтетических примерах,
без реальных ML-моделей — чистая математика.
"""

import math
import pytest
from utils.rag_metrics import (
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    hit_rate_at_k,
    ndcg_at_k,
    mean_retrieval_score,
    evaluate_retrieval,
)


# ================================================================== #
# precision_at_k
# ================================================================== #

class TestPrecisionAtK:

    def test_all_relevant(self):
        assert precision_at_k(["a", "b", "c"], {"a", "b", "c"}, 3) == pytest.approx(1.0)

    def test_none_relevant(self):
        assert precision_at_k(["a", "b", "c"], {"x", "y"}, 3) == pytest.approx(0.0)

    def test_partial(self):
        assert precision_at_k(["a", "b", "c"], {"a", "c"}, 3) == pytest.approx(2 / 3)

    def test_k_less_than_retrieved(self):
        # Топ-1: только первый документ — он релевантен
        assert precision_at_k(["a", "b", "c"], {"a"}, 1) == pytest.approx(1.0)

    def test_k_zero_returns_zero(self):
        assert precision_at_k(["a", "b"], {"a"}, 0) == 0.0

    def test_empty_retrieved(self):
        assert precision_at_k([], {"a"}, 3) == pytest.approx(0.0)


# ================================================================== #
# recall_at_k
# ================================================================== #

class TestRecallAtK:

    def test_full_recall(self):
        assert recall_at_k(["a", "b", "c"], {"a", "b"}, 3) == pytest.approx(1.0)

    def test_partial_recall(self):
        assert recall_at_k(["a", "b", "c"], {"a", "b", "d"}, 3) == pytest.approx(2 / 3)

    def test_zero_recall(self):
        assert recall_at_k(["x", "y"], {"a", "b"}, 3) == pytest.approx(0.0)

    def test_empty_relevant_returns_zero(self):
        assert recall_at_k(["a", "b"], set(), 3) == 0.0

    def test_k_limits_scope(self):
        # relevant=a, retrieved=[b, a, c] -> в top-1 нет a
        assert recall_at_k(["b", "a", "c"], {"a"}, 1) == pytest.approx(0.0)


# ================================================================== #
# reciprocal_rank
# ================================================================== #

class TestReciprocalRank:

    def test_first_position(self):
        assert reciprocal_rank(["a", "b", "c"], {"a"}) == pytest.approx(1.0)

    def test_second_position(self):
        assert reciprocal_rank(["x", "a", "c"], {"a"}) == pytest.approx(0.5)

    def test_third_position(self):
        assert reciprocal_rank(["x", "y", "a"], {"a"}) == pytest.approx(1 / 3)

    def test_not_found(self):
        assert reciprocal_rank(["x", "y", "z"], {"a"}) == pytest.approx(0.0)

    def test_empty_retrieved(self):
        assert reciprocal_rank([], {"a"}) == 0.0


# ================================================================== #
# hit_rate_at_k
# ================================================================== #

class TestHitRateAtK:

    def test_hit(self):
        assert hit_rate_at_k(["a", "b", "c"], {"c"}, 3) == 1.0

    def test_miss(self):
        assert hit_rate_at_k(["a", "b", "c"], {"z"}, 3) == 0.0

    def test_k_excludes_relevant(self):
        # relevant=c, k=2: топ-2 = [a, b] — не попали
        assert hit_rate_at_k(["a", "b", "c"], {"c"}, 2) == 0.0


# ================================================================== #
# ndcg_at_k
# ================================================================== #

class TestNdcgAtK:

    def test_perfect_ranking(self):
        # Все релевантные стоят первыми — NDCG = 1.0
        assert ndcg_at_k(["a", "b"], {"a", "b"}, 2) == pytest.approx(1.0, abs=1e-3)

    def test_no_relevant_in_top(self):
        assert ndcg_at_k(["x", "y"], {"a", "b"}, 2) == pytest.approx(0.0)

    def test_partial_relevance(self):
        # retrieved=[a, x, b], relevant={a, b}, k=3
        # DCG = 1/log2(2) + 0 + 1/log2(4) = 1 + 0.5 = 1.5
        # IDCG = 1/log2(2) + 1/log2(3) ≈ 1.631
        result = ndcg_at_k(["a", "x", "b"], {"a", "b"}, 3)
        assert 0.0 < result < 1.0

    def test_empty_relevant(self):
        assert ndcg_at_k(["a", "b"], set(), 2) == 0.0

    def test_k_zero(self):
        assert ndcg_at_k(["a"], {"a"}, 0) == 0.0


# ================================================================== #
# mean_retrieval_score
# ================================================================== #

class TestMeanRetrievalScore:

    def test_basic(self):
        assert mean_retrieval_score([0.8, 0.6, 0.7]) == pytest.approx(0.7, abs=0.001)

    def test_empty(self):
        assert mean_retrieval_score([]) == 0.0

    def test_single(self):
        assert mean_retrieval_score([0.95]) == pytest.approx(0.95)


# ================================================================== #
# evaluate_retrieval (интеграция)
# ================================================================== #

class TestEvaluateRetrieval:

    def test_returns_all_keys(self):
        result = evaluate_retrieval(
            retrieved=["a", "b", "c"],
            relevant={"a"},
            k=3,
        )
        assert "precision@3" in result
        assert "recall@3" in result
        assert "mrr" in result
        assert "hit_rate@3" in result
        assert "ndcg@3" in result

    def test_includes_mean_score_when_provided(self):
        result = evaluate_retrieval(
            retrieved=["a", "b"],
            relevant={"a"},
            k=2,
            scores=[0.9, 0.7],
        )
        assert "mean_score" in result
        assert result["mean_score"] == pytest.approx(0.8, abs=0.001)

    def test_no_mean_score_without_scores(self):
        result = evaluate_retrieval(["a"], {"a"}, k=1)
        assert "mean_score" not in result

    def test_perfect_retrieval(self):
        result = evaluate_retrieval(
            retrieved=["a", "b", "c"],
            relevant={"a", "b", "c"},
            k=3,
        )
        assert result["precision@3"] == pytest.approx(1.0)
        assert result["recall@3"] == pytest.approx(1.0)
        assert result["mrr"] == pytest.approx(1.0)
        assert result["hit_rate@3"] == 1.0

    def test_empty_retrieval(self):
        result = evaluate_retrieval(
            retrieved=[],
            relevant={"a", "b"},
            k=3,
        )
        assert result["precision@3"] == 0.0
        assert result["mrr"] == 0.0
        assert result["hit_rate@3"] == 0.0

    def test_realistic_scenario(self):
        """Реалистичный сценарий: RAG нашёл 2 из 4 релевантных в top-3."""
        retrieved = ["dry_care.md", "oily_care.md", "spf_guide.md"]
        relevant = {"dry_care.md", "spf_guide.md", "moisturizer.md", "toner.md"}
        result = evaluate_retrieval(retrieved, relevant, k=3, scores=[0.91, 0.75, 0.82])

        # precision@3 = 2/3 ≈ 0.667
        assert result["precision@3"] == pytest.approx(2 / 3, abs=0.001)
        # recall@3 = 2/4 = 0.5
        assert result["recall@3"] == pytest.approx(0.5, abs=0.001)
        # mrr: первый релевантный на позиции 1
        assert result["mrr"] == pytest.approx(1.0)
        assert result["hit_rate@3"] == 1.0
        assert result["mean_score"] == pytest.approx((0.91 + 0.75 + 0.82) / 3, abs=0.001)
