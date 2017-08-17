import logging
from os import getenv

from flask import Blueprint, make_response, render_template, request, redirect, url_for
from oauthlib.oauth2 import LegacyApplicationClient, MissingTokenError
import requests
from requests_oauthlib import OAuth2Session
from structlog import wrap_logger

from frontstage import app
from frontstage.exceptions.exceptions import ExternalServiceError
from frontstage.jwt import encode
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

        # Creates a 'session client' to interact with OAuth2. This provides a client ID to our client that is used to
        # interact with the server.
        client = LegacyApplicationClient(client_id=app.config['RAS_FRONTSTAGE_CLIENT_ID'])

        # Populates the request body with username and password from the user
        client.prepare_request_body(username=username, password=password, scope=['ci.write', 'ci.read'])

        # passes our 'client' to the session management object. this deals with
        # the transactions between the OAuth2 server
        oauth = OAuth2Session(client=client)
        token_url = app.config['ONS_OAUTH_PROTOCOL'] + app.config['ONS_OAUTH_SERVER'] + app.config['ONS_TOKEN_ENDPOINT']

        try:
            token = oauth.fetch_token(token_url=token_url, username=username, password=password, client_id=app.config['RAS_FRONTSTAGE_CLIENT_ID'],
                                      client_secret=app.config['RAS_FRONTSTAGE_CLIENT_SECRET'])

            logger.debug('Access Token Granted')

        except MissingTokenError as e:
            logger.warning('Missing token', exception=e)
            return render_template('sign-in/sign-in.html', _theme='default', form=form, data={"error": {"type": "failed"}})

        url = app.config['RAS_PARTY_GET_BY_EMAIL'].format(app.config['RAS_PARTY_SERVICE'], username)
        req = requests.get(url, verify=False)
        if req.status_code != 200:
            logger.error('Email not found in party service', email=username)
            raise ExternalServiceError(req)

        ##### THIS EXCEPTION CAN NEVER BE HIT??? #####
        try:
            party_id = req.json().get('id')
        except Exception as e:
            logger.error(str(e))
            logger.error('"event" : "error trying to get username from party service"')
            return render_template("error.html", _theme='default', data={"error": {"type": "failed"}})

        data_dict_for_jwt_token = {
            "refresh_token": token['refresh_token'],
            "access_token": token['access_token'],
            "scope": token['scope'],
            "expires_at": token['expires_at'],
            "username": username,
            "role": "respondent",
            "party_id": party_id
        }

        encoded_jwt_token = encode(data_dict_for_jwt_token)
        response = make_response(redirect(url_for('surveys_bp.logged_in',
                                                  _external=True,
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
