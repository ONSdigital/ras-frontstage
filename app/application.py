
"""
Main file that is run
"""

import json
import logging
import os
from datetime import datetime
from functools import wraps, update_wrapper
import requests
from flask import Flask, make_response, render_template, request, flash, redirect, url_for, abort #session, abort
from jose import JWTError
from oauthlib.oauth2 import LegacyApplicationClient, BackendApplicationClient, MissingTokenError
from requests import ConnectionError
from requests_oauthlib import OAuth2Session
from structlog import wrap_logger
from ons_ras_common import ons_env

from app.views.secure_messaging import secure_message_bp
from app.views.surveys import surveys_bp

from app.filters.case_status_filter import case_status_filter
from app.filters.file_size_filter import file_size_filter

from app.config import OAuthConfig, Config, TestingConfig, ProductionConfig
from app.jwt import encode
from app.models import LoginForm, RegistrationForm, EnrolmentCodeForm, db
from app.logger_config import logger_initial_config

app = Flask(__name__)
app.debug = True

app.config.update(
    DEBUG=True,
    TESTING=True,
    TEMPLATES_AUTO_RELOAD=True
)

db.init_app(app)


app.jinja_env.filters['case_status_filter'] = case_status_filter
app.jinja_env.filters['file_size_filter'] = file_size_filter

logger_initial_config(service_name='ras-frontstage')

logger = wrap_logger(logging.getLogger(__name__))

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
    return render_template('_temp.html', _theme='default')


@app.route('/error', methods=['GET', 'POST'])
def error_page():
    #
    #session.pop('jwt_token', None)
    response = make_response(render_template('error.html', _theme='default', data={"error": {"type": "failed"}}))
    response.set_cookie('authorization', value='', expires=0)
    return response

#    return render_template('error.html', _theme='default', data={"error": {"type": "failed"}})


# ===== Log out =====
@app.route('/logout')
def logout():
    # No more sessions!
    #if 'jwt_token' in session:
    #    session.pop('jwt_token')
    response = make_response(redirect(url_for('login')))
    response.set_cookie('authorization', value='', expires=0)
    return response


# ===== Sign in using OAuth2 =====
@app.route('/sign-in', methods=['GET', 'POST'])
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
        client = LegacyApplicationClient(
            client_id=OAuthConfig.RAS_FRONTSTAGE_CLIENT_ID)

        # Populates the request body with username and password from the user
        client.prepare_request_body(username=username, password=password, scope=['ci.write', 'ci.read'])

        # passes our 'client' to the session management object. this deals with
        # the transactions between the OAuth2 server
        oauth = OAuth2Session(client=client)
        token_url = OAuthConfig.ONS_OAUTH_PROTOCOL + OAuthConfig.ONS_OAUTH_SERVER + OAuthConfig.ONS_TOKEN_ENDPOINT

        try:
            token = oauth.fetch_token(token_url=token_url, username=username, password=password, client_id=OAuthConfig.RAS_FRONTSTAGE_CLIENT_ID,
                                      client_secret=OAuthConfig.RAS_FRONTSTAGE_CLIENT_SECRET)
            app.logger.debug(" *** Access Token Granted *** ")
            app.logger.debug(" Values are: ")
            for key in token:
                logger.debug("{} Value is: {}".format(key, token[key]))

        except MissingTokenError as e:
            logger.warning("Missing token error, error is: {}".format(e))
            logger.warning("Failed validation")
            return render_template('sign-in.html', _theme='default', form=form, data={"error": {"type": "failed"}})

        except Exception as e:
            logger.error("Error logging in: {}", str(e))
            return redirect(url_for('error_page'))

        data_dict_for_jwt_token = {
            "refresh_token": token['refresh_token'],
            "access_token": token['access_token'],
            "scope": token['scope'],
            "expires_at": token['expires_at'],
            "username": username
        }
        encoded_jwt_token = encode(data_dict_for_jwt_token)
        # No more sessions!
        #session['jwt_token'] = encoded_jwt_token
        response = make_response(redirect(url_for('surveys_bp.logged_in')))
        response.set_cookie('authorization', value=encoded_jwt_token)
        return response

        #return redirect(url_for('surveys_bp.logged_in'))

    template_data = {
        "error": {
            "type": request.args.get("error"),
            "logged_in": "False"
        },
        'account_activated': account_activated
    }

    return render_template('sign-in.html', _theme='default', form=form, data=template_data)


@app.route('/sign-in/error', methods=['GET'])
def sign_in_error():
    """Handles any sign in errors"""

    # password = request.form.get('pass')
    # password = request.form.get('emailaddress')

    template_data = {
        "error": {
            "type": "failed"
        }
    }

    # data variables configured: {"error": <undefined, failed, last-attempt>}
    return render_template('sign-in.html', _theme='default', data=template_data)


@app.route('/sign-in/troubleshoot')
def sign_in_troubleshoot():
    return render('sign-in.trouble.html')


@app.route('/sign-in/final-sign-in')
def sign_in_last_attempt():
    return render('sign-in.last-attempt.html')


@app.route('/sign-in/account-locked/')
def sign_in_account_locked():
    return render('sign-in.locked-account.html')


# ===== Messages =====
@app.route('/messages')
def messages():
    return render('messages.html')


# ===== Forgot password =====
@app.route('/forgot-password/')
def forgot_password():
    template_data = {
        "error": {
            "type": request.args.get("error")
        }
    }

    # data variables configured: {"error": <undefined, failed>}
    return render_template('forgot-password.html', _theme='default', data=template_data)


@app.route('/forgot-password/check-email/')
def forgot_password_check_email():
    return render('forgot-password.check-email.html')


# ===== Reset password =====
@app.route('/reset-password/')
def reset_password():
    template_data = {
        "error": {
            "type": request.args.get("error")
        }
    }

    if 'error' in request.args:
        logger.debug(request.args.get("error"))

    # data variables configured: {"error": <undefined, password-mismatch>}
    return render_template('reset-password.html', _theme='default', data=template_data)


@app.route('/reset-password/confirmation/')
def reset_password_confirmation():
    return render('reset-password.confirmation.html')


def validate_enrolment_code(enrolment_code):
    case_id = None

    # Build the URL
    url = Config.API_GATEWAY_IAC_URL + '{}'.format(enrolment_code)
    logger.debug('Validate IAC URL is: {}'.format(url))

    # Call the API Gateway Service to validate the enrolment code
    result = requests.get(url, verify=False)
    logger.debug('Result => {} {} : {}'.format(result.status_code, result.reason, result.text))

    if result.status_code == 200 and json.loads(result.text)['active']:
        case_id = json.loads(result.text)['caseId']

    return case_id


# ===== Registration =====
@app.route('/create-account/', methods=['GET', 'POST'])
def register():
    """Handles user registration"""

    form = EnrolmentCodeForm(request.form)

    template_data = {
        "error": {}
    }

    if request.method == 'POST' and form.validate():

        enrolment_code = request.form.get('enrolment_code')
        logger.debug("Enrolment code is: {}".format(enrolment_code))

        case_id = validate_enrolment_code(enrolment_code)

        if case_id:

            # Post an authentication case event to the case service
            ons_env.case_service.post_event(case_id,
                                            category='ACCESS_CODE_AUTHENTICATION_ATTEMPT',
                                            created_by='TODO',
                                            party_id='db036fd7-ce17-40c2-a8fc-932e7c228397',
                                            description='Enrolment code entered "{}"'.format(enrolment_code))

            # Encrypt the enrolment code
            coded_token = ons_env.crypt.encrypt(enrolment_code.encode()).decode()

            return redirect(url_for('register_confirm_organisation_survey', enrolment_code=coded_token))
        else:
            logger.info('Invalid IAC code: {}'.format(enrolment_code))
            template_data = {
                "error": {
                    "type": "failed"
                }
            }

    if form.errors:
        flash(form.errors, 'danger')

    return render_template('register.enter-enrolment-code.html', _theme='default', form=form, data=template_data)


@app.route('/create-account/confirm-organisation-survey/')
def register_confirm_organisation_survey():
    encrypted_enrolment_code = request.args.get('enrolment_code', None)

    # Decrypt the enrolment code if we have one
    if encrypted_enrolment_code:
        enrolment_code = ons_env.crypt.decrypt(encrypted_enrolment_code.encode()).decode()
    else:
        ons_env.logger.error('Confirm organisation screen - Enrolment code not specified')
        return redirect(url_for('login'))

    case_id = validate_enrolment_code(enrolment_code)

    # Ensure we have got a valid enrolment code, otherwise go to the sign in page
    if not case_id:
        ons_env.logger.error('Confirm organisation screen - Case ID not available')
        return redirect(url_for('login'))

    # TODO More error handling e.g. cater for case not coming back from the case service, etc.

    # TODO Use ras-common for this lookup
    # Look up the case by case_id
    url = Config.API_GATEWAY_CASE_URL + case_id
    case = requests.get(url, verify=False)
    logger.debug('Result => {} {} : {}'.format(case.status_code, case.reason, case.text))
    case = json.loads(case.text)

    business_party_id = case['caseGroup']['partyId']
    collection_exercise_id = case['caseGroup']['collectionExerciseId']

    # Look up the organisation
    url = Config.API_GATEWAY_PARTY_URL + 'businesses/id/' + business_party_id
    party = requests.get(url, verify=False)
    logger.debug('Result => {} {} : {}'.format(party.status_code, party.reason, party.text))
    party = json.loads(party.text)

    # Get the organisation name
    organisation_name = party['name']

    # TODO Use ras-common for this lookup
    # Look up the collection exercise
    url = Config.API_GATEWAY_COLLECTION_EXERCISE_URL + collection_exercise_id
    collection_exercise = requests.get(url, verify=False)
    logger.debug('Result => {} {} : {}'.format(collection_exercise.status_code, collection_exercise.reason,
                                               collection_exercise.text))
    collection_exercise = json.loads(collection_exercise.text)
    survey_id = collection_exercise['surveyId']

    # Look up the survey
    url = Config.API_GATEWAY_SURVEYS_URL + survey_id
    survey = requests.get(url, verify=False)
    logger.debug('Result => {} {} : {}'.format(survey.status_code, survey.reason, survey.text))
    survey = json.loads(survey.text)

    # Get the survey name
    survey_name = survey['longName']

    if request.method == 'POST':
        return redirect(url_for('register_enter_your_details', enrolment_code=encrypted_enrolment_code,
                                organisation_name=organisation_name, survey_name=survey_name))

    return render_template('register.confirm-organisation-survey.html', _theme='default', enrolment_code=enrolment_code,
                           encrypted_enrolment_code=encrypted_enrolment_code, organisation_name=organisation_name,
                           survey_name=survey_name)


# This take all the user credentials and then creates an account on the OAuth2 server
@app.route('/create-account/enter-account-details', methods=['GET', 'POST'])
def register_enter_your_details():

    enrolment_code = request.args.get('enrolment_code', None)
    if not enrolment_code:
        enrolment_code = request.form.get('enrolment_code')

    form = RegistrationForm(request.values, enrolment_code=enrolment_code)

    # Decrypt the enrolment_code if we have one
    if enrolment_code:
        enrolment_code = ons_env.crypt.decrypt(enrolment_code.encode()).decode()

    # Ensure we have got a valid enrolment code, otherwise go to the sign in page
    if not validate_enrolment_code(enrolment_code):
        return redirect(url_for('login'))

    if request.method == 'POST' \
            and 'create-account/enter-account-details' in request.headers['referer'] \
            and form.validate():

        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email_address = request.form.get('email_address')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        phone_number = request.form.get('phone_number')

        logger.debug("User name is: {} {}".format(first_name, last_name))
        logger.debug("Email is: {}".format(email_address))
        logger.debug("password is: {}".format(password))
        logger.debug("Confirmation password is: {}".format(password_confirm))
        logger.debug("phone number is: {}".format(phone_number))

        # Lets try and create this user on the OAuth2 server
        OAuth_payload = {"username": email_address, "password": password,
                         "client_id": OAuthConfig.RAS_FRONTSTAGE_CLIENT_ID, "client_secret": OAuthConfig.RAS_FRONTSTAGE_CLIENT_SECRET}
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        authorisation = (OAuthConfig.RAS_FRONTSTAGE_CLIENT_ID,
                         OAuthConfig.RAS_FRONTSTAGE_CLIENT_SECRET)

        try:
            OAuthurl = OAuthConfig.ONS_OAUTH_PROTOCOL + OAuthConfig.ONS_OAUTH_SERVER + OAuthConfig.ONS_ADMIN_ENDPOINT
            OAuth_response = requests.post(OAuthurl, auth=authorisation, headers=headers, data=OAuth_payload)
            logger.debug("OAuth response is: {}".format(OAuth_response.content))

            # json.loads(myResponse.content.decode('utf-8'))
            response_body = json.loads(OAuth_response.content.decode('utf-8'))
            logger.debug("OAuth2 response is: {}".format(OAuth_response.status_code))

            if OAuth_response.status_code == 401:
                # This looks like the user is not authorized to use the system. it could be a duplicate email. check our
                # exact error. if it is, then tell the user else fail as our server is not allowed to access the OAuth2
                # system.
                # TODO add logging
                # {"detail":"Duplicate user credentials"}
                if response_body["detail"]:
                    if response_body["detail"] == 'Duplicate user credentials':
                        logger.warning("We have duplicate user credentials")
                        errors = {'email_address': ['Please try a different email, this one is in use', ]}
                        return render_template('register.enter-your-details.html', _theme='default', form=form, errors=errors)

            # Deal with all other errors from OAuth2 registration
            if OAuth_response.status_code > 401:
                OAuth_response.raise_for_status()  # A stop gap until we know all the correct error pages
                logger.warning("OAuth error")

            # TODO A utility function to allow us to route to a page for 'user is registered already'.
            # We need a html page for this.

        except requests.exceptions.ConnectionError:
            logger.critical("There seems to be no server listening on this connection?")
            # TODO A redirect to a page that helps the user

        except requests.exceptions.Timeout:
            logger.critical("Timeout error. Is the OAuth Server overloaded?")
            # TODO A redirect to a page that helps the user
        except requests.exceptions.RequestException as e:
            # TODO catastrophic error. bail. A page that tells the user something horrid has happened and who to inform
            logger.debug(e)

        # if OAuth_response.status_code == 401:
        #     # This looks like the user is not authorized to use the system. it could be a duplicate email. check our
        #     # exact error. if it is, then tell the user else fail as our server is not allowed to access the OAuth2
        #     # system.
        #     # TODO add logging
        #     # {"detail":"Duplicate user credentials"}
        #     if response_body["detail"]:
        #         if response_body["detail"] == 'Duplicate user credentials':
        #             logger.warning("We have duplicate user credentials2")
        #             errors = {'email_address': ['Please try a different email, this one is in use', ]}
        #             return render_template('register.enter-your-details.html', _theme='default', form=form, errors=errors)
        #
        # # Deal with all other errors from OAuth2 registration
        # if OAuth_response.status_code > 401:
        #     OAuth_response.raise_for_status()  # A stop gap until we know all the correct error pages
        #     logger.warning("OAuth error")

        # We now have a successful user setup on the OAuth2 server. The next 2 steps we have to do are:
        # 1) Get a valid token for service to service communication. This is done so that the front stage service can
        #   talk with the party service to create a user.
        # 2) Create the user on the party service using the party service
        # /respondent/ endpoint

        # Step 1
        # Creates a 'session client' to interact with OAuth2. This provides a client ID to our client that is used to
        # interact with the server.
        client = BackendApplicationClient(
            client_id=OAuthConfig.RAS_FRONTSTAGE_CLIENT_ID)

        # Populates the request body with username and password from the user
        client.prepare_request_body(scope=['ps.write', ])

        # passes our 'client' to the session management object. this deals with
        # the transactions between the OAuth2 server
        oauth = OAuth2Session(client=client)
        token_url = OAuthConfig.ONS_OAUTH_PROTOCOL + OAuthConfig.ONS_OAUTH_SERVER + OAuthConfig.ONS_TOKEN_ENDPOINT
        logger.debug("Our Token Endpoint is: {}".format(token_url))

        try:
            token = oauth.fetch_token(token_url=token_url, client_id=OAuthConfig.RAS_FRONTSTAGE_CLIENT_ID,
                                      client_secret=OAuthConfig.RAS_FRONTSTAGE_CLIENT_SECRET)
            app.logger.debug(" *** Access Token Granted *** ")
            app.logger.debug(" Values are: ")
            for key in token:
                logger.debug("{} Value is: {}".format(key, token[key]))

            # TODO Check that this token has not expired. This should never happen, as we just got this token to
            # register the user

            data_dict_for_jwt_token = {
                "refresh_token": token['refresh_token'],
                "access_token": token['access_token'],
                "scope": token['scope'],
                "expires_at": token['expires_at'],
                "username": email_address
            }

            # We need to take our token from teh OAuth2 server and encode in a JWT token and send in the authorization
            # header to the party service microservice
            encoded_jwt_token = encode(data_dict_for_jwt_token)

        except JWTError:
            # TODO Provide proper logging
            logger.warning('JWT scope could not be validated.')
            return abort(500, '{"message":"There was a problem with the Authentication service please contact a member of the ONS staff"}')

        except MissingTokenError as e:
            app.logger.warning("Missing token error, error is: {}".format(e))
            app.logger.warning("Failed validation")

            return abort(500, '{"message":"There was a problem with the Authentication service please contact a member of the ONS staff"}')

        # Step 2
        # Register with the party service
        registration_data = {
            'emailAddress': email_address,
            'firstName': first_name,
            'lastName': last_name,
            'telephone': phone_number,
            'status': 'CREATED'
        }

        headers = {'authorization': encoded_jwt_token, 'content-type': 'application/json'}

        party_service_url = Config.API_GATEWAY_PARTY_URL + 'respondents'
        app.logger.debug("Party service URL is: {}".format(party_service_url))

        try:
            register_user = requests.post(party_service_url, headers=headers, data=json.dumps(registration_data))
            logger.debug("Response from party service is: {}".format(register_user.content))

            if register_user.ok:
                return render_template('register.almost-done.html', _theme='default', email=email_address)
            else:
                return abort(500, '{"message":"There was a problem with the registration service, please contact a member of the ONS staff"}')

        except ConnectionError:
            logger.critical("We could not connect to the party service")
            return abort(500, '{"message":"There was a problem establishing a connection with an ONS micro service."}')
        # TODO We need to add an exception timeout catch and handle this type of error

    else:
        logger.debug("either this is not a POST, or form validation failed")
        logger.warning("Form failed validation, errors are: {}".format(form.errors))

    return render_template('register.enter-your-details.html', _theme='default', form=form, errors=form.errors)


@app.route('/create-account/check-email/')
def register_almost_done():
    return render('register.almost-done.html')


@app.route('/activate-account', methods=['GET'])
def register_activate_account():
    token = request.args.get('token', None)

    # If the token was not provided then show the link expired page
    if not token:
        logger.warning('Missing email activation token')
        return redirect(url_for('register_resend_email'))

    # Call the Party service to try to activate the account corresponding to the token that was supplied
    url = Config.API_GATEWAY_PARTY_URL + 'emailverification/' + token
    result = requests.post(url)
    logger.debug('Activate account - response from party service is: {}'.format(result.content))

    if result.status_code == 200 and json.loads(result.text)['active']:
        return redirect(url_for('login', account_activated=True))
    else:
        return redirect(url_for('register_resend_email'))


@app.route('/create-account/resend-email/', methods=['GET'])
def register_resend_email():
    return render('register.link-expired.html')


@app.route('/create-account/email-resent/', methods=['GET'])
def register_email_resent():
    return render('register.email-resent.html')


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
