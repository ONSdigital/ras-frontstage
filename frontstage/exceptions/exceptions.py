import logging

from structlog import wrap_logger


logger = wrap_logger(logging.getLogger(__name__))


class ExternalServiceError(Exception):
    def __init__(self, response):
        self.url = response.url
        self.status_code = response.status_code
