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
            return render_template('register/register.enter-your-details.html', form=form, errors=error)
        elif response.status_code != 201:
            logger.error('Failed to create account', status=response.status_code)
            raise ApiError(response)

        logger.info('Successfully created account')
        return render_template('register/register.almost-done.html', email=request.form.get('email_address'))

    else:
        # Validate enrolment code before rendering form
        response = api_call('POST', app.config['VALIDATE_ENROLMENT'],
                            json={'enrolment_code': enrolment_code})
        if response.status_code != 200:
            logger.error('Failed to validate enrolment code')
            if response.status_code == 401:
                logger.error('Invalid enrolment code used')
            raise ApiError(response)

        return render_template('register/register.enter-your-details.html', form=form, errors=form.errors)
