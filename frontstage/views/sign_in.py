import logging
from os import getenv

from flask import Blueprint, make_response, render_template, request, redirect, url_for
from oauthlib.oauth2 import LegacyApplicationClient, MissingTokenError
import requests
from requests_oauthlib import OAuth2Session
from structlog import wrap_logger
import json
from frontstage import app
from frontstage.exceptions.exceptions import ExternalServiceError
from frontstage.jwt import encode, timestamp_token
from frontstage.models import LoginForm


logger = wrap_logger(logging.getLogger(__name__))

sign_in_bp = Blueprint('sign_in_bp', __name__, static_folder='static', template_folder='frontstage/templates/sign-in')


# ===== Sign in using OAuth2 =====
@sign_in_bp.route('/', methods=['GET', 'POST'])
def login():
    """Handles sign in using OAuth2"""
    form = LoginForm(request.form)
    account_activated = request.args.get('account_activated', None)

    if request.method == 'POST' and form.validate():
        username = request.form.get('username')
        password = request.form.get('password')

        # TODO Consider moving this to a helper function.
        # Lets get a token from the OAuth2 server
        try:
            token_url = app.config['ONS_OAUTH_PROTOCOL'] + app.config['ONS_OAUTH_SERVER'] + app.config['ONS_TOKEN_ENDPOINT']
            data = {
                'grant_type': 'password',
                'client_id': app.config['RAS_FRONTSTAGE_CLIENT_ID'],
                'client_secret': app.config['RAS_FRONTSTAGE_CLIENT_SECRET'],
                'username': username,
                'password': password,
            }
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            }

            oauth2_response = requests.post(url=token_url, data=data, headers=headers, auth=(app.config['RAS_FRONTSTAGE_CLIENT_ID'],
                                                                                              app.config['RAS_FRONTSTAGE_CLIENT_SECRET']))
            # Check to see that this user has not attempted to login too many times or that they have not forgot to
            # click on the activate account URL in their email by checking the error message back from the OAuth2 server
            if oauth2_response.status_code == 401:
                oauth2Error = json.loads(oauth2_response.text)
                if 'Unauthorized user credentials' in oauth2Error['detail']:
                    return render_template('sign-in/sign-in.html', _theme='default', form=form, data={"error": {"type": "failed"}})
                elif 'User account locked' in oauth2Error['detail']:
                    logger.warning('User account is locked on the OAuth2 server')
                    return render_template('sign-in/sign-in.trouble.html', _theme='default', form=form,
                                           data={"error": {"type": "account locked"}})
                elif 'User account not verified' in oauth2Error['detail']:
                    logger.warning('User account is not verified on the OAuth2 server')
                    return render_template('sign-in/sign-in.account-not-verified.html', _theme='default', form=form,
                                           data={"error": {"type": "account not verified"}})
                else:
                    logger.error('OAuth 2 server generated 401 which is not understood', oauth2error=oauth2Error['detail'])
                    return render_template('sign-in/sign-in.html', _theme='default', form=form,
                                           data={"error": {"type": "failed"}})
            if oauth2_response.status_code != 201:
                logger.error('Unknown error from the OAuth2 server')
                raise ExternalServiceError(oauth2_response)
            logger.debug('Access Token Granted')
        except requests.ConnectionError as e:
            logger.warning('Connection error between the server and the OAuth2 service of: {}'.format(exception=str(e)))
            raise ExternalServiceError(e)
        oauth2_token = json.loads(oauth2_response.text)

        url = app.config['RAS_PARTY_GET_BY_EMAIL'].format(app.config['RAS_PARTY_SERVICE'], username)
        req = requests.get(url, verify=False)
        if req.status_code == 404:
            logger.error('Email not found in party service', email=username)
            return render_template('sign-in/sign-in.html', _theme='default',
                                   form=form, data={"error": {"type": "failed"}})
        elif req.status_code != 200:
            logger.error('Error retrieving respondent from party service', email=username)
            raise ExternalServiceError(req)
        party_id = req.json().get('id')

        # Take our raw token and add a UTC timestamp to the expires_at attribute
        data_dict_for_jwt_token = timestamp_token(oauth2_token, username, party_id)
        encoded_jwt_token = encode(data_dict_for_jwt_token)
        response = make_response(redirect(url_for('surveys_bp.logged_in', _external=True,
                                                  _scheme=getenv('SCHEME', 'http'))))
        response.set_cookie('authorization', value=encoded_jwt_token)
        return response

    template_data = {
        "error": {
            "type": form.errors,
            "logged_in": "False"
        },
        'account_activated': account_activated
    }

    return render_template('sign-in/sign-in.html', _theme='default', form=form, data=template_data)

  
@sign_in_bp.route('/logout')
def logout():
    response = make_response(redirect(url_for('sign_in_bp.login')))
    response.set_cookie('authorization', value='', expires=0)
    return response
