import logging
from os import getenv

from flask import make_response, render_template, redirect, request, url_for
from structlog import wrap_logger

from frontstage import app
from frontstage.common.api_call import api_call
from frontstage.common.session import SessionHandler
from frontstage.controllers import oauth_controller, party_controller
from frontstage.exceptions.exceptions import ApiError, OAuth2Error
from frontstage.jwt import encode, timestamp_token
from frontstage.models import LoginForm
from frontstage.views.sign_in import sign_in_bp


logger = wrap_logger(logging.getLogger(__name__))


ACCOUNT_LOCKED_ERROR = 'User account locked'
BAD_AUTH_ERROR = 'Unauthorized user credentials'
NOT_VERIFIED_ERROR = 'User account not verified'


@app.route('/', methods=['GET'])
def home():
    return redirect(url_for('sign_in_bp.login', _external=True, _scheme=getenv('SCHEME', 'http')))


@sign_in_bp.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    account_activated = request.args.get('account_activated', None)

    if request.method == 'POST' and form.validate():
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            oauth2_token = oauth_controller.sign_in(username, password)
        except OAuth2Error as exc:
            error_message = exc.message
            if BAD_AUTH_ERROR in error_message:
                return render_template('sign-in/sign-in.html', form=form, data={"error": {"type": "failed"}})
            elif ACCOUNT_LOCKED_ERROR in error_message:
                logger.debug('User account is locked on the OAuth2 server')
                return render_template('sign-in/sign-in.trouble.html', form=form, data={"error": {"type": "account locked"}})
            elif NOT_VERIFIED_ERROR in error_message:
                logger.debug('User account is not verified on the OAuth2 server')
                return render_template('sign-in/sign-in.account-not-verified.html', form=form,
                                       data={"error": {"type": "account not verified"}})
            logger.error('OAuth 2 server generated 401 which is not understood',
                         oauth2error=error_message)
            return render_template('sign-in/sign-in.html', form=form, data={"error": {"type": "failed"}})

        # NB: currently not handling a failed response from the party service
        party_id = party_controller.get_party_by_email(username).get('id')
        # Take our raw token and add a UTC timestamp to the expires_at attribute
        data_dict = {**oauth2_token, 'party_id': party_id}
        data_dict_for_jwt_token = timestamp_token(data_dict)
        encoded_jwt_token = encode(data_dict_for_jwt_token)
        response = make_response(redirect(url_for('surveys_bp.logged_in', _external=True,
                                                  _scheme=getenv('SCHEME', 'http'))))

        session = SessionHandler()
        logger.info('Creating session', party_id=party_id)
        session.create_session(encoded_jwt_token)
        response.set_cookie('authorization',
                            value=session.session_key,
                            expires=data_dict_for_jwt_token['expires_at'])
        logger.info('Successfully created session', party_id=party_id, session_key=session.session_key)
        return response

    template_data = {
        "error": {
            "type": form.errors,
            "logged_in": "False"
        },
        'account_activated': account_activated
    }
    return render_template('sign-in/sign-in.html', form=form, data=template_data)
