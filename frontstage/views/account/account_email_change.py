import logging
from os import getenv

from flask import redirect, render_template, url_for, abort, request
from structlog import wrap_logger
from frontstage.controllers import party_controller
from frontstage.exceptions.exceptions import ApiError
from frontstage.views.account import account_bp

logger = wrap_logger(logging.getLogger(__name__))


@account_bp.route('/confirm-account-email-change/<token>', methods=['GET'])
def confirm_account_email_change(token):
    logger.info('Attempting to confirm account email change', token=token)

    try:
        party_controller.verify_email(token)
    except ApiError as exc:
        # Handle api errors
        if exc.status_code == 409:
            logger.info('Expired account email change verification token', token=token, api_url=exc.url,
                        api_status_code=exc.status_code)
            return render_template('account/account-email-change-confirm-link-expired.html', token=token)
        elif exc.status_code == 404:
            logger.warning('Unrecognised account email change verification token', token=token, api_url=exc.url,
                           api_status_code=exc.status_code)
            abort(404)
        else:
            logger.info('Failed to verify account email change verification email',
                        token=token, api_url=exc.url, api_status_code=exc.status_code)
            raise exc

    # Successful account activation therefore redirect back to the login screen
    logger.info('Successfully verified email change on your account', token=token)
    return render_template('account/account-email-change-confirm.html')


@account_bp.route('/resend-account-email-change-expired-token/<token>', methods=['GET'])
def resend_account_email_change_expired_token(token):
    party_controller.resend_account_email_change_expired_token(token)
    logger.info('Re-sent verification email for account email change expired token.', token=token)
    return render_template('sign-in/sign-in.verification-email-sent.html')
