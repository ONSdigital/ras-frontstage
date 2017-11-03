import json
import logging

from flask import Blueprint, render_template, request, redirect, url_for
import requests
from structlog import wrap_logger

from frontstage import app
from frontstage.common.api_call import api_call
from frontstage.exceptions.exceptions import ApiError
from frontstage.exceptions.exceptions import ExternalServiceError
from frontstage.models import ForgotPasswordForm, ResetPasswordForm


logger = wrap_logger(logging.getLogger(__name__))

passwords_bp = Blueprint('passwords_bp', __name__, static_folder='static', template_folder='templates/passwords')


# ===== Forgot password =====
@passwords_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm(request.form)

    if request.method == 'POST' and form.validate():
        email_address = request.form.get('email_address')
        post_data = {"username": email_address}

        response = api_call('POST', app.config['REQUEST_PASSWORD_CHANGE'], json=post_data)

        if response.status_code == 401:
            error_json = json.loads(response.text).get('error')
            error_message = error_json.get('data', {}).get('detail')
            if 'Unauthorized user credentials' in error_message:
                logger.info('Requesting password change for unregistered email on OAuth2 server')
                template_data = {"error": {"type": {"Email address is not registered"}}}
                return render_template('passwords/forgot-password.html', _theme='default', form=form, data=template_data)
            elif 'User account locked' in error_message:
                logger.warning('Requesting password change for locked email on OAuth2 server')
            else:
                logger.warning('Unknown 401 OAuth2 error')
            return render_template('passwords/reset-password.trouble.html', _theme='default',
                                   data={"error": {"type": "failed"}})

        elif response.status_code == 404:
            logger.error('Requesting password change for email registered on OAuth2 server but not in party service')
            template_data = {"error": {"type": {"Email address is not registered"}}}
            return render_template('passwords/forgot-password.html', _theme='default', form=form, data=template_data)

        if response.status_code != 200:
            logger.error('Unable to send password change request')
            raise ApiError(response)

        logger.debug('Successfully sent password change request email')

        return redirect(url_for('passwords_bp.forgot_password_check_email'))

    template_data = {
        "error": {
            "type": form.errors
        }
    }
    return render_template('passwords/forgot-password.html', _theme='default', form=form, data=template_data)


@passwords_bp.route('/forgot-password/check-email', methods=['GET'])
def forgot_password_check_email():
    return render_template('passwords/forgot-password.check-email.html', _theme='default')


# ===== Reset password =====
@passwords_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    form = ResetPasswordForm(request.form)
    url = app.config['RAS_PARTY_VERIFY_PASSWORD_TOKEN'].format(app.config['RAS_PARTY_SERVICE'], token)
    response = requests.get(url, auth=app.config['BASIC_AUTH'], verify=False)
    if response.status_code == 409:
        logger.warning('Token expired', token=token)
        return render_template('passwords/password-expired.html', _theme='default')
    elif response.status_code == 404:
        logger.warning('Invalid token sent to party service', token=token)
        return redirect(url_for('error_bp.not_found_error_page'))
    elif response.status_code != 200:
        logger.error('Party service failed to verify token')
        raise ExternalServiceError(response)

    if request.method == 'POST' and form.validate():
        password = request.form.get('password')
        put_data = {
            "new_password": password
        }

        url = app.config['RAS_PARTY_CHANGE_PASSWORD'].format(app.config['RAS_PARTY_SERVICE'], token)
        response = requests.put(url, auth=app.config['BASIC_AUTH'], json=put_data, verify=False)

        if response.status_code != 200:
            logger.error('Failed to change user password', token=token)
            raise ExternalServiceError(response)
        logger.info('Successfully change user password', token=token)
        return redirect(url_for('passwords_bp.reset_password_confirmation'))

    template_data = {
        "error": {
            "type": form.errors
        },
        'token': token
    }
    return render_template('passwords/reset-password.html', _theme='default', form=form, data=template_data)


@passwords_bp.route('/reset-password/confirmation', methods=['GET', 'POST'])
def reset_password_confirmation():
    return render_template('passwords/reset-password.confirmation.html', _theme='default')
