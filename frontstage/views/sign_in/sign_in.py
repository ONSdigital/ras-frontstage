import json
import logging
from os import getenv

from flask import make_response, render_template, redirect, request, url_for
from structlog import wrap_logger

from frontstage import app
from frontstage.common.api_call import api_call
from frontstage.common.session import SessionHandler
from frontstage.controllers import party_controller
from frontstage.exceptions.exceptions import ApiError
from frontstage.jwt import encode, timestamp_token
from frontstage.models import LoginForm
from frontstage.views.sign_in import sign_in_bp


logger = wrap_logger(logging.getLogger(__name__))


@app.route('/', methods=['GET'])
def home():
    return redirect(url_for('sign_in_bp.login', _external=True, _scheme=getenv('SCHEME', 'http')))


@sign_in_bp.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    account_activated = request.args.get('account_activated', None)

    if request.method == 'POST' and form.validate():
        username = request.form.get('username')
        password = request.form.get('password')
        sign_in_data = {
            "username": username,
            "password": password
        }

        respondent = party_controller.get_respondent_by_email(username)
        if not respondent or respondent['status'] != 'ACTIVE':
            logger.debug("Respondent not able to sign in as don't have an active account in the system.")
            return render_template('sign-in/sign-in.html', form=form, data={"error": {"type": "failed"}})

        response = api_call('POST', app.config['SIGN_IN_URL'], json=sign_in_data)

        # Handle OAuth2 authentication errors
        if response.status_code == 401:
            error_json = json.loads(response.text).get('error')
            error_message = error_json.get('data', {}).get('detail')
            if 'Unauthorized user credentials' in error_message:
                return render_template('sign-in/sign-in.html', form=form, data={"error": {"type": "failed"}})
            else:
                logger.error('OAuth 2 server generated 401 which is not understood',
                             oauth2error=error_message)
                return render_template('sign-in/sign-in.html', form=form, data={"error": {"type": "failed"}})

        if response.status_code != 200:
            logger.error('Failed to sign in')
            raise ApiError(response)

        # Take our raw token and add a UTC timestamp to the expires_at attribute
        response_json = json.loads(response.text)
        data_dict_for_jwt_token = timestamp_token(response_json, respondent)
        encoded_jwt_token = encode(data_dict_for_jwt_token)
        response = make_response(redirect(url_for('surveys_bp.logged_in', _external=True,
                                                  _scheme=getenv('SCHEME', 'http'))))

        session = SessionHandler()
        logger.info('Creating session', party_id=respondent['id'])
        session.create_session(encoded_jwt_token)
        response.set_cookie('authorization',
                            value=session.session_key,
                            expires=data_dict_for_jwt_token['expires_at'])
        logger.info('Successfully created session', party_id=respondent['id'],
                    session_key=session.session_key)
        return response

    template_data = {
        "error": {
            "type": form.errors,
            "logged_in": "False"
        },
        'account_activated': account_activated
    }
    return render_template('sign-in/sign-in.html', form=form, data=template_data)
