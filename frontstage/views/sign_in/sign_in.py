import logging
from os import getenv

from flask import make_response, render_template, redirect, request, url_for
from structlog import wrap_logger

from frontstage import app
from frontstage.common.session import SessionHandler
from frontstage.controllers import oauth_controller, party_controller
from frontstage.exceptions.exceptions import OAuth2Error
from frontstage.jwt import encode, timestamp_token
from frontstage.models import LoginForm
from frontstage.views.sign_in import sign_in_bp
from frontstage.views.sign_in.errors_routing import RoutingAccountLocked, RoutingUnauthorizedUserCredentials, \
    RoutingUnVerifiedError, RoutingUnVerifiedUserAccount

logger = wrap_logger(logging.getLogger(__name__))


BAD_AUTH_ERROR = 'Unauthorized user credentials'
NOT_VERIFIED_ERROR = 'User account not verified'
USER_ACCOUNT_LOCKED = 'User account locked'

NOT_EXPECTED = "not expected"
__DATA = {"error": {"type": "failed"}}

__ERROR_ROUTES = {BAD_AUTH_ERROR: RoutingUnauthorizedUserCredentials('sign-in/sign-in.html', __DATA),
                  NOT_VERIFIED_ERROR: RoutingUnVerifiedUserAccount('sign-in/sign-in.account-not-verified.html'),
                  USER_ACCOUNT_LOCKED: RoutingAccountLocked('sign-in/sign-in.account-locked.html', __DATA)}


@app.route('/', methods=['GET'])
def home():
    return redirect(url_for('sign_in_bp.login', _external=True, _scheme=getenv('SCHEME', 'http')))


@sign_in_bp.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    account_activated = request.args.get('account_activated', None)

    if request.method == 'POST' and form.validate():
        username = request.form.get('username') # This is actually the email address of the user, used as username.
        password = request.form.get('password')

        # At this stage we are checking if teh user is registered
        party_id = __validate_accout(username, form)

        # Take our raw token and add a UTC timestamp to the expires_at attribute
        data_dict = {**__get_auth_token(username, password, form), 'party_id': party_id}
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


def __validate_accout(username, form):
    party_json = party_controller.get_respondent_by_email(username)
    if not party_json or 'id' not in party_json:
        logger.info('Respondent not able to sign in as they don\'t have an active account in the system.')
        return render_template('sign-in/sign-in.html', form=form, data={"error": {"type": "failed"}})

    return party_json['id']


def __get_auth_token(username, password, form):

    try:
        return oauth_controller.sign_in(username, password)
    except OAuth2Error as exc:
        route_validator = __ERROR_ROUTES.get(exc.oauth2_error, RoutingUnVerifiedError('sign-in/sign-in.html', __DATA))
        return route_validator.log_message().notify_user(username, "name").route_me(form)


