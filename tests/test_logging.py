import unittest
from app.logger_config import logger_initial_config
from unittest import mock


class LoggingTestCase(unittest.TestCase):
    """Test case for logging"""

    def test_basic_logger_config(self):
        """Test logger configuration"""
        with mock.patch('logging.basicConfig') as loggingConfig:
            logger_initial_config(service_name='ras-secure-message', log_level='INFO', logger_format="message", logger_date_format='2017-06-13')
            loggingConfig.assert_called_with(level='INFO', format="message", datefmt='2017-06-13')

if __name__ == '__main__':
    unittest.main()
