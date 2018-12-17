import logging
from os import getenv

from flask import make_response, render_template, redirect, request, url_for
from structlog import wrap_logger

from frontstage import app
from frontstage.common.session import SessionHandler
from frontstage.controllers import oauth_controller, party_controller
from frontstage.controllers.party_controller import notify_party_and_respondent_account_locked
from frontstage.exceptions.exceptions import OAuth2Error
from frontstage.jwt import encode, timestamp_token
from frontstage.models import LoginForm
from frontstage.views.sign_in import sign_in_bp


logger = wrap_logger(logging.getLogger(__name__))


BAD_AUTH_ERROR = 'Unauthorized user credentials'
NOT_VERIFIED_ERROR = 'User account not verified'
USER_ACCOUNT_LOCKED = 'User account locked'


@app.route('/', methods=['GET'])
def home():
    return redirect(url_for('sign_in_bp.login', _external=True, _scheme=getenv('SCHEME', 'http')))


def get_oauth_token(username, password, party_id, party_json, form):
    try:
        oauth2_token = oauth_controller.sign_in(username, password)
        return oauth2_token
    except OAuth2Error as exc:
        error_message = exc.oauth2_error
        if USER_ACCOUNT_LOCKED in error_message:
            logger.info('User account is locked on the OAuth2 server', party_id=party_id)
            if party_json['status'] == 'ACTIVE' or party_json['status'] == 'CREATED':
                notify_party_and_respondent_account_locked(respondent_id=party_id,
                                                           email_address=username,
                                                           status='SUSPENDED')
            return render_template('sign-in/sign-in.account-locked.html', form=form)
        elif BAD_AUTH_ERROR in error_message:
            return render_template('sign-in/sign-in.html', form=form, data={"error": {"type": "failed"}})
        elif NOT_VERIFIED_ERROR in error_message:
            logger.info('User account is not verified on the OAuth2 server')
            return render_template('sign-in/sign-in.account-not-verified.html', party_id=party_id,
                                   email=username)
        else:
            logger.info('OAuth 2 server generated 401 which is not understood', oauth2_error=error_message)
            return render_template('sign-in/sign-in.html', form=form, data={"error": {"type": "failed"}})


@sign_in_bp.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    form.username.data = form.username.data.strip()
    account_activated = request.args.get('account_activated', None)

    if request.method == 'POST' and form.validate():
        username = form.username.data
        password = request.form.get('password')

        party_json = party_controller.get_respondent_by_email(username)
        if not party_json or 'id' not in party_json:
            logger.info('Respondent not able to sign in as they don\'t have an active account in the system.')
            return render_template('sign-in/sign-in.html', form=form, data={"error": {"type": "failed"}})
        party_id = party_json['id']

        oauth2_token = get_oauth_token(username, password, party_id, party_json, form)

        if not isinstance(oauth2_token, dict):
            return oauth2_token

        # Take our raw token and add a UTC timestamp to the expires_at attribute
        data_dict = {**oauth2_token, 'party_id': party_id}
        data_dict_for_jwt_token = timestamp_token(data_dict)
        encoded_jwt_token = encode(data_dict_for_jwt_token)
        if request.args.get('next'):
            response = make_response(redirect(request.args.get('next')))
        else:
            response = make_response(redirect(url_for('surveys_bp.get_survey_list', tag='todo', _external=True,
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
    if request.args.get('next'):
        return render_template('sign-in/sign-in.html', form=form, data=template_data,
                               next=request.args.get('next'))
    return render_template('sign-in/sign-in.html', form=form, data=template_data)


@sign_in_bp.route('/resend_verification/<party_id>', methods=['GET'])
def resend_verification(party_id):
    party_controller.resend_verification_email(party_id)
    logger.info('Re-sent verification email.', party_id=party_id)
    return render_template('sign-in/sign-in.verification-email-sent.html')


@sign_in_bp.route('/resend-verification-expired-token/<token>', methods=['GET'])
def resend_verification_expired_token(token):
    party_controller.resend_verification_email_expired_token(token)
    logger.info('Re-sent verification email for expired token.', token=token)
    return render_template('sign-in/sign-in.verification-email-sent.html')
