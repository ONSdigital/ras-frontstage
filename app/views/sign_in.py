import os
import logging
from flask import Flask, Blueprint, make_response, render_template, request, redirect, url_for
from structlog import wrap_logger
from oauthlib.oauth2 import LegacyApplicationClient, MissingTokenError
from requests_oauthlib import OAuth2Session
from app.config import Config
from app.jwt import encode
from app.models import LoginForm

app = Flask(__name__)
app.debug = True

app.config.update(
    DEBUG=True,
    TESTING=True,
    TEMPLATES_AUTO_RELOAD=True
)

if 'APP_SETTINGS' in os.environ:
    app.config.from_object(Config)

logger = wrap_logger(logging.getLogger(__name__))
sign_in_bp = Blueprint('sign_in_bp', __name__, static_folder='static', template_folder='templates/sign-in')


# ===== Sign in using OAuth2 =====
@sign_in_bp.route('/', methods=['GET', 'POST'])
def login():
    """Handles sign in using OAuth2"""

    logger.debug("*** Hitting login for OAuth() function.... ***")
    """ Login OAuth Page.
    This function uses the OAuth 2 server to receive a token upon successful sign in. If the user presents the correct
    password and username and is accepted by the OAuth 2 server we receive an access token, a refresh token and a TTL.
    Otherwise we fail.
    This uses the flow Resource Owner Password Credentials Grant. See: https://tools.ietf.org/html/rfc6749#section-4.3
    To make this work the server application (thats us!) needs a client ID and a client secret. This has to exist on the
    OAuth server. We then use Basic Auth to access the OAuth2 server and provide the user ID, and user password in the
    POST Body message. In the real world this would be done over https - for now all this works over http since it is
    behind our firewall.
    Parms_to_OAuth:
        client_id
        client_secret
        user_id
        user_password
        oauth2_url
    Returned_from_OAuth:
        access_token
        refresh_token
        ttl
    """
    form = LoginForm(request.form)

    account_activated = request.args.get('account_activated', None)

    if request.method == 'POST' and form.validate():
        username = request.form.get('username')
        password = request.form.get('password')
        logger.debug("Username is: {}".format(username))
        logger.debug("Password is: {}".format(password))

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

            app.logger.debug(" *** Access Token Granted *** ")
            app.logger.debug(" Values are: ")
            for key in token:
                logger.debug("{} Value is: {}".format(key, token[key]))

        except MissingTokenError as e:
            logger.warning("Missing token error, error is: {}".format(e))
            logger.warning("Failed validation")
            return render_template('sign-in/sign-in.html', _theme='default', form=form, data={"error": {"type": "failed"}})

 #       except Exception as e:
 #           logger.error("Error logging in: {}", str(e))
 #           return redirect(url_for('error_page'))

        data_dict_for_jwt_token = {
            "refresh_token": token['refresh_token'],
            "access_token": token['access_token'],
            "scope": token['scope'],
            "expires_at": token['expires_at'],
            "username": username,
            "user_uuid": "ce12b958-2a5f-44f4-a6da-861e59070a32",
            "role": "respondent",
            "party_id": "db036fd7-ce17-40c2-a8fc-932e7c228397"
        }

        encoded_jwt_token = encode(data_dict_for_jwt_token)
        response = make_response(redirect(url_for('surveys_bp.logged_in')))
        logger.info('Encoded JWT {}'.format(encoded_jwt_token))
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


@sign_in_bp.route('/sign-in/error', methods=['GET'])
def sign_in_error():
    """Handles any sign in errors"""

    template_data = {
        "error": {
            "type": "failed"
        }
    }

    # data variables configured: {"error": <undefined, failed, last-attempt>}
    return render_template('sign-in/sign-in.html', _theme='default', data=template_data)


@sign_in_bp.route('/sign-in/troubleshoot')
def sign_in_troubleshoot():
    return render_template('sign-in/sign-in.trouble.html', _theme='default')


@sign_in_bp.route('/sign-in/final-sign-in')
def sign_in_last_attempt():
    return render_template('sign-in/sign-in.last-attempt.html', _theme='default')


@sign_in_bp.route('/sign-in/account-locked/')
def sign_in_account_locked():
    return render_template('sign-in/sign-in.locked-account.html', _theme='default')
