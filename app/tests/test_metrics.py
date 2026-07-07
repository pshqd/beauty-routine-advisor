"""
Тесты MetricsCollector.
Проверяется вся публичная логика: counters, gauges, histograms, snapshot, reset.
"""

import pytest
import threading
import time


class TestCounters:

    def test_inc_default(self, fresh_metrics):
        """inc() без аргумента value увеличивает на 1."""
        fresh_metrics.inc("req")
        assert fresh_metrics.get_counter("req") == 1.0

    def test_inc_custom_value(self, fresh_metrics):
        fresh_metrics.inc("req", 5)
        assert fresh_metrics.get_counter("req") == 5.0

    def test_inc_accumulates(self, fresh_metrics):
        for _ in range(10):
            fresh_metrics.inc("req")
        assert fresh_metrics.get_counter("req") == 10.0

    def test_missing_counter_returns_zero(self, fresh_metrics):
        assert fresh_metrics.get_counter("nonexistent") == 0.0

    def test_counters_independent(self, fresh_metrics):
        fresh_metrics.inc("a", 3)
        fresh_metrics.inc("b", 7)
        assert fresh_metrics.get_counter("a") == 3.0
        assert fresh_metrics.get_counter("b") == 7.0

    def test_thread_safety(self, fresh_metrics):
        """1000 потоков инкрементируют счётчик без гоночных условий."""
        threads = [threading.Thread(target=fresh_metrics.inc, args=("t",)) for _ in range(1000)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert fresh_metrics.get_counter("t") == 1000.0


class TestGauges:

    def test_set_and_get(self, fresh_metrics):
        fresh_metrics.set_gauge("active_conn", 42)
        assert fresh_metrics.get_gauge("active_conn") == 42

    def test_overwrite(self, fresh_metrics):
        fresh_metrics.set_gauge("g", 1)
        fresh_metrics.set_gauge("g", 99)
        assert fresh_metrics.get_gauge("g") == 99

    def test_missing_gauge_returns_none(self, fresh_metrics):
        assert fresh_metrics.get_gauge("nonexistent") is None


class TestHistograms:

    def test_observe_and_stats(self, fresh_metrics):
        for v in [10, 20, 30, 40, 50]:
            fresh_metrics.observe("latency", v)
        stats = fresh_metrics.get_histogram_stats("latency")
        assert stats["count"] == 5
        assert stats["mean"] == pytest.approx(30.0)
        assert stats["max"] == pytest.approx(50.0)

    def test_empty_histogram(self, fresh_metrics):
        stats = fresh_metrics.get_histogram_stats("empty")
        assert stats["count"] == 0
        assert stats["mean"] == 0.0

    def test_p95_single_value(self, fresh_metrics):
        fresh_metrics.observe("x", 100.0)
        stats = fresh_metrics.get_histogram_stats("x")
        assert stats["p95"] == pytest.approx(100.0)

    def test_p95_large_sample(self, fresh_metrics):
        for i in range(1, 101):
            fresh_metrics.observe("h", float(i))
        stats = fresh_metrics.get_histogram_stats("h")
        assert stats["p95"] >= 95.0
        assert stats["p99"] >= 99.0


class TestSnapshot:

    def test_snapshot_structure(self, fresh_metrics):
        snap = fresh_metrics.snapshot()
        assert "uptime_seconds" in snap
        assert "counters" in snap
        assert "gauges" in snap
        assert "histograms" in snap

    def test_snapshot_reflects_data(self, fresh_metrics):
        fresh_metrics.inc("reqs", 3)
        fresh_metrics.set_gauge("workers", 4)
        fresh_metrics.observe("ms", 123.0)
        snap = fresh_metrics.snapshot()
        assert snap["counters"]["reqs"] == 3.0
        assert snap["gauges"]["workers"] == 4
        assert snap["histograms"]["ms"]["count"] == 1

    def test_uptime_positive(self, fresh_metrics):
        time.sleep(0.01)
        snap = fresh_metrics.snapshot()
        assert snap["uptime_seconds"] > 0


class TestReset:

    def test_reset_clears_counters(self, fresh_metrics):
        fresh_metrics.inc("x", 10)
        fresh_metrics.reset()
        assert fresh_metrics.get_counter("x") == 0.0

    def test_reset_clears_histograms(self, fresh_metrics):
        fresh_metrics.observe("y", 5.0)
        fresh_metrics.reset()
        assert fresh_metrics.get_histogram_stats("y")["count"] == 0
