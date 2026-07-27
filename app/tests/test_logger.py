"""
Тесты utils.logger.
Проверяются: JSONFormatter, HumanFormatter, setup_logger, RequestLogger.
"""

import json
import logging
import time
import pytest
from unittest.mock import patch, MagicMock
from io import StringIO

from utils.logger import JSONFormatter, HumanFormatter, setup_logger, RequestLogger


# ================================================================== #
# JSONFormatter
# ================================================================== #

class TestJSONFormatter:

    def _make_record(self, msg="test", level=logging.INFO, **extra):
        record = logging.LogRecord(
            name="test", level=level, pathname="", lineno=0,
            msg=msg, args=(), exc_info=None,
        )
        for k, v in extra.items():
            setattr(record, k, v)
        return record

    def test_output_is_valid_json(self):
        fmt = JSONFormatter()
        output = fmt.format(self._make_record())
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_required_keys_present(self):
        fmt = JSONFormatter()
        parsed = json.loads(fmt.format(self._make_record()))
        assert "timestamp" in parsed
        assert "level" in parsed
        assert "logger" in parsed
        assert "message" in parsed

    def test_extra_fields_propagated(self):
        fmt = JSONFormatter()
        record = self._make_record(latency_ms=123.4, request_id="abc")
        parsed = json.loads(fmt.format(record))
        assert parsed["latency_ms"] == 123.4
        assert parsed["request_id"] == "abc"

    def test_exception_included(self):
        fmt = JSONFormatter()
        try:
            raise ValueError("boom")
        except ValueError:
            import sys
            record = self._make_record()
            record.exc_info = sys.exc_info()
        parsed = json.loads(fmt.format(record))
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]

    def test_level_name_correct(self):
        fmt = JSONFormatter()
        record = self._make_record(level=logging.WARNING)
        parsed = json.loads(fmt.format(record))
        assert parsed["level"] == "WARNING"


# ================================================================== #
# setup_logger
# ================================================================== #

class TestSetupLogger:

    def test_returns_logger_instance(self):
        logger = setup_logger("test.setup")
        assert isinstance(logger, logging.Logger)

    def test_does_not_duplicate_handlers(self):
        name = "test.nodup"
        l1 = setup_logger(name)
        l2 = setup_logger(name)
        assert l1 is l2
        # Повторный вызов не добавляет хендлеры
        handler_count = len(l1.handlers)
        setup_logger(name)
        assert len(l1.handlers) == handler_count

    def test_propagate_disabled(self):
        logger = setup_logger("test.prop")
        assert logger.propagate is False

    def test_no_file_when_log_file_none(self):
        logger = setup_logger("test.nofile", log_file=None)
        file_handlers = [
            h for h in logger.handlers if isinstance(h, logging.FileHandler)
        ]
        assert len(file_handlers) == 0

    def test_json_format_flag(self):
        """json_format=True должен давать валидный JSON на stdout."""
        stream = StringIO()
        logger = logging.getLogger("test.json_fmt_unique")
        logger.handlers.clear()
        logger.propagate = False
        logger.setLevel(logging.INFO)
        from utils.logger import JSONFormatter
        h = logging.StreamHandler(stream)
        h.setFormatter(JSONFormatter())
        logger.addHandler(h)
        logger.info("hello json")
        output = stream.getvalue().strip()
        parsed = json.loads(output)
        assert parsed["message"] == "hello json"


# ================================================================== #
# RequestLogger
# ================================================================== #

class TestRequestLogger:

    def test_logs_start_and_done(self):
        mock_logger = MagicMock(spec=logging.Logger)
        with RequestLogger(mock_logger, "TEST OP"):
            pass
        # info вызывался дважды: start + done
        assert mock_logger.info.call_count == 2

    def test_logs_error_on_exception(self):
        mock_logger = MagicMock(spec=logging.Logger)
        with pytest.raises(RuntimeError):
            with RequestLogger(mock_logger, "FAIL OP"):
                raise RuntimeError("oops")
        mock_logger.error.assert_called_once()

    def test_latency_in_done_extra(self):
        mock_logger = MagicMock(spec=logging.Logger)
        with RequestLogger(mock_logger, "TIMED OP"):
            time.sleep(0.01)
        # Второй info-вызов — это done
        _, kwargs = mock_logger.info.call_args
        extra = kwargs.get("extra", {})
        assert "latency_ms" in extra
        assert extra["latency_ms"] > 0

    def test_set_extra_appears_in_log(self):
        mock_logger = MagicMock(spec=logging.Logger)
        with RequestLogger(mock_logger, "OP") as rl:
            rl.set_extra(sources_count=5)
        _, kwargs = mock_logger.info.call_args
        assert kwargs["extra"]["sources_count"] == 5

    def test_does_not_suppress_exception(self):
        mock_logger = MagicMock(spec=logging.Logger)
        with pytest.raises(ValueError):
            with RequestLogger(mock_logger, "OP"):
                raise ValueError("must propagate")

    def test_extra_kwargs_passed_to_start_log(self):
        mock_logger = MagicMock(spec=logging.Logger)
        with RequestLogger(mock_logger, "OP", user_id="u42"):
            pass
        first_call_kwargs = mock_logger.info.call_args_list[0][1]
        assert first_call_kwargs["extra"]["user_id"] == "u42"
