import logging

from flask import render_template, request
from structlog import wrap_logger

from frontstage import app
from frontstage.common.api_call import api_call
from frontstage.common.cryptographer import Cryptographer
from frontstage.exceptions.exceptions import ApiError
from frontstage.models import RegistrationForm
from frontstage.views.register import register_bp


logger = wrap_logger(logging.getLogger(__name__))
cryptographer = Cryptographer()


@register_bp.route('/create-account/enter-account-details', methods=['GET', 'POST'])
def register_enter_your_details():
    # Get and decrypt enrolment code
    encrypted_enrolment_code = request.args.get('encrypted_enrolment_code', None)
    enrolment_code = cryptographer.decrypt(encrypted_enrolment_code.encode()).decode()
    form = RegistrationForm(request.values, enrolment_code=encrypted_enrolment_code)

    # Validate enrolment code before rendering or checking the form
    iac_controller.validate_enrolment_code(enrolment_code)

    if request.method == 'POST' and form.validate():
        logger.info('Attempting to create account')
        email_address = request.form.get('email_address')
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
                logger.debug('Email already used')
                error = {"email_address": ["This email has already been used to register an account"]}
                return render_template('register/register.enter-your-details.html', form=form, errors=error)
            else:
                logger.error('Failed to create account', status=exc.status_code)
                raise exc

        logger.info('Successfully created account')
        return render_template('register/register.almost-done.html', email=email_address)

    else:
        return render_template('register/register.enter-your-details.html', form=form, errors=form.errors)
