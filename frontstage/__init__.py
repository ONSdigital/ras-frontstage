import logging
import os

from flask import Flask
from flask_wtf.csrf import CSRFProtect
from structlog import wrap_logger

from frontstage.exceptions.exceptions import MissingEnvironmentVariable
from frontstage.filters.file_size_filter import file_size_filter
from frontstage.logger_config import logger_initial_config


app = Flask(__name__)

app_config = 'config.{}'.format(os.environ.get('APP_SETTINGS', 'Config'))
app.config.from_object(app_config)

log_level = 'DEBUG' if app.config['DEBUG'] else None
logger_initial_config(service_name='ras-frontstage', log_level=log_level)
logger = wrap_logger(logging.getLogger(__name__))
logger.debug('{} used'.format(str(app_config)))

for var in app.config['NON_DEFAULT_VARIABLES']:
    if not app.config[var]:
        raise MissingEnvironmentVariable(app, logger)

app.url_map.strict_slashes = False

csrf = CSRFProtect(app)

app.jinja_env.filters['file_size_filter'] = file_size_filter


@app.after_request
def apply_caching(response):
    response.headers["X-Frame-Options"] = "DENY"
    return response

import frontstage.views  # NOQA  # pylint: disable=wrong-import-position
import frontstage.error_handlers  # NOQA  # pylint: disable=wrong-import-position
