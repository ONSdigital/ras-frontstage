import logging
import unittest

from structlog import wrap_logger

from frontstage.logger_config import logger_initial_config


class TestLoggerConfig(unittest.TestCase):
    def test_indent_type_error(self):
        logger_initial_config()
        logger = wrap_logger(logging.getLogger())
        with self.assertLogs(level="ERROR") as cm:
            logger.error("Test")
        message = cm[0][0].msg
        self.assertIn('"event": "Test", "severity": "error",' ' "level": "error", "service": "ras-frontstage"', message)
