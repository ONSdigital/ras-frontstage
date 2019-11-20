import logging

from flask import redirect, render_template, request, url_for, abort, current_app as app
from itsdangerous import BadSignature, SignatureExpired, BadData
from structlog import wrap_logger

from frontstage.controllers import party_controller
# from frontstage.controllers import oauth_controller
# from frontstage.controllers.notify_controller import NotifyController
# from frontstage.exceptions.exceptions import NotifyError
# from frontstage.exceptions.exceptions import ApiError
from frontstage.models import ResetPasswordForm
from frontstage.views.passwords import passwords_bp
from frontstage.common import verification
# from frontstage.exceptions.exceptions import NotifyError
# from frontstage.controllers.notify_controller import NotifyController
from frontstage.exceptions.exceptions import ApiError

logger = wrap_logger(logging.getLogger(__name__))


@passwords_bp.route('/reset-password/<token>', methods=['GET'])
def get_reset_password(token, form_errors=None):
    form = ResetPasswordForm(request.form)

    try:
        duration = app.config['EMAIL_TOKEN_EXPIRY']
        _ = verification.decode_email_token(token, duration)
    except SignatureExpired:
        logger.warning('Token expired for frontstage reset', token=token)
        return render_template('passwords/password-expired.html', token=token)
    except (BadSignature, BadData):
        logger.warning('Invalid token sent to frontstage password reset', token=token)
        return render_template('passwords/password-expired.html', token=token)

    # try:
    #     party_controller.verify_token(token)
    # except ApiError as exc:
    #     if exc.status_code == 409:
    #         logger.warning('Token expired', api_url=exc.url, api_status_code=exc.status_code, token=token)
    #         return render_template('passwords/password-expired.html', token=token)
    #     elif exc.status_code == 404:
    #         logger.warning('Invalid token sent to party service', api_url=exc.url, api_status_code=exc.status_code,
    #                        token=token)
    #         abort(404)
    #     else:
    #         raise exc

    template_data = {
        "error": {
            "type": form_errors
        },
        'token': token
    }
    return render_template('passwords/reset-password.html', form=form, data=template_data)


@passwords_bp.route('/reset-password/<token>', methods=['POST'])
def post_reset_password(token):
    form = ResetPasswordForm(request.form)

    if not form.validate():
        return get_reset_password(token, form_errors=form.errors)

    password = request.form.get('password')

    try:
        party_controller.change_password(password, token)
    except ApiError as exc:
        if exc.status_code == 409:
            logger.warning('Token expired', api_url=exc.url, api_status_code=exc.status_code, token=token)
            return render_template('passwords/password-expired.html', token=token)
        elif exc.status_code == 404:
            logger.warning('Invalid token sent to party service', api_url=exc.url, api_status_code=exc.status_code,
                           token=token)
            abort(404)
        else:
            raise exc

    logger.info('Successfully changed user password', token=token)
    return redirect(url_for('passwords_bp.reset_password_confirmation'))


@passwords_bp.route('/reset-password/confirmation', methods=['GET'])
def reset_password_confirmation():
    return render_template('passwords/reset-password.confirmation.html')


@passwords_bp.route('/resend-password-email-expired-token/<token>', methods=['GET'])
def resend_password_email_expired_token(token):
    # email = verification.decode_email_token(token)
    # return send_password_change_email(email)

    party_controller.resend_password_email_expired_token(token)
    logger.info('Re-sent password email for expired token.', token=token)
    return redirect(url_for('passwords_bp.reset_password_check_email'))


@passwords_bp.route('/reset-password/check-email', methods=['GET'])
def reset_password_check_email():
    return render_template('passwords/reset-password.check-email.html')


# def send_confirm_change_email(email):
#     first_name = oauth_controller.get_first_name_by_email(email)
#     if first_name != "":
#         personalisation = {
#             'FIRST_NAME': first_name
#         }
#
#         try:
#             NotifyController().request_to_notify(email=email,
#                                                  template_name='confirm_password_change',
#                                                  personalisation=personalisation)
#         except NotifyError as e:
#             # This shouldn't show the client an error - the password change was still successful.
#             # They just won't get a confirmation email
#             logger.error('Error sending password change confirmation email to Notify Gateway', msg=e.description)


# def send_password_change_email(email):
#     url_safe_serializer = URLSafeSerializer(app.config['SECRET_KEY'])
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
