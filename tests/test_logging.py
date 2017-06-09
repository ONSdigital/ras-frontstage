import unittest
from testfixtures import log_capture
import logging
from structlog import wrap_logger
from app.logger_config import logger_initial_config


class LoggingTestCase(unittest.TestCase):
    """Test case for logging"""

    @log_capture()
    def test_logging_format(self, l):
        """Test logging is in expected format"""
        logger_initial_config(service_name='ras-frontstage')
        logger = logging.getLogger(__name__)

        logger.info('test')
        l.check(
            ('test_logging', 'INFO', 'test')
        )


if __name__ == '__main__':
    unittest.main()