import json
import logging
from os import getenv

from flask import Blueprint, render_template, request, redirect, url_for
import requests
from structlog import wrap_logger

from frontstage import app
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
        post_data = {"email_address": email_address}

        try:
            token_url = app.config['ONS_TOKEN']

            data = {
                'grant_type': 'reset_password',
                'client_id': app.config['RAS_FRONTSTAGE_CLIENT_ID'],
                'client_secret': app.config['RAS_FRONTSTAGE_CLIENT_SECRET'],
                'username': email_address,
            }
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            }

            oauth2_response = requests.post(url=token_url, data=data,
                                            headers=headers, auth=(app.config['RAS_FRONTSTAGE_CLIENT_ID'],
                                                                   app.config['RAS_FRONTSTAGE_CLIENT_SECRET']))
            # Check to see that this user account is not locked
            if oauth2_response.status_code == 401:
                oauth2Error = json.loads(oauth2_response.text)
                if 'Unauthorized user credentials' in oauth2Error['detail']:
                    logger.warning('Email address is not registered')
                    template_data = {"error": {"type": {"Email address is not registered"}}}
                    return render_template('passwords/forgot-password.html', _theme='default', form=form,
                                           data=template_data)
                elif 'User account locked' in oauth2Error['detail']:
                    logger.warning('Trying to reset password when user account is locked on the OAuth2 server')
                else:
                    logger.error('OAuth 2 server generated 401 which is not understood',
                                 oauth2error=oauth2Error.get('detail'))

                return render_template('passwords/reset-password.trouble.html', _theme='default',
                                       data={"error": {"type": "failed"}})
            if oauth2_response.status_code != 201:
                logger.error('Unknown error from the OAuth2 server')
                raise ExternalServiceError(oauth2_response)
        except requests.ConnectionError as e:
            logger.warning('Connection error between the server and the OAuth2 service of: {}'.format(exception=str(e)))
            raise ExternalServiceError(e)

        url = app.config['RAS_PARTY_RESET_PASSWORD_REQUEST'].format(app.config['RAS_PARTY_SERVICE'])
        response = requests.post(url, auth=app.config['BASIC_AUTH'], json=post_data, verify=False)
        if response.status_code == 404:
            logger.warning('Email address is not registered')
            template_data = {"error": {"type": {"Email address is not registered"}}}
            return render_template('passwords/forgot-password.html', _theme='default', form=form, data=template_data)
        if response.status_code != 200:
            logger.error('Failed to send password change request email')
            raise ExternalServiceError(response)
        logger.debug('Successfully sent password change request email')
        return redirect(url_for('passwords_bp.forgot_password_check_email'))

    template_data = {
        "error": {
            "type": form.errors
        }
    }
    return render_template('passwords/forgot-password.html', _theme='default', form=form, data=template_data)


@passwords_bp.route('/forgot-password/check-email', methods=['GET', 'POST'])
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
