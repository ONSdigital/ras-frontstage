import logging
from os import getenv

from flask import redirect, render_template, url_for
from structlog import wrap_logger

from frontstage import app
from frontstage.common.api_call import api_call
from frontstage.common.cryptographer import Cryptographer
from frontstage.exceptions.exceptions import ApiError
from frontstage.views.register import register_bp


logger = wrap_logger(logging.getLogger(__name__))
cryptographer = Cryptographer()


@register_bp.route('/activate-account/<token>', methods=['GET'])
def register_activate_account(token):
    logger.info('Attempting to verify email')
    response = api_call('PUT', app.config['VERIFY_EMAIL'], parameters={'token': token})

    # Handle api errors
    if response.status_code == 409:
        logger.info('Expired email verification token', token=token)
        return render_template('register/register.link-expired.html')
    elif response.status_code == 404:
        logger.warning('Unrecognised email verification token', token=token)
        return redirect(url_for('error_bp.not_found_error_page'))
    elif response.status_code != 200:
        logger.info('Failed to verify email')
        raise ApiError(response)

    # Successful account activation therefore redirect back to the login screen
    logger.info('Successfully verified email')
    return redirect(url_for('sign_in_bp.login',
                            account_activated=True,
                            _external=True,
                            _scheme=getenv('SCHEME', 'http')))
