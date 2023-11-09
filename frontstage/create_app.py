import logging
import os

from flask import Flask, request
from flask_wtf.csrf import CSRFProtect
from structlog import wrap_logger

from frontstage.exceptions.exceptions import MissingEnvironmentVariable
from frontstage.filters.file_size_filter import file_size_filter
from frontstage.filters.subject_filter import subject_filter
from frontstage.logger_config import logger_initial_config

CACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
}


class GCPLoadBalancer:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        scheme = os.environ.get("SCHEME", "http")
        if scheme:
            environ["wsgi.url_scheme"] = scheme
        return self.app(environ, start_response)


def create_app_object():
    app = Flask(__name__)

    # Load app config
    app_config = "config.{}".format(os.environ.get("APP_SETTINGS", "Config"))
    app.config.from_object(app_config)

    app.name = "ras-frontstage"

    if not app.config["DEBUG"]:
        app.wsgi_app = GCPLoadBalancer(app.wsgi_app)

    # Configure logger
    logger_initial_config(log_level=app.config["LOGGING_LEVEL"])
    logger = wrap_logger(logging.getLogger(__name__))
    logger.debug("App configuration set", config=app_config)

    # If any required variables are not set abort launch
    for var in app.config["NON_DEFAULT_VARIABLES"]:
        if not app.config[var]:
            raise MissingEnvironmentVariable(app, logger)

    app.url_map.strict_slashes = False

    app.jinja_env.filters["file_size_filter"] = file_size_filter
    app.jinja_env.filters["subject_filter"] = subject_filter

    csrf = CSRFProtect(app)
    csrf.exempt("frontstage.views.session.session_refresh_expires_at")

    @app.after_request
    def apply_headers(response):
        if request.path.startswith("/static/"):
            return response
        response.headers["X-Frame-Options"] = "DENY"
        for k, v in CACHE_HEADERS.items():
            response.headers[k] = v
        return response

    return app
