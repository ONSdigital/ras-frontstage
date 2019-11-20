import logging

from flask import abort, redirect, render_template, request, url_for
from itsdangerous import URLSafeSerializer, BadSignature
from structlog import wrap_logger

from frontstage import app
# from frontstage.controllers import oauth_controller
from frontstage.controllers import party_controller
from frontstage.exceptions.exceptions import UserDoesNotExist
from frontstage.models import ForgotPasswordForm
from frontstage.views.passwords import passwords_bp
# from frontstage.common import verification
# from frontstage.exceptions.exceptions import NotifyError
# from frontstage.controllers.notify_controller import NotifyController

logger = wrap_logger(logging.getLogger(__name__))


BAD_AUTH_ERROR = 'Unauthorized user credentials'

url_safe_serializer = URLSafeSerializer(app.config['SECRET_KEY'])


@passwords_bp.route('/forgot-password', methods=['GET'])
def get_forgot_password():
    form = ForgotPasswordForm(request.form)
    return render_template('passwords/forgot-password.html', form=form)


@passwords_bp.route('/forgot-password', methods=['POST'])
def post_forgot_password():
    # form = ForgotPasswordForm(request.form)
    # form.email_address.data = form.email_address.data.strip()
    # email = form.data.get('email_address')
    #
    # if form.validate():
    #     return send_password_change_email(email)
    #
    # return render_template('passwords/forgot-password.html', form=form, email=email)

    form = ForgotPasswordForm(request.form)
    form.email_address.data = form.email_address.data.strip()
    email = form.data.get('email_address')

    encoded_email = url_safe_serializer.dumps(email)

    if form.validate():

        try:
            party_controller.reset_password_request(email)
        except UserDoesNotExist:
            logger.info('Requesting password change for unregistered email in party service')
            return redirect(url_for('passwords_bp.forgot_password_check_email', email=encoded_email))

        logger.info('Successfully sent password change request email')
        return redirect(url_for('passwords_bp.forgot_password_check_email', email=encoded_email))

    return render_template('passwords/forgot-password.html', form=form, email=email)


# def send_password_change_email(email):
#     # url_safe_serializer = URLSafeSerializer(app.config['SECRET_KEY'])
#
#     first_name = oauth_controller.get_first_name_by_email(email)
#     if first_name != "":
#         internal_url = app.config['INTERNAL_WEBSITE_URL']
#         verification_url = f'{internal_url}/passwords/reset-password/{verification.generate_email_token(email)}'
#
#         logger.info('Sending password change email', verification_url=verification_url)
#
#         personalisation = {
#             'RESET_PASSWORD_URL': verification_url,
#             'FIRST_NAME': first_name
#         }
#
#         try:
#             NotifyController().request_to_notify(email=email,
#                                                  template_name='request_password_change',
#                                                  personalisation=personalisation)
#         except NotifyError as e:
#             logger.error('Error sending password change request email to Notify Gateway', msg=e.description)
#             return render_template('forgot-password-error.html')
#
#         logger.info('Successfully sent password change request email', email=url_safe_serializer.dumps(email))
#     else:
#         # We still want to render the template for an email without an account to avoid
#         # people fishing for valid emails
#         logger.info('Requested password reset for email not in UAA', email=url_safe_serializer.dumps(email))
#
#     return redirect(url_for('passwords_bp.forgot_password_check_email', email=url_safe_serializer.dumps(email)))


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
