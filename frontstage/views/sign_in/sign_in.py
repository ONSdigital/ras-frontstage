import json
import logging
from os import getenv

from flask import make_response, render_template, redirect, request, url_for
from structlog import wrap_logger

from frontstage import app
from frontstage.common.api_call import api_call
from frontstage.common.session import SessionHandler
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
        response = api_call('POST', app.config['SIGN_IN_URL'], json=sign_in_data)

        # Handle OAuth2 authentication errors
        if response.status_code == 401:
            error_json = json.loads(response.text).get('error')
            error_message = error_json.get('data', {}).get('detail')
            if 'Unauthorized user credentials' in error_message:
                return render_template('sign-in/sign-in.html', form=form, data={"error": {"type": "failed"}})
            elif 'User account locked' in error_message:
                logger.debug('User account is locked on the OAuth2 server')
                return render_template('sign-in/sign-in.trouble.html', form=form, data={"error": {"type": "account locked"}})
            elif 'User account not verified' in error_message:
                logger.debug('User account is not verified on the OAuth2 server')
                return render_template('sign-in/sign-in.account-not-verified.html',
                                       form=form,
                                       data={"error": {"type": "account not verified"}})
            else:
                logger.error('OAuth 2 server generated 401 which is not understood',
                             oauth2error=error_message)
                return render_template('sign-in/sign-in.html', form=form, data={"error": {"type": "failed"}})

        if response.status_code != 200:
            logger.error('Failed to sign in')
            raise ApiError(response)

        # Take our raw token and add a UTC timestamp to the expires_at attribute
        response_json = json.loads(response.text)
        data_dict_for_jwt_token = timestamp_token(response_json)
        encoded_jwt_token = encode(data_dict_for_jwt_token)
        response = make_response(redirect(url_for('surveys_bp.logged_in', _external=True,
                                                  _scheme=getenv('SCHEME', 'http'))))

        session = SessionHandler()
        logger.info('Creating session', party_id=response_json['party_id'])
        session.create_session(encoded_jwt_token)
        response.set_cookie('authorization',
                            value=session.session_key,
                            expires=data_dict_for_jwt_token['expires_at'])
        logger.info('Successfully created session', party_id=response_json['party_id'],
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
