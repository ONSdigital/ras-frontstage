import logging

from flask import abort, redirect, render_template, request, url_for
from itsdangerous import URLSafeSerializer, BadSignature
from structlog import wrap_logger
# from werkzeug.exceptions import NotFound

from frontstage import app
from frontstage.views.passwords import reset_password
# from frontstage.controllers import party_controller
# from frontstage.exceptions.exceptions import UserDoesNotExist
from frontstage.models import ForgotPasswordForm
from frontstage.views.passwords import passwords_bp
# from frontstage.common import verification
# from frontstage.exceptions.exceptions import NotifyError
# from frontstage.controllers.notify_controller import NotifyController
# from frontstage.controllers import party_controller
# from frontstage.common import verification
# from frontstage.exceptions.exceptions import RasNotifyError
# from frontstage.controllers.notify_controller import NotifyGateway

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
    email = form.data.get('email_address').strip()

    if form.validate():
        return reset_password.request_password_change(email)

    return render_template('passwords/forgot-password.html', form=form, email=email)


# @passwords_bp.route('/forgot-password', methods=['POST'])
# def post_forgot_password():
#     form = ForgotPasswordForm(request.form)
#     form.email_address.data = form.email_address.data.strip()
#     email = form.data.get('email_address')
#
#     encoded_email = url_safe_serializer.dumps(email)
#
#     if form.validate():
#
#         try:
#             party_controller.reset_password_request(email)
#         except UserDoesNotExist:
#             logger.info('Requesting password change for unregistered email in party service')
#             return redirect(url_for('passwords_bp.forgot_password_check_email', email=encoded_email))
#
#         logger.info('Successfully sent password change request email')
#         return redirect(url_for('passwords_bp.forgot_password_check_email', email=encoded_email))
#
#     return render_template('passwords/forgot-password.html', form=form, email=email)


@passwords_bp.route('/forgot-password/check-email', methods=['GET'])
def forgot_password_check_email():
    encoded_email = request.args.get('email', None)

    if encoded_email is None:
        logger.error('No email parameter supplied')
        return redirect(url_for('passwords_bp.get_forgot_password'))

    try:
        email = url_safe_serializer.loads(encoded_email)
    except BadSignature:
        logger.error('Unable to decode email from URL', encoded_email=encoded_email)
        abort(404)

    return render_template('passwords/forgot-password.check-email.html', email=email)
