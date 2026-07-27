"""
Сборщик runtime-метрик приложения.

Метрики хранятся в памяти (in-process). Для прода можно подключить
Prometheus-экспортер — достаточно заменить MetricsCollector на
prometheus_client.Counter / Histogram.

Использование:
    from utils.metrics import metrics
    metrics.inc("chat_requests_total")
    metrics.observe("llm_latency_ms", 342.5)
    print(metrics.snapshot())   # → dict со всеми метриками
"""

import time
import threading
from collections import defaultdict
from typing import Any


class MetricsCollector:
    """
    Потокобезопасный in-memory коллектор метрик.

    Поддерживает три типа:
    - counter  : монотонно возрастающий счётчик (inc)
    - gauge    : произвольное текущее значение   (set_gauge)
    - histogram: набор наблюдений для avg/p95/max (observe)
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._counters: dict[str, float] = defaultdict(float)
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._started_at = time.time()

    # ------------------------------------------------------------------ #
    # Counters
    # ------------------------------------------------------------------ #

    def inc(self, name: str, value: float = 1.0) -> None:
        """Увеличивает счётчик на value."""
        with self._lock:
            self._counters[name] += value

    def get_counter(self, name: str) -> float:
        with self._lock:
            return self._counters.get(name, 0.0)

    # ------------------------------------------------------------------ #
    # Gauges
    # ------------------------------------------------------------------ #

    def set_gauge(self, name: str, value: float) -> None:
        """Устанавливает текущее значение gauge."""
        with self._lock:
            self._gauges[name] = value

    def get_gauge(self, name: str) -> float | None:
        with self._lock:
            return self._gauges.get(name)

    # ------------------------------------------------------------------ #
    # Histograms
    # ------------------------------------------------------------------ #

    def observe(self, name: str, value: float) -> None:
        """Записывает наблюдение в гистограмму."""
        with self._lock:
            self._histograms[name].append(value)

    def get_histogram_stats(self, name: str) -> dict[str, float]:
        """
        Возвращает статистику по гистограмме.

        Returns:
            dict с count, mean, p50, p95, p99, max
        """
        with self._lock:
            values = sorted(self._histograms.get(name, []))

        if not values:
            return {"count": 0, "mean": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0}

        n = len(values)

        def percentile(p: float) -> float:
            idx = int(p / 100 * n)
            return values[min(idx, n - 1)]

        return {
            "count": n,
            "mean": round(sum(values) / n, 2),
            "p50": round(percentile(50), 2),
            "p95": round(percentile(95), 2),
            "p99": round(percentile(99), 2),
            "max": round(values[-1], 2),
        }

    # ------------------------------------------------------------------ #
    # Snapshot
    # ------------------------------------------------------------------ #

    def snapshot(self) -> dict[str, Any]:
        """Возвращает полный снимок всех метрик."""
        with self._lock:
            counters = dict(self._counters)
            gauges = dict(self._gauges)
            histogram_names = list(self._histograms.keys())

        histograms = {
            name: self.get_histogram_stats(name)
            for name in histogram_names
        }

        uptime_s = round(time.time() - self._started_at, 1)

        return {
            "uptime_seconds": uptime_s,
            "counters": counters,
            "gauges": gauges,
            "histograms": histograms,
        }

    def reset(self) -> None:
        """Сбрасывает все метрики (используется в тестах)."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._started_at = time.time()


# Глобальный синглтон — импортируйте отовсюду
metrics = MetricsCollector()
