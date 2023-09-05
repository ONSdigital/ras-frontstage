import logging

import fakeredis
import redis
from flask import render_template
from flask_talisman import Talisman
from jinja2 import ChainableUndefined
from structlog import wrap_logger

from frontstage.common.jinja_filters import filter_blueprint
from frontstage.controllers.banner_controller import current_banner
from frontstage.create_app import create_app_object

logger = wrap_logger(logging.getLogger(__name__))

CSP_POLICY = {
    "default-src": ["'self'", "https://cdn.ons.gov.uk"],
    "font-src": ["'self'", "data:", "https://fonts.gstatic.com", "https://cdn.ons.gov.uk"],
    "script-src": ["'self'", "https://www.googletagmanager.com", "https://cdn.ons.gov.uk", "unsafe-eval"],
    "connect-src": [
        "'self'",
        "https://*.google-analytics.com",
        "https://*.analytics.google.com",
        "https://*.googletagmanager.com",
    ],
    "img-src": [
        "'self'",
        "data:",
        "https://www.gstatic.com",
        "https://www.google-analytics.com",
        "https://www.googletagmanager.com",
        "https://ssl.gstatic.com",
        "https://cdn.ons.gov.uk",
    ],
    "style-src": [
        "'self'",
        "https://cdn.ons.gov.uk",
        "'unsafe-inline'",
        "https://tagmanager.google.com",
        "https://fonts.googleapis.com",
    ],
}

app = create_app_object()

talisman = Talisman(
    app,
    content_security_policy=CSP_POLICY,
    content_security_policy_nonce_in=["script-src"],
    force_https=app.config["SECURE_APP"],
    strict_transport_security=True,
    strict_transport_security_max_age=31536000,
    frame_options="DENY",
)

if not app.config["TESTING"]:
    redis = redis.Redis(host=app.config["REDIS_HOST"], port=app.config["REDIS_PORT"], db=app.config["REDIS_DB"])
    logger.info("Using real redis")
else:
    redis = fakeredis.FakeRedis()
    logger.info("Using fakeredis")

app.jinja_env.undefined = ChainableUndefined
app.jinja_env.add_extension("jinja2.ext.do")

app.register_blueprint(filter_blueprint)


@app.context_processor
def inject_availability_message():
    banner = current_banner()
    if banner:
        return {"availability_message": banner}
    return {}


import frontstage.error_handlers  # NOQA

# Bind routes to app
import frontstage.views  # NOQA


@app.before_request
def redirect_to_maintenance_page():
    if app.config["UNDER_MAINTENANCE"]:
        return render_template("maintenance_page.html")
