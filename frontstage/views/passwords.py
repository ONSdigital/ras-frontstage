import json
import logging

from flask import Blueprint, redirect, render_template, request, url_for
from structlog import wrap_logger

from frontstage import app
from frontstage.common.api_call import api_call
from frontstage.exceptions.exceptions import ApiError
from frontstage.models import ForgotPasswordForm, ResetPasswordForm


logger = wrap_logger(logging.getLogger(__name__))

passwords_bp = Blueprint('passwords_bp', __name__,
                         static_folder='static', template_folder='templates/passwords')


@passwords_bp.route('/forgot-password', methods=['GET'])
def get_forgot_password():
    form = ForgotPasswordForm(request.form)
    template_data = {
        "error": {
            "type": {}
        }
    }
    return render_template('passwords/forgot-password.html', _theme='default',
                           form=form, data=template_data)


@passwords_bp.route('/forgot-password', methods=['POST'])
def post_forgot_password():
    form = ForgotPasswordForm(request.form)

    if form.validate():
        email_address = request.form.get('email_address')
        post_data = {"username": email_address}
        response = api_call('POST', app.config['REQUEST_PASSWORD_CHANGE'], json=post_data)

        # If we receive a 401 parse the error message to display the correct reason why
        if response.status_code == 401:
            error_json = json.loads(response.text).get('error')
            error_message = error_json.get('data', {}).get('detail')
            logger.info(error_message=error_message)
            if 'Unauthorized user credentials' in error_message:
                logger.info('Requesting password change for unregistered email on OAuth2 server')
                template_data = {"error": {"type": {"Email address is not registered"}}}
                return render_template('passwords/forgot-password.html', _theme='default', form=form,
                                       data=template_data)
            return render_template('passwords/reset-password.trouble.html', _theme='default',
                                   data={"error": {"type": "failed"}})

        elif response.status_code == 404:
            logger.error('Requesting password change for email registered'
                         ' on OAuth2 server but not in party service')
            template_data = {"error": {"type": {"Email address is not registered"}}}
            return render_template('passwords/forgot-password.html', _theme='default',
                                   form=form, data=template_data)

        if response.status_code != 200:
            logger.error('Unable to send password change request', status=response.status_code)
            raise ApiError(response)

        logger.debug('Successfully sent password change request email')
        return redirect(url_for('passwords_bp.forgot_password_check_email'))

    template_data = {
        "error": {
            "type": form.errors
        }
    }
    return render_template('passwords/forgot-password.html', _theme='default',
                           form=form, data=template_data)


@passwords_bp.route('/forgot-password/check-email', methods=['GET'])
def forgot_password_check_email():
    return render_template('passwords/forgot-password.check-email.html', _theme='default')


@passwords_bp.route('/reset-password/<token>', methods=['GET'])
def get_reset_password(token, form_errors=None):
    form = ResetPasswordForm(request.form)

    url = app.config['VERIFY_PASSWORD_TOKEN']
    parameters = {"token": token}
    response = api_call('GET', url, parameters=parameters)

    if response.status_code == 409:
        logger.warning('Token expired', token=token)
        return render_template('passwords/password-expired.html', _theme='default')
    elif response.status_code == 404:
        logger.warning('Invalid token sent to party service', token=token)
        return redirect(url_for('error_bp.not_found_error_page'))
    elif response.status_code != 200:
        logger.error('Party service failed to verify token', status=response.status_code)
        raise ApiError(response)

    template_data = {
        "error": {
            "type": form_errors
        },
        'token': token
    }
    return render_template('passwords/reset-password.html', _theme='default',
                           form=form, data=template_data)


@passwords_bp.route('/reset-password/<token>', methods=['POST'])
def post_reset_password(token):
    form = ResetPasswordForm(request.form)

    if not form.validate():
        return get_reset_password(token, form_errors=form.errors)

    password = request.form.get('password')
    put_data = {
        "new_password": password,
        "token": token
    }

    url = app.config['CHANGE_PASSWORD']
    response = api_call('PUT', url, json=put_data)

    if response.status_code == 409:
        logger.warning('Token expired', token=token)
        return render_template('passwords/password-expired.html', _theme='default')
    elif response.status_code == 404:
        logger.warning('Invalid token sent to party service', token=token)
        return redirect(url_for('error_bp.not_found_error_page'))
    elif response.status_code != 200:
        logger.error('Party service failed to verify token', status=response.status_code)
        raise ApiError(response)

    logger.info('Successfully changed user password', token=token)
    return redirect(url_for('passwords_bp.reset_password_confirmation'))


@passwords_bp.route('/reset-password/confirmation', methods=['GET'])
def reset_password_confirmation():
    return render_template('passwords/reset-password.confirmation.html', _theme='default')
