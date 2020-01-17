import logging

from flask import redirect, render_template, request, url_for, abort, current_app as app
from itsdangerous import BadSignature, SignatureExpired, BadData
from structlog import wrap_logger

from frontstage.controllers import party_controller

from frontstage.models import ResetPasswordForm
from frontstage.views.passwords import passwords_bp
from frontstage.common import verification

from frontstage.controllers.notify_controller import NotifyGateway
from frontstage.exceptions.exceptions import ApiError
from frontstage.exceptions.exceptions import RasNotifyError

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
        duration = app.config['EMAIL_TOKEN_EXPIRY']
        email = verification.decode_email_token(token, duration)
        party_controller.change_password(email, password)
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


@passwords_bp.route('/reset-password/check-email', methods=['GET'])
def reset_password_check_email():
    return render_template('passwords/reset-password.check-email.html')


@passwords_bp.route('/resend-password-email-expired-token/<token>', methods=['GET'])
def resend_password_email_expired_token(token):
    email = verification.decode_email_token(token)
    return request_password_change(email)


def request_password_change(email):
    respondent = party_controller.get_respondent_by_email(email)

    if not respondent:
        logger.info("Respondent does not exist")
        return redirect(url_for('passwords_bp.reset_password_check_email'))

    party_id = str(respondent['id'])

    logger.info("Requesting password change", party_id=party_id)

    token = verification.generate_email_token(email)
    verification_url = url_for('passwords_bp.post_reset_password', token=token)
    personalisation = {
        'RESET_PASSWORD_URL': verification_url,
        'FIRST_NAME': respondent['firstName']
    }

    # If we don't have a gov notify to send to, log it out so we can simulate following the url
    if not app.config['SEND_EMAIL_TO_GOV_NOTIFY']:
        logger.info('Reset password url', url=verification_url, party_id=party_id)

    try:
        NotifyGateway(app.config).request_to_notify(email=email,
                                                    template_name='request_password_change',
                                                    personalisation=personalisation,
                                                    reference=party_id)
        logger.info('Password reset email successfully sent', party_id=party_id)
    except RasNotifyError:
        # Note: intentionally suppresses exception
        logger.error('Error sending request to Notify Gateway', respondent_id=party_id, exc_info=True)

    return redirect(url_for('passwords_bp.reset_password_check_email'))
