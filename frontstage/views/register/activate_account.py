import logging
from os import getenv

from flask import redirect, render_template, url_for
from structlog import wrap_logger

from frontstage.controllers import party_controller
from frontstage.exceptions.exceptions import ApiError
from frontstage.views.register import register_bp


logger = wrap_logger(logging.getLogger(__name__))


@register_bp.route('/activate-account/<token>', methods=['GET'])
def register_activate_account(token):
    logger.info('Attempting to verify email', token=token)

    try:
        party_controller.verify_email(token)
    except ApiError as exc:
        # Handle api errors
        if exc.status_code == 409:
            logger.info('Expired email verification token', token=token)
            return render_template('register/register.link-expired.html')
        elif exc.status_code == 404:
            logger.warning('Unrecognised email verification token', token=token)
            return redirect(url_for('error_bp.not_found_error_page'))
        elif exc.status_code != 200:
            logger.info('Failed to verify email', token=token)
            raise exc

    # Successful account activation therefore redirect back to the login screen
    logger.info('Successfully verified email', token=token)
    return redirect(url_for('sign_in_bp.login',
                            account_activated=True,
                            _external=True,
                            _scheme=getenv('SCHEME', 'http')))
