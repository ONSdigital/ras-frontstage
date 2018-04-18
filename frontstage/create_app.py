import logging
import os

from flask import Flask
from structlog import wrap_logger

from frontstage.cloud.cloudfoundry import ONSCloudFoundry
from frontstage.exceptions.exceptions import MissingEnvironmentVariable
from frontstage.filters.file_size_filter import file_size_filter
from frontstage.filters.subject_filter import subject_filter
from frontstage.logger_config import logger_initial_config


cf = ONSCloudFoundry()

CACHE_HEADERS = {
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
}

def create_app_object():
    app = Flask(__name__)

    # Load app config
    app_config = 'config.{}'.format(os.environ.get('APP_SETTINGS', 'Config'))
    app.config.from_object(app_config)

    # Configure logger
    log_level = 'DEBUG' if app.config['DEBUG'] else None
    logger_initial_config(service_name='ras-frontstage', log_level=log_level)
    logger = wrap_logger(logging.getLogger(__name__))
    logger.debug('App configuration set', config=app_config)

    # If deploying in cloudfoundry set config to use cf redis instance
    if cf.detected:
        logger.info('Cloudfoundry detected, setting service configurations')
        app.config['REDIS_HOST'] = cf.redis.credentials['host']
        app.config['REDIS_PORT'] = cf.redis.credentials['port']

    # If any required variables are not set abort launch
    for var in app.config['NON_DEFAULT_VARIABLES']:
        if not app.config[var]:
            raise MissingEnvironmentVariable(app, logger)

    app.url_map.strict_slashes = False

    app.jinja_env.filters['file_size_filter'] = file_size_filter
    app.jinja_env.filters['subject_filter'] = subject_filter

    @app.after_request
    def apply_headers(response):
        response.headers["X-Frame-Options"] = "DENY"
        for k, v in CACHE_HEADERS.items():
            response.headers[k] = v
        return response

    return app
