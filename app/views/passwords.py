import logging
from flask import Blueprint, render_template, request
from structlog import wrap_logger

logger = wrap_logger(logging.getLogger(__name__))
passwords_bp = Blueprint('passwords_bp', __name__, static_folder='static', template_folder='templates/passwords')


# ===== Forgot password =====
@passwords_bp.route('/forgot-password/')
def forgot_password():
    template_data = {
        "error": {
            "type": request.args.get("error")
        }
    }

    # data variables configured: {"error": <undefined, failed>}
    return render_template('passwords/forgot-password.html', _theme='default', data=template_data)


@passwords_bp.route('/forgot-password/check-email/')
def forgot_password_check_email():
    return render_template('passwords/forgot-password.check-email.html', _theme='default')


# ===== Reset password =====
@passwords_bp.route('/reset-password/')
def reset_password():
    template_data = {
        "error": {
            "type": request.args.get("error")
        }
    }

    if 'error' in request.args:
        logger.debug(request.args.get("error"))

    # data variables configured: {"error": <undefined, password-mismatch>}
    return render_template('passwords/reset-password.html', _theme='default', data=template_data)


@passwords_bp.route('/reset-password/confirmation/')
def reset_password_confirmation():
    return render_template('passwords/reset-password.confirmation.html', _theme='default')
