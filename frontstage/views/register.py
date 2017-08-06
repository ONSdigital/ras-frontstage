import json
import logging

from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from jose import JWTError
from oauthlib.oauth2 import BackendApplicationClient, MissingTokenError
from ons_ras_common import ons_env
import requests
from requests_oauthlib import OAuth2Session
from structlog import wrap_logger

from frontstage import app
from frontstage.common.post_event import post_event
from frontstage.jwt import encode
from frontstage.models import RegistrationForm, EnrolmentCodeForm, RespondentStatus


logger = wrap_logger(logging.getLogger(__name__))

register_bp = Blueprint('register_bp', __name__, static_folder='static', template_folder='templates/register')


def validate_enrolment_code(enrolment_code):
    case_id = None

    # Build the URL
    # url = app.config['API_GATEWAY_IAC_URL'] + '{}'.format(enrolment_code)
    url = app.config['RM_IAC_GET'].format(app.config['RM_IAC_SERVICE'], enrolment_code)
    logger.debug('Validate IAC URL is: {}'.format(url))

    # Call the API Gateway Service to validate the enrolment code
    result = requests.get(url, verify=False)
    logger.debug('Result => {} {} : {}'.format(result.status_code, result.reason, result.text))

    if result.status_code == 200 and json.loads(result.text)['active']:
        case_id = json.loads(result.text)['caseId']

    return case_id


# ===== Registration =====
@register_bp.route('/create-account/', methods=['GET', 'POST'])
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

            # TODO pass in the user who is creating the post event

            # Post an authentication case event to the case service
            post_event(case_id,
                        category='ACCESS_CODE_AUTHENTICATION_ATTEMPT',
                        created_by='TODO',
                        party_id='db036fd7-ce17-40c2-a8fc-932e7c228397',
                        description='Enrolment code entered "{}"'.format(enrolment_code))

            # Encrypt the enrolment code
            coded_token = ons_env.crypt.encrypt(enrolment_code.encode()).decode()

            return redirect(url_for('register_bp.register_confirm_organisation_survey', enrolment_code=coded_token))
        else:
            logger.info('Invalid IAC code: {}'.format(enrolment_code))
            template_data = {
                "error": {
                    "type": "failed"
                }
            }

    if form.errors:
        flash(form.errors, 'danger')

    return render_template('register/register.enter-enrolment-code.html', _theme='default', form=form, data=template_data)


@register_bp.route('/create-account/confirm-organisation-survey/', methods=['GET', 'POST'])
def register_confirm_organisation_survey():

    encrypted_enrolment_code = request.args.get('enrolment_code', None)
    if not encrypted_enrolment_code:
        encrypted_enrolment_code = request.form.get('enrolment_code')

    # Decrypt the enrolment code if we have one
    if encrypted_enrolment_code:
        decrypted_enrolment_code = ons_env.crypt.decrypt(encrypted_enrolment_code.encode()).decode()
    else:
        logger.error('Confirm organisation screen - Enrolment code not specified')
        return redirect(url_for('error_bp.error_page'))

    case_id = validate_enrolment_code(decrypted_enrolment_code)

    # Ensure we have got a valid enrolment code, otherwise go to the sign in page
    if not case_id:
        logger.error('Confirm organisation screen - Case ID not available')
        return redirect(url_for('error_bp.error_page'))

    # TODO More error handling e.g. cater for case not coming back from the case service, etc.

    # TODO Use ras-common for this lookup
    # Look up the case by case_id
    # url = app.config['API_GATEWAY_CASE_URL'] + case_id

    url = app.config['RM_CASE_GET'].format(app.config['RM_CASE_SERVICE'], case_id)
    case = requests.get(url, verify=False)
    logger.debug('case result => {} {} : {}'.format(case.status_code, case.reason, case.text))
    case = json.loads(case.text)

    business_party_id = case['caseGroup']['partyId']
    collection_exercise_id = case['caseGroup']['collectionExerciseId']

    # Look up the organisation
    # url = app.config['API_GATEWAY_PARTY_URL'] + 'businesses/id/' + business_party_id

    url = app.config['RAS_PARTY_GET_BY_BUSINESS'].format(app.config['RAS_PARTY_SERVICE'], business_party_id)
    party = requests.get(url, verify=False)
    logger.debug('party result => {} {} : {}'.format(party.status_code, party.reason, party.text))
    party = json.loads(party.text)

    # Get the organisation name
    organisation_name = party['name']

    # TODO Use ras-common for this lookup
    # Look up the collection exercise
    # url = app.config['API_GATEWAY_COLLECTION_EXERCISE_URL'] + collection_exercise_id

    url = app.config['RM_COLLECTION_EXERCISES_GET'].format(app.config['RM_COLLECTION_EXERCISE_SERVICE'], collection_exercise_id)
    logger.debug('collection URL {}'.format(url))

    collection_exercise = requests.get(url, verify=False)
    logger.debug('CE result => {} {} : {}'.format(collection_exercise.status_code, collection_exercise.reason,
                                               collection_exercise.text))
    collection_exercise = json.loads(collection_exercise.text)
    survey_id = collection_exercise['surveyId']

    # Look up the survey
    # url = app.config['API_GATEWAY_SURVEYS_URL'] + survey_id

    url = app.config['RM_SURVEY_GET'].format(app.config['RM_SURVEY_SERVICE'], survey_id)
    logger.debug('survey url {}'.format(url))

    survey = requests.get(url, verify=False)
    logger.debug('survey result => {} {} : {}'.format(survey.status_code, survey.reason, survey.text))
    survey = json.loads(survey.text)

    # Get the survey name
    survey_name = survey['longName']

    if request.method == 'POST':
        return redirect(url_for('register_bp.register_enter_your_details', enrolment_code=encrypted_enrolment_code,
                                organisation_name=organisation_name, survey_name=survey_name))
    else:
        return render_template('register/register.confirm-organisation-survey.html', _theme='default',
                               enrolment_code=decrypted_enrolment_code,
                               encrypted_enrolment_code=encrypted_enrolment_code, organisation_name=organisation_name,
                               survey_name=survey_name)


# This take all the user credentials and then creates an account on the OAuth2 server
@register_bp.route('/create-account/enter-account-details', methods=['GET', 'POST'])
def register_enter_your_details():
    encrypted_enrolment_code = request.args.get('enrolment_code', None)
    if not encrypted_enrolment_code:
        encrypted_enrolment_code = request.form.get('enrolment_code', None)

    # Decrypt the enrolment_code if we have one
    if encrypted_enrolment_code:
        decrypted_enrolment_code = ons_env.crypt.decrypt(encrypted_enrolment_code.encode()).decode()
    else:
        decrypted_enrolment_code = None

    # Ensure we have got a valid enrolment code, otherwise go to the sign in page
    if not decrypted_enrolment_code or not validate_enrolment_code(decrypted_enrolment_code):
        logger.error('Enter Account Details page - invalid enrolment code: ' + str(decrypted_enrolment_code))
        return redirect(url_for('error_bp.error_page'))

    form = RegistrationForm(request.values, enrolment_code=encrypted_enrolment_code)

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
        # OAuth_payload = {
        #     "username": email_address,
        #     "password": password,
        #     "client_id": app.config['RAS_FRONTSTAGE_CLIENT_ID'],
        #     "client_secret": app.config['RAS_FRONTSTAGE_CLIENT_SECRET']
        # }

        headers = {'content-type': 'application/x-www-form-urlencoded'}

        # authorisation = {app.config['RAS_FRONTSTAGE_CLIENT_ID']: app.config['RAS_FRONTSTAGE_CLIENT_SECRET']}

        # try:
        #     OAuthurl = app.config['ONS_OAUTH_PROTOCOL'] + app.config['ONS_OAUTH_SERVER'] + app.config['ONS_ADMIN_ENDPOINT']
        #     OAuth_response = requests.post(OAuthurl, auth=authorisation, headers=headers, data=OAuth_payload)
        #     logger.debug("OAuth response is: {}".format(OAuth_response.content))
        #
        #     # json.loads(myResponse.content.decode('utf-8'))
        #     response_body = json.loads(OAuth_response.content.decode('utf-8'))
        #     logger.debug("OAuth2 response is: {}".format(OAuth_response.status_code))
        #
        #     if OAuth_response.status_code == 401:
        #         # This looks like the user is not authorized to use the system. it could be a duplicate email. check our
        #         # exact error. if it is, then tell the user else fail as our server is not allowed to access the OAuth2
        #         # system.
        #         # TODO add logging
        #         # {"detail":"Duplicate user credentials"}
        #         if response_body["detail"]:
        #             if response_body["detail"] == 'Duplicate user credentials':
        #                 logger.warning("We have duplicate user credentials")
        #                 errors = {'email_address_confirm': ['Please try a different email, this one is in use', ]}
        #                 return render_template('register/register.enter-your-details.html', _theme='default', form=form, errors=errors)
        #
        #     # Deal with all other errors from OAuth2 registration
        #     if OAuth_response.status_code > 401:
        #         OAuth_response.raise_for_status()  # A stop gap until we know all the correct error pages
        #         logger.warning("OAuth error")
        #
        #     # TODO A utility function to allow us to route to a page for 'user is registered already'.
        #     # We need a html page for this.
        #
        # except requests.exceptions.ConnectionError:
        #     logger.critical("There seems to be no server listening on this connection?")
        #     # TODO A redirect to a page that helps the user
        #
        # except requests.exceptions.Timeout:
        #     logger.critical("Timeout error. Is the OAuth Server overloaded?")
        #     # TODO A redirect to a page that helps the user
        # except requests.exceptions.RequestException as e:
        #     # TODO catastrophic error. bail. A page that tells the user something horrid has happened and who to inform
        #     logger.debug(e)

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
        #             return render_template('register/register.enter-your-details.html', _theme='default', form=form, errors=errors)
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
        client = BackendApplicationClient(client_id=app.config['RAS_FRONTSTAGE_CLIENT_ID'])

        # Populates the request body with username and password from the user
        client.prepare_request_body(scope=['ps.write', ])

        # passes our 'client' to the session management object. this deals with
        # the transactions between the OAuth2 server
        oauth = OAuth2Session(client=client)
        token_url = app.config['ONS_OAUTH_PROTOCOL'] + app.config['ONS_OAUTH_SERVER'] + app.config['ONS_TOKEN_ENDPOINT']
        logger.debug("Our Token Endpoint is: {}".format(token_url))

        try:
            token = oauth.fetch_token(token_url=token_url, client_id=app.config['RAS_FRONTSTAGE_CLIENT_ID'],
                                      client_secret=app.config['RAS_FRONTSTAGE_CLIENT_SECRET'])
            logger.debug(" *** Access Token Granted *** ")
            logger.debug(" Values are: ")
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
            logger.warning("Missing token error, error is: {}".format(e))
            logger.warning("Failed validation")

            return abort(500, '{"message":"There was a problem with the Authentication service please contact a member of the ONS staff"}')

        # Step 2
        # Register with the party service
        registration_data = {
            'emailAddress': email_address,
            'firstName': first_name,
            'lastName': last_name,
            'password': password,
            'telephone': phone_number,
            'enrolmentCode': decrypted_enrolment_code,
            'status': 'CREATED'
        }

        headers = {'authorization': encoded_jwt_token, 'content-type': 'application/json'}

        # party_service_url = app.config['API_GATEWAY_PARTY_URL'] + 'respondents'
        party_service_url = app.config['RAS_PARTY_POST_RESPONDENTS'].format(app.config['RAS_PARTY_SERVICE'])
        logger.debug("Party service URL is: {}".format(party_service_url))

        try:
            result = requests.post(party_service_url, headers=headers, data=json.dumps(registration_data))
            logger.debug("Response from party service is: {}".format(result.content))

            if result.status_code == 200:
                return render_template('register/register.almost-done.html', _theme='default', email=email_address)
            else:
                logger.error('Unable to register user - Party service error user')
                return redirect(url_for('error_bp.error_page'))

        except ConnectionError:
            logger.critical("We could not connect to the party service")
            return redirect(url_for('error_bp.error_page'))

        # TODO We need to add an exception timeout catch and handle this type of error

    else:
        logger.debug("either this is not a POST, or form validation failed")
        logger.warning("Form failed validation, errors are: {}".format(form.errors))

    return render_template('register/register.enter-your-details.html', _theme='default', form=form, errors=form.errors)


@register_bp.route('/create-account/check-email/')
def register_almost_done():
    return render_template('register/register.almost-done.html', _theme='default')


@register_bp.route('/activate-account/<token>', methods=['GET'])
def register_activate_account(token):

    # Call the Party service to try to activate the account corresponding to the token that was supplied
    # url = app.config['API_GATEWAY_PARTY_URL'] + 'emailverification/' + token

    url = app.config['RAS_PARTY_VERIFY_EMAIL'].format(app.config['RAS_PARTY_SERVICE'], token)
    result = requests.put(url)
    logger.debug('Activate account - response from party service is: {}'.format(result.content))

    if result.status_code == 200:
        json_response = json.loads(result.text)

        if json_response.get('status')==RespondentStatus.ACTIVE.name:
            # Successful account activation therefore redirect off to the login screen
            return redirect(url_for('sign_in_bp.login', account_activated=True))
        else:
            # Try to get the user id
            user_id = json_response.get('id')
            if user_id:
                # Unable to activate account therefore give the user the option to send out a new email token
                logger.debug('Expired activation token: ' + str(token))
                return redirect(url_for('register_bp.register_resend_email', user_id=user_id))
            else:
                logger.error('Unable to determine user for activation token: ' + str(token))
                return redirect(url_for('error_bp.error_page'))
    else:
        # If the token was not recognised, we don't know who the user is so redirect them off to the error page
        logger.warning('Unrecognised email activation token: ' + str(token) +
                       ' Response code: ' + str(result.status_code))
        return redirect(url_for('error_bp.error_page'))


@register_bp.route('/create-account/resend-email', methods=['GET'])
def register_resend_email():
    user_id = request.args.get('user_id', None)
    return render_template('register/register.link-expired.html', _theme='default', user_id=user_id)


@register_bp.route('/create-account/email-resent', methods=['GET'])
def register_email_resent():
    # TODO Call the service that will request a new email to be sent out

    return render_template('register/register.email-resent.html', _theme='default')
