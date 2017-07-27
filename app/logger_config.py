import logging
import os


def logger_initial_config(service_name=None,
                          log_level=None,
                          logger_format=None,
                          logger_date_format=None):
    '''Set initial logger config'''

    if not log_level:
        log_level = os.getenv('RAS_FRONTSTAGE_LOGGING_LEVEL', 'INFO')
    if not logger_format:
        logger_format = (
            "%(asctime)s.%(msecs)06dZ|"
            "%(levelname)s: {}: event='%(message)s': file='%(name)s.%(funcName)s:line no.='%(lineno)d'"
        ).format(service_name)
    if not logger_date_format:
        logger_date_format = os.getenv('LOGGING_DATE_FORMAT', "%Y-%m-%dT%H:%M%s")

    logging.basicConfig(level=log_level,
                        format=logger_format,
                        datefmt=logger_date_format)
