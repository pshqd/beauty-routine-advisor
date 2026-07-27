"""
Тесты для GET /api/metrics и интеграции middleware в Flask.
Использует flask_app и client fixtures из conftest.py.
"""

import pytest


class TestMetricsEndpoint:

    def test_get_metrics_returns_200(self, client):
        resp = client.get("/api/metrics")
        assert resp.status_code == 200

    def test_metrics_json_structure(self, client):
        resp = client.get("/api/metrics")
        data = resp.get_json()
        assert "uptime_seconds" in data
        assert "counters" in data
        assert "histograms" in data

    def test_request_increments_counter(self, client):
        from utils.metrics import metrics
        before = metrics.get_counter("http_requests_total")
        client.get("/api/health")
        after = metrics.get_counter("http_requests_total")
        assert after > before

    def test_latency_histogram_populated(self, client):
        client.get("/api/health")
        from utils.metrics import metrics
        stats = metrics.get_histogram_stats("http_latency_ms")
        assert stats["count"] >= 1
        assert stats["mean"] > 0
