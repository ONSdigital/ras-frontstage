import json
import logging
import unittest
from datetime import datetime, timezone

from freezegun import freeze_time
from structlog import wrap_logger

from frontstage.logger_config import logger_initial_config

TIME_TO_FREEZE = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

EXPECTED_ERROR_OUTPUT = json.dumps(
    {
        "event": "Test error",
        "severity": "error",
        "service": "ras-frontstage",
        "created_at": "2023-01-01T12:001672574400",
    }
)
EXPECTED_INFO_OUTPUT = json.dumps(
    {
        "additional_key": "additional_value",
        "event": "Test info",
        "severity": "info",
        "service": "ras-frontstage",
        "created_at": "2023-01-01T12:001672574400",
    }
)
EXPECTED_WARN_OUTPUT = json.dumps(
    {
        "event": "Test warn",
        "severity": "warning",
        "service": "ras-frontstage",
        "created_at": "2023-01-01T12:001672574400",
    }
)


class TestLoggerConfig(unittest.TestCase):
    @freeze_time(TIME_TO_FREEZE)
    def test_level_info(self):
        logs = self._get_logs("INFO")

        self.assertEqual(len(logs.output), 3)
        self.assertEqual(EXPECTED_ERROR_OUTPUT, logs[0][0].msg)
        self.assertEqual(EXPECTED_WARN_OUTPUT, logs[0][1].msg)
        self.assertEqual(EXPECTED_INFO_OUTPUT, logs[0][2].msg)

    @freeze_time(TIME_TO_FREEZE)
    def test_level_warn(self):
        logs = self._get_logs("WARN")

        self.assertEqual(len(logs.output), 2)
        self.assertEqual(EXPECTED_ERROR_OUTPUT, logs[0][0].msg)
        self.assertEqual(EXPECTED_WARN_OUTPUT, logs[0][1].msg)

    @freeze_time(TIME_TO_FREEZE)
    def test_level_error(self):
        logs = self._get_logs("ERROR")

        self.assertEqual(len(logs.output), 1)
        self.assertEqual(EXPECTED_ERROR_OUTPUT, logs[0][0].msg)

    def test_exception(self):
        logger_initial_config("INFO")
        logger = wrap_logger(logging.getLogger())

        with self.assertLogs() as logs:
            try:
                raise GenerateException("test exception for logging")
            except GenerateException:
                logger.error("Test error", exc_info=True)

        self.assertIn("GenerateException('test exception for logging'", logs[0][0].msg)

    def _get_logs(self, log_level):
        logger_initial_config(log_level)
        logger = wrap_logger(logging.getLogger())
        with self.assertLogs() as logs:
            logger.error("Test error")
            logger.warn("Test warn")
            logger.info("Test info", additional_key="additional_value")
        return logs


class GenerateException(Exception):
    def __init__(self, message):
        self.message = message
