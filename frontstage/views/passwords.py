import logging
from os import getenv

from flask import Blueprint, render_template, request, redirect, url_for
from structlog import wrap_logger

from frontstage.models import ForgotPasswordForm, ResetPasswordForm


logger = wrap_logger(logging.getLogger(__name__))

passwords_bp = Blueprint('passwords_bp', __name__, static_folder='static', template_folder='templates/passwords')


# ===== Forgot password =====
@passwords_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():

    form = ForgotPasswordForm(request.form)

    if request.method == 'POST' and form.validate():

        email_address = request.form.get('email_address')

        # TODO do some kind of back end processing to validate the email address, error handling, logging
        # print('Email address=' + email_address)

        return redirect(url_for('passwords_bp.forgot_password_check_email',
                                _external=True,
                                _scheme=getenv('SCHEME', 'http')))

    template_data = {
        "error": {
            "type": form.errors
        }
    }

    return render_template('passwords/forgot-password.html', _theme='default', form=form, data=template_data)


@passwords_bp.route('/forgot-password/check-email', methods=['GET', 'POST'])
def forgot_password_check_email():
    return render_template('passwords/forgot-password.check-email.html', _theme='default')


# ===== Reset password =====
@passwords_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):

    form = ResetPasswordForm(request.form)

    # TODO validate the token

    if request.method == 'POST' and form.validate():
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        print('password=' + password)
        print('password_confirm=' + password_confirm)

        # TODO do some kind of back end processing to change the password, error handling, logging

        return redirect(url_for('passwords_bp.reset_password_confirmation'))

    template_data = {
        "error": {
            "type": form.errors
        },
        'token': token
    }
    return render_template('passwords/reset-password.html', _theme='default', form=form, data=template_data)


@passwords_bp.route('/reset-password/confirmation', methods=['GET', 'POST'])
def reset_password_confirmation():
    return render_template('passwords/reset-password.confirmation.html', _theme='default')
