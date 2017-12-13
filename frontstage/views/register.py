import json
import logging
from os import getenv

from flask import Blueprint, redirect, render_template, request, url_for
from structlog import wrap_logger

from frontstage import app
from frontstage.common.api_call import api_call
from frontstage.common.cryptographer import Cryptographer
from frontstage.exceptions.exceptions import ApiError
from frontstage.models import EnrolmentCodeForm, RegistrationForm


logger = wrap_logger(logging.getLogger(__name__))
register_bp = Blueprint('register_bp', __name__,
                        static_folder='static', template_folder='templates/register')
cryptographer = Cryptographer()


@register_bp.route('/create-account', methods=['GET', 'POST'])
def register():
    form = EnrolmentCodeForm(request.form)

    if request.method == 'POST' and form.validate():
        logger.info('Enrolment code submitted')
        enrolment_code = request.form.get('enrolment_code').lower()
        request_data = {
            'enrolment_code': enrolment_code,
            'initial': True
        }
        response = api_call('POST', app.config['VALIDATE_ENROLMENT'], json=request_data)

        # Handle API errors
        if response.status_code == 404:
            logger.info('Enrolment code not found')
            template_data = {"error": {"type": "failed"}}
            return render_template('register/register.enter-enrolment-code.html', _theme='default',
                                   form=form, data=template_data), 202
        elif response.status_code == 401 and not json.loads(response.text).get('active'):
            logger.info('Enrolment code not active')
            template_data = {"error": {"type": "failed"}}
            return render_template('register/register.enter-enrolment-code.html', _theme='default',
                                   form=form, data=template_data), 200
        elif response.status_code != 200:
            logger.error('Failed to submit enrolment code')
            raise ApiError(response)

        encrypted_enrolment_code = cryptographer.encrypt(enrolment_code.encode()).decode()
        logger.info('Successful enrolment code submitted')
        return redirect(url_for('register_bp.register_confirm_organisation_survey',
                                encrypted_enrolment_code=encrypted_enrolment_code,
                                _external=True,
                                _scheme=getenv('SCHEME', 'http')))

    return render_template('register/register.enter-enrolment-code.html', _theme='default',
                           form=form, data={"error": {}})


@register_bp.route('/create-account/confirm-organisation-survey', methods=['GET'])
def register_confirm_organisation_survey():
    # Get and decrypt enrolment code
    encrypted_enrolment_code = request.args.get('encrypted_enrolment_code', None)
    enrolment_code = cryptographer.decrypt(encrypted_enrolment_code.encode()).decode()

    logger.info('Attempting to retrieve data for confirm organisation/survey page')
    response = api_call('POST', app.config['CONFIRM_ORGANISATION_SURVEY'],
                        json={'enrolment_code': enrolment_code})

    if response.status_code != 200:
        logger.error('Failed to retrieve data for confirm organisation/survey page')
        raise ApiError(response)

    response_json = json.loads(response.text)
    logger.info('Successfully retrieved data for confirm organisation/survey page')
    return render_template('register/register.confirm-organisation-survey.html',
                           _theme='default',
                           enrolment_code=enrolment_code,
                           encrypted_enrolment_code=encrypted_enrolment_code,
                           organisation_name=response_json['organisation_name'],
                           survey_name=response_json['survey_name'])


@register_bp.route('/create-account/enter-account-details', methods=['GET', 'POST'])
def register_enter_your_details():
    # Get and decrypt enrolment code
    encrypted_enrolment_code = request.args.get('encrypted_enrolment_code', None)
    enrolment_code = cryptographer.decrypt(encrypted_enrolment_code.encode()).decode()
    form = RegistrationForm(request.values, enrolment_code=encrypted_enrolment_code)

    if request.method == 'POST' and form.validate():
        logger.info('Attempting to create account')
        registration_data = {
            'emailAddress': request.form.get('email_address'),
            'firstName': request.form.get('first_name'),
            'lastName': request.form.get('last_name'),
            'password': request.form.get('password'),
            'telephone': request.form.get('phone_number'),
            'enrolmentCode': enrolment_code
        }
        # Api will validate the enrolment code before it creates account
        response = api_call('POST', app.config['CREATE_ACCOUNT'], json=registration_data)

        # Handle errors from the Api service
        if response.status_code == 400:
            logger.debug('Email already used')
            error = {"email_address": ["This email has already been used to register an account"]}
            return render_template('register/register.enter-your-details.html',
                                   _theme='default',
                                   form=form,
                                   errors=error)
        elif response.status_code != 201:
            logger.error('Failed to create account')
            raise ApiError(response)

        logger.info('Successfully created account')
        return render_template('register/register.almost-done.html',
                               _theme='default', email=request.form.get('email_address'))

    else:
        # Validate enrolment code before rendering form
        response = api_call('POST', app.config['VALIDATE_ENROLMENT'],
                            json={'enrolment_code': enrolment_code})
        if response.status_code != 200:
            logger.error('Failed to validate enrolment code')
            if response.status_code == 401:
                logger.error('Invalid enrolment code used')
            raise ApiError(response)

        return render_template('register/register.enter-your-details.html', _theme='default',
                               form=form, errors=form.errors)


@register_bp.route('/create-account/check-email')
def register_almost_done():
    return render_template('register/register.almost-done.html', _theme='default')


@register_bp.route('/activate-account/<token>', methods=['GET'])
def register_activate_account(token):
    logger.info('Attempting to verify email')
    response = api_call('PUT', app.config['VERIFY_EMAIL'], parameters={'token': token})

    # Handle api errors
    if response.status_code == 409:
        logger.info('Expired email verification token', token=token)
        return render_template('register/register.link-expired.html', _theme='default')
    elif response.status_code == 404:
        logger.warning('Unrecognised email verification token', token=token)
        return redirect(url_for('error_bp.not_found_error_page'))
    elif response.status_code != 200:
        logger.info('Failed to verify email')
        raise ApiError(response)

    # Successful account activation therefore redirect back to the login screen
    logger.info('Successfully verified email')
    return redirect(url_for('sign_in_bp.login',
                            account_activated=True,
                            _external=True,
                            _scheme=getenv('SCHEME', 'http')))

