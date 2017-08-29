import json
import logging
from os import getenv

from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from jose import JWTError
from oauthlib.oauth2 import BackendApplicationClient, MissingTokenError
import requests
from requests_oauthlib import OAuth2Session
from structlog import wrap_logger

from frontstage import app
from frontstage.common.post_event import post_event
from frontstage.jwt import encode
from frontstage.models import RegistrationForm, EnrolmentCodeForm, RespondentStatus
from frontstage.exceptions.exceptions import ExternalServiceError
from frontstage.common.cryptographer import Cryptographer


logger = wrap_logger(logging.getLogger(__name__))

register_bp = Blueprint('register_bp', __name__, static_folder='static', template_folder='templates/register')

cryptographer = Cryptographer()


def validate_enrolment_code(enrolment_code):
    case_id = None

    # TODO Calling methods have been written to expect a 'None' case_id to be returned if
    # the IAC code has already been used (active=false). This makes the following implementation
    # unnecessarily complicated.

    url = app.config['RM_IAC_GET'].format(app.config['RM_IAC_SERVICE'], enrolment_code)
    logger.debug('Enrolment code validation attempt', url=url, enrolment_code=enrolment_code)

    result = requests.get(url, verify=False)
    logger.debug('IAC service response', status_code=result.status_code, reason=result.reason, text=result.text)

    if result.status_code == 200:
        # The IAC does exist
        result = json.loads(result.text)
        active = result['active']
        if active:
            # assign the case_id as expected by calling methods
            case_id = result['caseId']
            logger.info('Active enrolment code used', case_id=case_id)
        else:
            # don't assign the case_id even though one does exist
            logger.info('Inactive enrolment code used', case_id=case_id)

    elif result.status_code == 404:
        logger.error('Enrolment code not found', enrolment_code=enrolment_code)
    elif result.status_code != 200:
        raise ExternalServiceError(result)

    return case_id


# ===== Registration =====
@register_bp.route('/create-account', methods=['GET', 'POST'])
def register():
    """Handles user registration"""

    form = EnrolmentCodeForm(request.form)

    template_data = {
        "error": {}
    }

    if request.method == 'POST' and form.validate():

        enrolment_code = request.form.get('enrolment_code')
        logger.debug('Enrolment code submitted', enrolment_code=enrolment_code)

        case_id = validate_enrolment_code(enrolment_code)

        if case_id:

            url = app.config['RM_CASE_GET_BY_IAC'].format(app.config['RM_CASE_SERVICE'], enrolment_code)
            case = requests.get(url, verify=False)

            if case.status_code == 200:
                case = json.loads(case.text)
                business_party_id = case['partyId']
            elif case.status_code != 200:
                raise ExternalServiceError(case)

            post_event(case_id,
                       category='ACCESS_CODE_AUTHENTICATION_ATTEMPT',
                       created_by='FRONTSTAGE',
                       party_id=business_party_id,
                       description='Access code authentication attempted')

            # Encrypt the enrolment code
            coded_token = cryptographer.encrypt(enrolment_code.encode()).decode()

            return redirect(url_for('register_bp.register_confirm_organisation_survey',
                                    enrolment_code=coded_token,
                                    _external=True,
                                    _scheme=getenv('SCHEME', 'http')))
        else:
            template_data = {"error": {"type": "failed"}}

        return render_template('register/register.enter-enrolment-code.html', _theme='default', form=form,
                               data=template_data), 202

    return render_template('register/register.enter-enrolment-code.html',
                           _theme='default',
                           form=form,
                           data=template_data)


@register_bp.route('/create-account/confirm-organisation-survey', methods=['GET', 'POST'])
def register_confirm_organisation_survey():
    # Validate enrolment code
    encrypted_enrolment_code = request.args.get('enrolment_code', None)
    if not encrypted_enrolment_code:
        encrypted_enrolment_code = request.form.get('enrolment_code')

    if encrypted_enrolment_code:
        decrypted_enrolment_code = cryptographer.decrypt(encrypted_enrolment_code.encode()).decode()
    else:
        logger.error('Enrolment code not specified')
        return redirect(url_for('error_bp.default_error_page'))

    case_id = validate_enrolment_code(decrypted_enrolment_code)
    if not case_id:
        return redirect(url_for('error_bp.default_error_page'))

    # Look up the case by case_id
    url = app.config['RM_CASE_GET'].format(app.config['RM_CASE_SERVICE'], case_id)
    logger.debug('Get case', url=url)
    case = requests.get(url, verify=False)
    logger.debug('Case service response', status_code=case.status_code, reason=case.reason, text=case.text)

    if case.status_code == 200:
        case = json.loads(case.text)
        business_party_id = case['caseGroup']['partyId']
        collection_exercise_id = case['caseGroup']['collectionExerciseId']
    elif case.status_code != 200:
        raise ExternalServiceError(case)

    # Look up the organisation by party_id
    url = app.config['RAS_PARTY_GET_BY_BUSINESS'].format(app.config['RAS_PARTY_SERVICE'], business_party_id)
    logger.debug('Get organisation', url=url)
    party = requests.get(url, verify=False)
    logger.debug('Party service response', status_code=party.status_code, reason=party.reason, text=party.text)

    if party.status_code == 200:
        party = json.loads(party.text)
        organisation_name = party['name']
    elif party.status_code != 200:
        raise ExternalServiceError(party)

    # Look up the collection exercise by collection_exercise_id
    url = app.config['RM_COLLECTION_EXERCISES_GET'].format(app.config['RM_COLLECTION_EXERCISE_SERVICE'], collection_exercise_id)
    logger.debug('Get collection exercise', url=url)
    collection_exercise = requests.get(url, verify=False)
    logger.debug('collection exercise service response',
                 status_code=collection_exercise.status_code,
                 reason=collection_exercise.reason,
                 text=collection_exercise.text)

    if collection_exercise.status_code == 200:
        collection_exercise = json.loads(collection_exercise.text)
        survey_id = collection_exercise['surveyId']
    elif collection_exercise != 200:
        raise ExternalServiceError(collection_exercise)

    # Look up the survey by survey_id
    url = app.config['RM_SURVEY_GET'].format(app.config['RM_SURVEY_SERVICE'], survey_id)
    logger.debug('Get survey', url=url)
    survey = requests.get(url, verify=False)
    logger.debug('Survey response', status_code=survey.status_code, reason=survey.reason, text=survey.text)

    if survey.status_code == 200:
        survey = json.loads(survey.text)
        survey_name = survey['longName']
    elif survey.status_code != 200:
        raise ExternalServiceError(collection_exercise)

    if request.method == 'POST':
        return redirect(url_for('register_bp.register_enter_your_details',
                                enrolment_code=encrypted_enrolment_code,
                                organisation_name=organisation_name,
                                survey_name=survey_name,
                                _external=True,
                                _scheme=getenv('SCHEME', 'http')))
    else:
        return render_template('register/register.confirm-organisation-survey.html',
                               _theme='default',
                               enrolment_code=decrypted_enrolment_code,
                               encrypted_enrolment_code=encrypted_enrolment_code,
                               organisation_name=organisation_name,
                               survey_name=survey_name)


# This take all the user credentials and then creates an account on the OAuth2 server
@register_bp.route('/create-account/enter-account-details', methods=['GET', 'POST'])
def register_enter_your_details():

    # Validate enrolment code
    encrypted_enrolment_code = request.args.get('enrolment_code', None)
    if not encrypted_enrolment_code:
        encrypted_enrolment_code = request.form.get('enrolment_code')

    if encrypted_enrolment_code:
        decrypted_enrolment_code = cryptographer.decrypt(encrypted_enrolment_code.encode()).decode()
    else:
        logger.error('Enrolment code not specified')
        return redirect(url_for('error_bp.default_error_page'))

    case_id = validate_enrolment_code(decrypted_enrolment_code)
    if not case_id:
        return redirect(url_for('error_bp.default_error_page'))

    form = RegistrationForm(request.values, enrolment_code=encrypted_enrolment_code)

    if request.method == 'POST' \
            and 'create-account/enter-account-details' in request.headers['referer'] \
            and form.validate():

        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email_address = request.form.get('email_address')
        password = request.form.get('password')
        phone_number = request.form.get('phone_number')

        client = BackendApplicationClient(client_id=app.config['RAS_FRONTSTAGE_CLIENT_ID'])

        # Populates the request body with username and password from the user
        client.prepare_request_body(scope=['ps.write', ])

        # passes our 'client' to the session management object
        # this deals with the transactions between the OAuth2 server
        oauth = OAuth2Session(client=client)
        token_url = app.config['ONS_OAUTH_PROTOCOL'] + app.config['ONS_OAUTH_SERVER'] + app.config['ONS_TOKEN_ENDPOINT']
        logger.debug('Fetching oauth token', url=token_url)

        try:
            token = oauth.fetch_token(token_url=token_url, client_id=app.config['RAS_FRONTSTAGE_CLIENT_ID'],
                                      client_secret=app.config['RAS_FRONTSTAGE_CLIENT_SECRET'])
            logger.debug('Access token granted')

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
            logger.warning('JWT scope could not be validated')
            return abort(500, '{"event" : "There was a problem with the Authentication service please contact a member of the ONS staff"}')

        except MissingTokenError as e:
            logger.warning('Missing token error', exception=str(e))
            return abort(500, '{"event" : "There was a problem with the Authentication service please contact a member of the ONS staff"}')

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

        party_service_url = app.config['RAS_PARTY_POST_RESPONDENTS'].format(app.config['RAS_PARTY_SERVICE'])
        logger.debug('Attempting account creation', url=party_service_url)
        result = requests.post(party_service_url, headers=headers, data=json.dumps(registration_data))
        logger.debug('Party service response', status_code=result.status_code, reason=result.reason, text=result.text)

        if result.status_code == 400:
            duplicate_error = {"email_address": ["This email has already been used to register an account"]}
            return render_template('register/register.enter-your-details.html',
                                   _theme='default',
                                   form=form,
                                   errors=duplicate_error)
        elif result.status_code != 200:
            raise ExternalServiceError(result)
        else:
            return render_template('register/register.almost-done.html', _theme='default', email=email_address)
        # TODO We need to add an exception timeout catch and handle this type of error
    else:
        if form.errors:
            logger.warning('Form submitted with errors', errors=str(form.errors))
        return render_template('register/register.enter-your-details.html', _theme='default', form=form, errors=form.errors)


@register_bp.route('/create-account/check-email')
def register_almost_done():
    return render_template('register/register.almost-done.html', _theme='default')


@register_bp.route('/activate-account/<token>', methods=['GET'])
def register_activate_account(token):

    # Call the Party service to try to activate the account corresponding to the token that was supplied
    url = app.config['RAS_PARTY_VERIFY_EMAIL'].format(app.config['RAS_PARTY_SERVICE'], token)
    logger.info('Attempting to verify email', url=url)
    result = requests.put(url)

    if result.status_code == 409:
        # Token is expired
        json_response = json.loads(result.text)
        party_id = json_response.get('id')
        if party_id:
            logger.warning('Expired token', token=token, party_id=party_id)
            return render_template('register/register.link-expired.html', _theme='default', party_id=party_id)
        else:
            logger.error('No party_id found', token=token)
            return redirect(url_for('error_bp.default_error_page'))
    elif result.status_code == 404:
        # Token not recognised
        logger.warning("Unrecognised email verification token", token=token)
        return redirect(url_for('error_bp.not_found_error_page'))
    elif result.status_code != 200:
        raise ExternalServiceError(result)

    json_response = json.loads(result.text)

    if json_response.get('status') == RespondentStatus.ACTIVE.name:
        # Successful account activation therefore redirect off to the login screen
        logger.info('User account validated', party_id=json_response.get('id'))
        return redirect(url_for('sign_in_bp.login',
                                account_activated=True,
                                _external=True,
                                _scheme=getenv('SCHEME', 'http')))
    else:
        logger.error('Token status is not ACTIVE and status code is not 409 (You shouldnt get here)', status_code=result.status_code)
        return redirect(url_for('error_bp.default_error_page'))


@register_bp.route('/create-account/email-resent', methods=['GET'])
def register_email_resent():
    # Resend email verification link
    party_id = request.args.get('party_id')
    logger.debug('Attempting to re-send email verification link', party_id=party_id)
    url = app.config['RAS_PARTY_RESEND_VERIFICATION'].format(app.config['RAS_PARTY_SERVICE'], party_id)
    response = requests.get(url)
    if response.status_code == 200:
        logger.info("Successfully re-sent email verification link", party_id=party_id)
        return render_template('register/register.email-resent.html', _theme='default')
    elif response.status_code == 404:
        logger.warning("Party not found to resend email verification link to", party_id=party_id)
        return redirect(url_for('error_bp.default_error_page'))
    else:
        raise ExternalServiceError(response)
