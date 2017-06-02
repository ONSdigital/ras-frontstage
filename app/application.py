"""
Main file that is ran
"""
from functools import wraps, update_wrapper
from datetime import datetime
import logging
import sys
import os
import requests
from requests import ConnectionError
from flask import Flask, make_response, render_template, request, flash, redirect, url_for, session, Response, abort, Blueprint, current_app
from oauthlib.oauth2 import LegacyApplicationClient, BackendApplicationClient, MissingTokenError
from requests_oauthlib import OAuth2Session
import json
from jwt import encode, decode
from jose import JWTError
from config import OAuthConfig, PartyService, Config, FrontstageLogging
from models import LoginForm, User, RegistrationForm, ActivationCodeForm, db
from utils import get_user_scopes_util


frontstage = Blueprint('frontstage', __name__, static_folder='static', template_folder='templates')
current_app.debug = True

if 'APP_SETTINGS' in os.environ:
    # app.config.from_object(os.environ['APP_SETTINGS'])
    current_app.config.from_object(Config)

db.init_app(current_app)


# TODO Remove this before production
@frontstage.route('/')
@frontstage.route('/home', methods=['GET', 'POST'])
def hello_world():
    return render_template('_temp.html', _theme='default')


@frontstage.route('/')
@frontstage.route('/logged-in', methods=['GET', 'POST'])
def logged_in():
    """Logged in page for users only."""

    if session.get('jwt_token'):
        jwttoken = session.get('jwt_token')

        try:
            decodedJWT = decode(jwttoken)
            for key in decodedJWT:
                current_app.logger.debug(" {} is: {}".format(key, decodedJWT[key]))
                # userID = decodedJWT['user_id']
            return render_template('signed-in.html', _theme='default', data={"error": {"type": "success"}})

        except JWTError:
            # TODO Provide proper logging
            current_app.logger.debug("This is not a valid JWT Token")
            # app.logger.warning('JWT scope could not be validated.')
            # Make sure we pop this invalid session variable.
            session.pop('jwt_token')

    return render_template('signed-in.html', _theme='default', data={"error": {"type": "failed"}})


@frontstage.route('/protected/collectioninstrument', methods=['GET'])
def protected_collection():
    """Protected method to return full list of collectioninstrument json."""
    if session.get('jwt_token'):
        jwttoken = session.get('jwt_token')

        decodedJWT = decode(jwttoken)
        userID = decodedJWT['user_id']

        try:
            user_object = User.query.filter_by(username=userID).first()
            # Check the tokens are the same
            # TODO Check the token has not expired
            if user_object.token == jwttoken:

                headers = {'authorization': jwttoken}
                url = 'localhost:5000/collectioninstrument'
                req = requests.get(url,  headers=headers)
                data = req.json()
                current_app.logger.debug(data)
                res = Response(response=data, status=200, mimetype="application/json")
                return res

            res = Response(response="""Your session is stale, try logging in again to
                                     refresh your session variables""", status=404, mimetype="text/html")
            return res
        except:
            res = Response(response="""Looks like you are not a valid user,
                           try logging in again and refresh your session""", status=404, mimetype="text/html")
            return res


@frontstage.route('/logout')
def logout():
    if 'jwt_token' in session:
        session.pop('jwt_token')

    return redirect(url_for('login_OAuth'))


# ===== Sign in =====
@frontstage.route('/sign-in/', methods=['GET', 'POST'])
def login():
    """Handles sign-in"""

    current_app.logger.debug("*** Hitting login() function.... ***")
    """Login Page."""
    form = LoginForm(request.form)

    if request.method == 'POST' and form.validate():
        username = request.form.get('username')
        password = request.form.get('password')
        current_app.logger.debug("Username is: {}".format(username))
        current_app.logger.debug("Password is: {}".format(password))

        existing_user = User.query.filter_by(username=username).first()

        if not (existing_user and existing_user.check_password_simple(password)):
            flash('Invalid username or password. Please try again.', 'danger')
            current_app.logger.debug("Failed validation")
            return render_template('sign-in.html', _theme='default', form=form, data={"error": {"type": "failed"}})

        session['username'] = username

        usr_scopes = get_user_scopes_util(username)

        data_dict_for_jwt_token = {"username": username, "user_scopes": usr_scopes}

        encoded_jwt_token = encode(data_dict_for_jwt_token)
        session['jwt_token'] = encoded_jwt_token

        flash('You have successfully logged in.', 'success')
        current_app.logger.debug("validation OK")
        return redirect(url_for('logged_in'))

    if form.errors:
        flash(form.errors, 'danger')

    templateData = {
        "error": {
            "type": request.args.get("error")
        }
    }

    return render_template('sign-in.html', _theme='default', form=form, data=templateData)


# ===== Sign in using OAuth2 =====
@frontstage.route('/sign-in/OAuth', methods=['GET', 'POST'])
def login_OAuth():
    """Handles sign in using OAuth2"""

    current_app.logger.debug("*** Hitting login for OAuth() function.... ***")
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

    if request.method == 'POST' and form.validate():
        username = request.form.get('username')
        password = request.form.get('password')
        current_app.logger.debug("Username is: {}".format(username))
        current_app.logger.debug("Password is: {}".format(password))

        # Creates a 'session client' to interact with OAuth2. This provides a client ID to our client that is used to
        # interact with the server.
        client = LegacyApplicationClient(client_id=OAuthConfig.RAS_FRONTSTAGE_CLIENT_ID)

        # Populates the request body with username and password from the user
        client.prepare_request_body(username=username, password=password, scope=['ci.write', 'ci.read'])

        # passes our 'client' to the session management object. this deals with the transactions between the OAuth2 server
        oauth = OAuth2Session(client=client)
        token_url = OAuthConfig.ONS_OAUTH_PROTOCOL + OAuthConfig.ONS_OAUTH_SERVER + OAuthConfig.ONS_TOKEN_ENDPOINT

        try:
            token = oauth.fetch_token(token_url=token_url, username=username, password=password, client_id=OAuthConfig.RAS_FRONTSTAGE_CLIENT_ID, client_secret=OAuthConfig.RAS_FRONTSTAGE_CLIENT_SECRET)
            current_app.logger.debug(" *** Access Token Granted *** ")
            current_app.logger.debug(" Values are: ")
            for key in token:
                current_app.logger.debug(key, " Value is: ", token[key])
        except MissingTokenError as e:
            current_app.logger.warning("Missing token error, error is: {}".format(e))
            current_app.logger.warning("Failed validation")
        current_app.logger.debug("Our Token Endpoint is: {}".format(token_url))

        try:
            token = oauth.fetch_token(token_url=token_url, username=username, password=password, client_id=OAuthConfig.RAS_FRONTSTAGE_CLIENT_ID, client_secret=OAuthConfig.RAS_FRONTSTAGE_CLIENT_SECRET)
            current_app.logger.debug(" *** Access Token Granted *** ")
            current_app.logger.debug(" Values are: ")
            for key in token:
                current_app.logger.debug("{} Value is: {}".format(key, token[key]))
        except MissingTokenError as e:
            current_app.logger.warning("Missing token error, error is: {}".format(e))
            current_app.logger.warning("Failed validation")
            return render_template('sign-in-oauth.html', _theme='default', form=form, data={"error": {"type": "failed"}})

        data_dict_for_jwt_token = {"refresh_token": token['refresh_token'],
                                   "access_token": token['access_token'],
                                   "scope": token['scope'],
                                   "expires_at": token['expires_at'],
                                   "username": username }

        encoded_jwt_token = encode(data_dict_for_jwt_token)
        session['jwt_token'] = encoded_jwt_token
        return redirect(url_for('logged_in'))

    templateData = {
        "error": {
            "type": request.args.get("error")
        }
    }

    return render_template('sign-in-oauth.html', _theme='default', form=form, data=templateData)


@frontstage.route('/sign-in/error', methods=['GET'])
def sign_in_error():
    """Handles any sign in errors"""

    password = request.form.get('pass')
    password = request.form.get('emailaddress')

    templateData = {
        "error": {
            "type": "failed"
        }
    }

    # data variables configured: {"error": <undefined, failed, last-attempt>}
    return render_template('sign-in.html', _theme='default', data=templateData)


@frontstage.route('/sign-in/troubleshoot')
def sign_in_troubleshoot():
    return render('sign-in.trouble.html')


@frontstage.route('/sign-in/final-sign-in')
def sign_in_last_attempt():
    return render('sign-in.last-attempt.html')


@frontstage.route('/sign-in/account-locked/')
def sign_in_account_locked():
    return render('sign-in.locked-account.html')


# ===== Forgot password =====
@frontstage.route('/forgot-password/')
def forgot_password():
    templateData = {
        "error": {
            "type": request.args.get("error")
        }
    }

    # data variables configured: {"error": <undefined, failed>}
    return render_template('forgot-password.html', _theme='default', data=templateData)


@frontstage.route('/forgot-password/check-email/')
def forgot_password_check_email():
    return render('forgot-password.check-email.html')


# ===== Reset password =====
@frontstage.route('/reset-password/')
def reset_password():
    templateData = {
        "error": {
            "type": request.args.get("error")
        }
    }

    current_app.logger.debug(request.args.get("error"))

    # data variables configured: {"error": <undefined, password-mismatch>}
    return render_template('reset-password.html', _theme='default', data=templateData)


@frontstage.route('/reset-password/confirmation/')
def reset_password_confirmation():
    return render('reset-password.confirmation.html')


# ===== Registration =====
@frontstage.route('/create-account/', methods=['GET', 'POST'])
def register():
    """Handles user registration"""

    form = ActivationCodeForm(request.form)

    if request.method == 'POST' and form.validate():
        activation_code = request.form.get('activation_code')
        current_app.logger.debug("Activation code is: {}".format(activation_code))

    if form.errors:
        flash(form.errors, 'danger')

    templateData = {
        "error": {
            "type": request.args.get("error")
        }
    }

    return render_template('register.html', _theme='default', form=form, data=templateData)


# This take all the user credentials and then creates an account on the OAuth2 server
@frontstage.route('/create-account/enter-account-details/', methods=['GET', 'POST'])
def register_enter_your_details():

    form = RegistrationForm(request.form)

    if request.method == 'POST' and form.validate():

        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email_address = request.form.get('email_address')
        email_address_confirm = request.form.get('email_address_confirm')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        phone_number = request.form.get('phone_number')
        terms_and_conditions = request.form.get('terms_and_conditions')

        current_app.logger.debug("User name is: {} {}".format(first_name, last_name))
        current_app.logger.debug("Email is: {}".format(email_address))
        current_app.logger.debug("Confirmation email is: {}".format(email_address_confirm))
        current_app.logger.debug("password is: {}".format(password))
        current_app.logger.debug("Confirmation password is: {}".format(password_confirm))
        current_app.logger.debug("phone number is: {}".format(phone_number))
        current_app.logger.debug("T's&C's is: {}".format(terms_and_conditions))

        # Lets try and create this user on the OAuth2 server
        OAuth_payload = {"username": email_address, "password": password, "client_id": OAuthConfig.RAS_FRONTSTAGE_CLIENT_ID, "client_secret": OAuthConfig.RAS_FRONTSTAGE_CLIENT_SECRET }
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        authorisation = (OAuthConfig.RAS_FRONTSTAGE_CLIENT_ID, OAuthConfig.RAS_FRONTSTAGE_CLIENT_SECRET)

        try:
            OAuthurl = OAuthConfig.ONS_OAUTH_PROTOCOL + OAuthConfig.ONS_OAUTH_SERVER + OAuthConfig.ONS_ADMIN_ENDPOINT
            OAuth_response = requests.post(OAuthurl, auth=authorisation, headers=headers, data=OAuth_payload)
            current_app.logger.debug("OAuth response is: {}".format(OAuth_response.content))
            response_body = json.loads(OAuth_response.content)

            # TODO A utility function to allow us to route to a page for 'user is registered already'. We need a html page for this.

        except requests.exceptions.ConnectionError:
            current_app.logger.critical("There seems to be no server listening on this connection?")
            # TODO A redirect to a page that helps the user

        except requests.exceptions.Timeout:
            current_app.logger.critical("Timeout error. Is the OAuth Server overloaded?")
            # TODO A redirect to a page that helps the user
        except requests.exceptions.RequestException as e:
            # TODO catastrophic error. bail. A page that tells the user something horrid has happeded and who to inform
            current_app.logger.debug(e)

        if OAuth_response.status_code == 401:
            # This looks like the user is not authorized to use the system. it could be a duplicate email. check our
            # exact error. if it is, then tell the user else fail as our server is not allowed to access the OAuth2
            # system.
            # TODO add logging
            # {"detail":"Duplicate user credentials"}
            if response_body["detail"]:
                if response_body["detail"] == 'Duplicate user credentials':
                    current_app.logger.warning("We have duplicate user credentials")
                    errors = {'email_address_confirm': ['Please try a different email, this one is in use', ]}

                    return render_template('register.enter-your-details.html', _theme='default', form=form, errors=errors)

        # Deal with all other errors from OAuth2 registration
        if OAuth_response.status_code > 401:
            OAuth_response.raise_for_status()  # A stop gap until we know all the correct error pages
            current_app.logger.warning("OAuth error")

        # We now have a successful user setup on the OAuth2 server. The next 2 steps we have to do are:
        # 1) Get a valid token for service to service communication. This is done so that the front stage service can
        #   talk with the party service to create a user.
        # 2) Create the user on the party service using the party service /respondent/ endpoint

        # Step 1
        # Creates a 'session client' to interact with OAuth2. This provides a client ID to our client that is used to
        # interact with the server.
        client = BackendApplicationClient(client_id=OAuthConfig.RAS_FRONTSTAGE_CLIENT_ID)

        # Populates the request body with username and password from the user
        client.prepare_request_body(scope=['ps.write',])

        # passes our 'client' to the session management object. this deals with the transactions between the OAuth2 server
        oauth = OAuth2Session(client=client)
        token_url = OAuthConfig.ONS_OAUTH_PROTOCOL + OAuthConfig.ONS_OAUTH_SERVER + OAuthConfig.ONS_TOKEN_ENDPOINT
        current_app.logger.debug("Our Token Endpoint is: ", token_url)

        try:
            token = oauth.fetch_token(token_url=token_url, client_id=OAuthConfig.RAS_FRONTSTAGE_CLIENT_ID, client_secret=OAuthConfig.RAS_FRONTSTAGE_CLIENT_SECRET)
            current_app.logger.debug(" *** Access Token Granted *** ")
            current_app.logger.debug(" Values are: ")
            for key in token:
                current_app.logger.debug("{} Value is: {}".format(key, token[key]))

            # TODO Check that this token has not expired. This should never happen, as we just got this token to
            # register the user

            data_dict_for_jwt_token = {"refresh_token": token['refresh_token'],
                                       "access_token": token['access_token'],
                                       "scope": token['scope'],
                                       "expires_at": token['expires_at'],
                                       "username": email_address}

            # We need to take our token from teh OAuth2 server and encode in a JWT token and send in the authorization
            # header to the party service microservice
            encoded_jwt_token = encode(data_dict_for_jwt_token)

        except JWTError:
            # TODO Provide proper logging
            current_app.logger.warning('JWT scope could not be validated.')
            return abort(500, '{"message":"There was a problem with the Authentication service please contact a member of the ONS staff"}')
        except MissingTokenError as e:
            current_app.logger.warning("Missing token error, error is: {}".format(e))
            current_app.logger.warning("Failed validation")
            return abort(500, '{"message":"There was a problem with the Authentication service please contact a member of the ONS staff"}')

        # Step 2
        # Register with the party service

        registrationData = {'emailAddress': email_address, 'firstName': first_name, 'lastName': last_name, 'telephone': phone_number, 'status': 'CREATED' }
        headers = {'authorization': encoded_jwt_token, 'content-type': 'application/json'}
        partyServiceURL = PartyService.PARTYSERVICE_PROTOCOL + PartyService.PARTYSERVICE_SERVER + PartyService.PARTYSERVICE_REGISTER_ENDPOINT
        current_app.logger.debug("Party service URL is: {}".format(partyServiceURL))

        try:
            register_user = requests.post(partyServiceURL, headers=headers, data=json.dumps(registrationData))
            current_app.logger.debug("Response from party service is: {}".format(register_user.content))

            if register_user.ok:
                return render_template('register.almost-done.html', _theme='default', email=email_address)
            else:
                return abort(500, '{"message":"There was a problem with the registration service, please contact a member of the ONS staff"}')

        except ConnectionError:
            current_app.logger.critical("We could not connect to the party service")
            return abort(500, '{"message":"There was a problem establishing a connection with an ONS micro service."}')
        # TODO We need to add an exception timeout catch and handle this type of error

    else:
        current_app.logger.debug("either this is not a POST, or form validation failed")
        current_app.logger.warning("Form failed validation, errors are: {}".format(form.errors))

    return render_template('register.enter-your-details.html', _theme='default', form=form, errors=form.errors)


@frontstage.route('/create-account/confirm-organisation-survey/')
def register_confirm_organisation_survey():
    return render('register.confirm-organisation-survey.html')


@frontstage.route('/create-account/check-email/')
def register_almost_done():
    return render('register.almost-done.html')


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


@frontstage.route('/protected/collectioninstrument/id/<string:_id>', methods=['GET', 'POST'])
def get_id(_id):
    """
    Method to return collection instrument json by ID.
    """
    # app.logger.info('get_id with value: {} '.format(_id))

    # First check we have a jwt token.
    if (session.get(('jwt_token') and session.get('username'))):
        jwttoken = session.get('jwt_token')

        # If we can decode the the token we need to get the user ID out and
        # ensure it's a valid token for that user in our database
        decodedJWT = decode(jwttoken)
        userID = decodedJWT['user_id']

        # lets find a user with this ID and check the token

        try:
            user_object = User.query.filter_by(username=userID).first()
            # Check the tokens are the same
            # TODO Check the token has not expired
            if user_object.token == jwttoken:
                # OK Tokens match we can forward this on to our collection instrument
                headers = {'authorization': jwttoken}
                # TODO make the calling of this URL a utility function
                url = 'localhost:5000/collectioninstrument/id/' + '_id'             # OK construct the URL now we know it's a valid token
                # Depending on wheather this is a put or a get will change how we forward on this message
                if request.method['GET']:
                    req = requests.get(url,  headers=headers)
                if request.method['PUT']:
                    req = requests.post(url,  headers=headers)
                data = req.json()
                current_app.logger.debug(data)
                res = Response(response=data, status=200, mimetype="application/json")
                return res

            # Anything else but a token match means we reject the call
            current_app.logger.warning("tokens don't match")
            res = Response(response="""Your session is stale, try logging in again to
                                     refresh your session variables""", status=404, mimetype="text/html")
            return res
        except:
            current_app.logger.debug("failure to find a user with this ID")
            res = Response(response="""Looks like you are not a valid user,
                           try logging in again and refresh your session""", status=404, mimetype="text/html")
            return res

    # If we hit here then the request did not have a token or username set
    res = Response(response="Not authorised", status=403, mimetype="text/html")
    return res


def setup_logging():
    """Set up logging for application"""

    logging.basicConfig(level=FrontstageLogging.LOG_LEVEL)
    log_formatter = logging.Formatter(FrontstageLogging.LOG_FORMAT)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(log_formatter)

    current_app.logger.addHandler(stdout_handler)


if __name__ == '__main__':
    setup_logging()
    PORT = int(os.environ.get('PORT', 5001))
    current_app.run(host='0.0.0.0', port=PORT)
