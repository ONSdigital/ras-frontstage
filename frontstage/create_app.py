import logging
import os
import requestsdefaulter
import copy

from flask import Flask, request
from flask_zipkin import Zipkin
from structlog import wrap_logger
from flask_talisman import Talisman

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

# TODO: review https://content-security-policy.com/, remove this comment if we're covered.
CSP_POLICY = {
    'default-src': ["'self'", 'https://cdn.ons.gov.uk'],
    'font-src': ["'self'", 'data:', 'https://fonts.gstatic.com', 'https://cdn.ons.gov.uk'],
    'script-src': ["'self'", 'https://www.googletagmanager.com', 'https://cdn.ons.gov.uk'],
    'connect-src': ["'self'", 'https://www.googletagmanager.com', 'https://tagmanager.google.com', 'https://cdn.ons.gov.uk'],
    'img-src': ["'self'", 'data:', 'https://www.gstatic.com', 'https://www.google-analytics.com',
                'https://www.googletagmanager.com', 'https://ssl.gstatic.com', 'https://cdn.ons.gov.uk'],
    'style-src': ["'self'", 'https://cdn.ons.gov.uk', "'unsafe-inline'", 'https://tagmanager.google.com', 'https://fonts.googleapis.com'],
}


class GCPLoadBalancer:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        scheme = environ.get("HTTP_X_FORWARDED_PROTO", "http")
        if scheme:
            environ["wsgi.url_scheme"] = scheme
        return self.app(environ, start_response)


def create_app_object():
    csp_policy = copy.deepcopy(CSP_POLICY)
    app = Flask(__name__)
    Talisman(
        app,
        content_security_policy=csp_policy,
        content_security_policy_nonce_in=['script-src'],
        force_https=False,  # this is handled at the firewall
        strict_transport_security=True,
        strict_transport_security_max_age=31536000,
        frame_options='DENY')
    app.name = "ras-frontstage"

    # Load app config
    app_config = 'config.{}'.format(os.environ.get('APP_SETTINGS', 'Config'))
    app.config.from_object(app_config)

    if not app.config['DEBUG'] and not cf.detected:
        app.wsgi_app = GCPLoadBalancer(app.wsgi_app)

    # Zipkin
    zipkin = Zipkin(app=app, sample_rate=app.config.get("ZIPKIN_SAMPLE_RATE"))
    requestsdefaulter.default_headers(zipkin.create_http_headers_for_new_span)

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
        if request.path.startswith('/static/'):
            return response
        response.headers["X-Frame-Options"] = "DENY"
        for k, v in CACHE_HEADERS.items():
            response.headers[k] = v
        return response

    return app
