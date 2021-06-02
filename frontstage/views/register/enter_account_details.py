import logging

from flask import render_template, request, url_for
from structlog import wrap_logger
from werkzeug.utils import redirect

from frontstage.common.cryptographer import Cryptographer
from frontstage.controllers import iac_controller, party_controller
from frontstage.exceptions.exceptions import ApiError
from frontstage.models import RegistrationForm, ShareSurveyRegistrationForm
from frontstage.views.register import register_bp


logger = wrap_logger(logging.getLogger(__name__))
cryptographer = Cryptographer()


@register_bp.route('/create-account/enter-account-details', methods=['GET', 'POST'])
def register_enter_your_details():
    # Get and decrypt enrolment code
    encrypted_enrolment_code = request.args.get('encrypted_enrolment_code', None)
    enrolment_code = cryptographer.decrypt(encrypted_enrolment_code.encode()).decode()
    form = RegistrationForm(request.values, enrolment_code=encrypted_enrolment_code)
    form.email_address.data = form.email_address.data.strip()

    # Validate enrolment code before rendering or checking the form
    iac_controller.validate_enrolment_code(enrolment_code)

    if request.method == 'POST' and form.validate():
        logger.info('Attempting to create account')
        email_address = form.email_address.data
        registration_data = {
            'emailAddress': email_address,
            'firstName': request.form.get('first_name'),
            'lastName': request.form.get('last_name'),
            'password': request.form.get('password'),
            'telephone': request.form.get('phone_number'),
            'enrolmentCode': enrolment_code,
        }

        try:
            party_controller.create_account(registration_data)
        except ApiError as exc:
            if exc.status_code == 400:
                logger.info('Email already used')
                error = {"email_address": ["This email has already been used to register an account"]}
                return render_template('register/register.enter-your-details.html', form=form, errors=error)
            else:
                logger.error('Failed to create account', status=exc.status_code)
                raise exc

        logger.info('Successfully created account')
        return render_template('register/register.almost-done.html', email=email_address)

    else:
        return render_template('register/register.enter-your-details.html', form=form, errors=form.errors)


@register_bp.route('/share-surveys/create-account/enter-account-details', methods=['GET', 'POST'])
def share_surveys_register_enter_your_details():
    """
     Registration endpoint for account creation and verification against share surveys (Account does not exist)
    :return:
    :rtype:
    """
    # Get and decrypt enrolment code
    batch_no = request.args.get('batch_no', None)
    email = request.args.get('email', None)
    form = ShareSurveyRegistrationForm(request.values, batch_no=batch_no, email=email)

    # Validate batch_no before rendering or checking the form
    party_controller.get_share_surveys_batch_number(batch_no)

    if request.method == 'POST' and form.validate():
        logger.info('Attempting to create account against share surveys email address')
        email_address = form.email.data
        registration_data = {
            'emailAddress': email_address,
            'firstName': request.form.get('first_name'),
            'lastName': request.form.get('last_name'),
            'password': request.form.get('password'),
            'telephone': request.form.get('phone_number'),
            'batch_no': batch_no,
        }

        try:
            logger.info('Calling party service to create account against share surveys email address')
            party_controller.create_share_survey_account(registration_data)
        except ApiError as exc:
            if exc.status_code == 400:
                logger.info('share surveys email address already in use')
                error = {"email_address": ["This email has already been used to register an account"]}
                return render_template('register/register-share-survey-enter-your-details.html', form=form,
                                       errors=error,
                                       email=email)
            else:
                logger.error('Failed to create/register new account  against share surveys email address',
                             status=exc.status_code)
                raise exc

        logger.info('Successfully created/registered new account against share surveys email address')
        return render_template('register/register-share-survey-registration-complete.html')

    else:
        return render_template('register/register-share-survey-enter-your-details.html', form=form, errors=form.errors,
                               email=email)
