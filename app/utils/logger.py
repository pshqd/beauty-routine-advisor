"""
Структурированное логирование для приложения.
Поддерживает JSON-формат для продакшена и human-readable для разработки.
"""

import logging
import sys
import json
import time
from datetime import datetime
from typing import Any
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """
    Форматтер для структурированных JSON-логов.
    Удобен для парсинга в ELK/Loki/любом log aggregator.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Прокидываем extra-поля (request_id, latency_ms, etc.)
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "levelname", "levelno",
                "pathname", "filename", "module", "exc_info",
                "exc_text", "stack_info", "lineno", "funcName",
                "created", "msecs", "relativeCreated", "thread",
                "threadName", "processName", "process", "message",
                "taskName",
            ):
                log_entry[key] = value

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


class HumanFormatter(logging.Formatter):
    """Human-readable форматтер для локальной разработки."""

    LEVEL_COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.LEVEL_COLORS.get(record.levelname, "")
        prefix = f"{color}[{record.levelname}]{self.RESET}"
        ts = datetime.utcnow().strftime("%H:%M:%S")
        base = f"{ts} {prefix} {record.name} — {record.getMessage()}"
        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)
        return base


def setup_logger(
    name: str,
    level: str = "INFO",
    json_format: bool = False,
    log_file: str | None = "logs/app.log",
) -> logging.Logger:
    """
    Настраивает и возвращает logger для модуля.

    Args:
        name:        Имя модуля (обычно __name__)
        level:       Уровень логирования (DEBUG/INFO/WARNING/ERROR)
        json_format: True → JSON-логи (для прода), False → human-readable
        log_file:    Путь к файлу логов. None — только stdout.

    Returns:
        logging.Logger: Настроенный logger
    """
    logger = logging.getLogger(name)

    # Предотвращаем дублирование хендлеров при повторном вызове
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    # Не пробрасываем в root-logger (избегаем дублей)
    logger.propagate = False

    formatter: logging.Formatter = (
        JSONFormatter() if json_format else HumanFormatter()
    )

    # --- stdout handler ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # --- file handler ---
    if log_file:
        try:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            file_formatter = JSONFormatter()  # в файл всегда JSON
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Не удалось создать файл логов '{log_file}': {e}")

    return logger


class RequestLogger:
    """
    Контекстный менеджер для логирования HTTP-запросов с замером latency.

    Пример:
        with RequestLogger(logger, "POST /api/chat", request_id="abc") as rl:
            result = llm_service.generate_response(...)
            rl.set_extra(chunks_found=3)
    """

    def __init__(self, logger: logging.Logger, operation: str, **extra):
        self.logger = logger
        self.operation = operation
        self.extra = extra
        self._start: float = 0.0
        self._additional: dict[str, Any] = {}

    def set_extra(self, **kwargs):
        """Добавляет дополнительные поля в итоговый лог."""
        self._additional.update(kwargs)

    def __enter__(self):
        self._start = time.perf_counter()
        self.logger.info(
            f"→ {self.operation} started",
            extra={**self.extra, "event": "request_start"},
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        latency_ms = round((time.perf_counter() - self._start) * 1000, 2)
        if exc_type:
            self.logger.error(
                f"✗ {self.operation} failed in {latency_ms}ms",
                extra={
                    **self.extra,
                    **self._additional,
                    "latency_ms": latency_ms,
                    "event": "request_error",
                    "error": str(exc_val),
                },
                exc_info=True,
            )
        else:
            self.logger.info(
                f"✓ {self.operation} done in {latency_ms}ms",
                extra={
                    **self.extra,
                    **self._additional,
                    "latency_ms": latency_ms,
                    "event": "request_done",
                },
            )
        return False  # не подавляем исключение
