import logging
import os

from flask import Flask
from structlog import wrap_logger

from frontstage.filters.case_status_filter import case_status_filter
from frontstage.filters.file_size_filter import file_size_filter
from frontstage.logger_config import logger_initial_config


app = Flask(__name__)

app_config = os.environ.get('APP_SETTINGS', 'config.DevelopmentConfig')
app.config.from_object(app_config)

app.url_map.strict_slashes = False

app.jinja_env.filters['case_status_filter'] = case_status_filter
app.jinja_env.filters['file_size_filter'] = file_size_filter

log_level = None
if app.config['DEBUG']:
    log_level = 'DEBUG'

logger_initial_config(service_name='ras-frontstage', log_level=log_level)
logger = wrap_logger(logging.getLogger(__name__))

import frontstage.views
import frontstage.error_handlers
