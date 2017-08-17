import logging
import os


def logger_initial_config(service_name=None,
                          log_level=None,
                          logger_format=None,
                          logger_date_format=None):
    '''Set initial logger config'''

    if not log_level:
        log_level = os.getenv('SMS_LOG_LEVEL', 'INFO')
    if not logger_format:
        logger_format = (
            "level='%(levelname)s' service='{}' created=%(asctime)s.%(msecs)06dZ | "
            "%(message)s file='%(name)s.%(funcName)s' line_no=%(lineno)d").format(service_name)
    if not logger_date_format:
        logger_date_format = os.getenv('LOGGING_DATE_FORMAT', "%Y-%m-%dT%H:%M%s")

    logging.basicConfig(level=log_level,
                        format=logger_format,
                        datefmt=logger_date_format)
