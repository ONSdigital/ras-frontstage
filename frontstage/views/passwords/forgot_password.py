import json
import logging

from flask import redirect, render_template, request, url_for
from structlog import wrap_logger

from frontstage import app
from frontstage.common.api_call import api_call
from frontstage.exceptions.exceptions import ApiError
from frontstage.models import ForgotPasswordForm
from frontstage.views.passwords import passwords_bp


logger = wrap_logger(logging.getLogger(__name__))


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
            logger.error('Unable to send password change request')
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
