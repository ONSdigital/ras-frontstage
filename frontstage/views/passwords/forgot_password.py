import logging

from flask import redirect, render_template, request, url_for
from frontstage import app
from itsdangerous import URLSafeSerializer, BadSignature
from structlog import wrap_logger

from frontstage.controllers import oauth_controller, party_controller
from frontstage.exceptions.exceptions import ApiError, OAuth2Error
from frontstage.models import ForgotPasswordForm
from frontstage.views.passwords import passwords_bp


logger = wrap_logger(logging.getLogger(__name__))


BAD_AUTH_ERROR = 'Unauthorized user credentials'

url_safe_serializer = URLSafeSerializer(app.config['SECRET_KEY'])


@passwords_bp.route('/forgot-password', methods=['GET'])
def get_forgot_password():
    form = ForgotPasswordForm(request.form)
    return render_template('passwords/forgot-password.html', form=form)


@passwords_bp.route('/forgot-password', methods=['POST'])
def post_forgot_password():
    form = ForgotPasswordForm(request.form)
    email = form.data.get('email_address')

    encoded_email = url_safe_serializer.dumps(email)

    if form.validate():

        try:
            oauth_controller.check_account_valid(email)
        except OAuth2Error as exc:
            error_message = exc.oauth2_error
            if BAD_AUTH_ERROR in error_message:
                logger.info('Requesting password change for unregistered email on OAuth2 server')
                return redirect(url_for('passwords_bp.forgot_password_check_email', email=encoded_email))
            else:
                logger.info(exc.message, oauth2_error=error_message)
            return render_template('passwords/reset-password.trouble.html')

        try:
            party_controller.reset_password_request(email)
        except ApiError as exc:
            if exc.status_code == 404:
                logger.error('Failed to retrieve details from party service')
                return render_template('errors/404-error.html')
            raise exc

        logger.info('Successfully sent password change request email')
        return redirect(url_for('passwords_bp.forgot_password_check_email', email=encoded_email))

    return render_template('passwords/forgot-password.html', form=form, email=email)


@passwords_bp.route('/forgot-password/check-email', methods=['GET'])
def forgot_password_check_email():
    encoded_email = request.args.get('email', None)

    if encoded_email is None:
        logger.error('No email parameter supplied')
        return redirect('passwords/forgot-password')

    try:
        email = url_safe_serializer.loads(encoded_email)
    except BadSignature:
        logger.error('Unable to decode email from URL', encoded_email=encoded_email)
        return render_template('errors/404-error.html'), 404

    return render_template('passwords/forgot-password.check-email.html', email=email)
