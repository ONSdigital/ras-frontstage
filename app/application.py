
"""
Main file that is run
"""

import logging
import os
from datetime import datetime
from functools import wraps, update_wrapper

from flask import Flask, make_response, render_template, redirect, url_for
from structlog import wrap_logger

from app.filters.case_status_filter import case_status_filter
from app.filters.file_size_filter import file_size_filter
from app.logger_config import logger_initial_config
from app.views.passwords import passwords_bp
from app.views.register import register_bp
from app.views.secure_messaging import secure_message_bp
from app.views.sign_in import sign_in_bp
from app.views.surveys import surveys_bp
from config import Config, TestingConfig, ProductionConfig

app = Flask(__name__)
app.debug = True

app.config.update(
    DEBUG=True,
    TESTING=True,
    TEMPLATES_AUTO_RELOAD=True
)

app.jinja_env.filters['case_status_filter'] = case_status_filter
app.jinja_env.filters['file_size_filter'] = file_size_filter

logger_initial_config(service_name='ras-frontstage')

logger = wrap_logger(logging.getLogger(__name__))

app.register_blueprint(passwords_bp, url_prefix='/passwords')
app.register_blueprint(register_bp, url_prefix='/register')
app.register_blueprint(sign_in_bp, url_prefix='/sign-in')
app.register_blueprint(surveys_bp, url_prefix='/surveys')
app.register_blueprint(secure_message_bp, url_prefix='/secure-message')

if 'APP_SETTINGS' in os.environ:
    # app.config.from_object(os.environ['APP_SETTINGS'])
    app.config.from_object(Config)

# If our PRODUCTION_VERSION environment variable is set as true (this should be set in our manifest.yml file in the root
# folder.) we will use those settings. If not we will default to our TEST settings.
if 'PRODUCTION_VERSION' in os.environ:
    logger.info(" *** Production server settings are being used. ***")
    app.config.from_object(ProductionConfig)
else:
    logger.info(" *** APP.Info Testing server settings are being used. ***")
    app.config.from_object(TestingConfig)
    logger.info("testing server started...")


# TODO Remove this before production
@app.route('/home', methods=['GET', 'POST'])
def hello_world():
    return render_template('_DEV_ONLY_HOME_PAGE.html', _theme='default')


@app.route('/error', methods=['GET', 'POST'])
def error_page():
    response = make_response(render_template('error.html', _theme='default', data={"error": {"type": "failed"}}))
    response.set_cookie('authorization', value='', expires=0)
    return response


# ===== Log out =====
@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('sign_in_bp.login')))
    response.set_cookie('authorization', value='', expires=0)
    return response


# ===== Messages =====
@app.route('/messages')
def messages():
    return render('messages.html')


# Disable cache for development
def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response

    return update_wrapper(no_cache, view)


def render(template):
    return render_template(template, _theme='default')
