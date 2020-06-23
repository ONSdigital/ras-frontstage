import logging
from os import getenv

from flask import make_response, render_template, redirect, request, url_for
from structlog import wrap_logger

from frontstage import app
from frontstage.common.session import Session
from frontstage.common.utilities import obfuscate_email
from frontstage.controllers import auth_controller, party_controller
from frontstage.controllers.party_controller import notify_party_and_respondent_account_locked
from frontstage.controllers import conversation_controller
from frontstage.exceptions.exceptions import AuthError
from frontstage.models import LoginForm
from frontstage.views.sign_in import sign_in_bp


logger = wrap_logger(logging.getLogger(__name__))

UNKNOWN_ACCOUNT_ERROR = 'Authentication error in Auth service'
BAD_AUTH_ERROR = 'Unauthorized user credentials'
NOT_VERIFIED_ERROR = 'User account not verified'
USER_ACCOUNT_LOCKED = 'User account locked'


@app.route('/', methods=['GET'])
def home():
    return redirect(url_for('sign_in_bp.login', _external=True, _scheme=getenv('SCHEME', 'http')))


@sign_in_bp.route('/', methods=['GET', 'POST'])
def login():  # noqa: C901
    form = LoginForm(request.form)
    form.username.data = form.username.data.strip()
    account_activated = request.args.get('account_activated', None)

    secure = app.config['WTF_CSRF_ENABLED']

    if request.method == 'POST' and form.validate():
        username = form.username.data
        password = request.form.get('password')
        bound_logger = logger.bind(email=obfuscate_email(username))
        bound_logger.info("Attempting to find user in auth service")
        try:
            auth_controller.sign_in(username, password)
        except AuthError as exc:
            error_message = exc.auth_error
            party_json = party_controller.get_respondent_by_email(username)
            party_id = party_json.get('id') if party_json else None
            bound_logger = bound_logger.bind(party_id=party_id)

            if USER_ACCOUNT_LOCKED in error_message:  # pylint: disable=no-else-return
                if not party_id:
                    bound_logger.error("Respondent account locked in auth but doesn't exist in party")
                    return render_template('sign-in/sign-in.html', form=form, data={"error": {"type": "failed"}})
                bound_logger.info('User account is locked on the Auth server', status=party_json['status'])
                if party_json['status'] == 'ACTIVE' or party_json['status'] == 'CREATED':
                    notify_party_and_respondent_account_locked(respondent_id=party_id,
                                                               email_address=username,
                                                               status='SUSPENDED')
                return render_template('sign-in/sign-in.account-locked.html', form=form)
            elif NOT_VERIFIED_ERROR in error_message:
                bound_logger.info('User account is not verified on the Auth server')
                return render_template('sign-in/sign-in.account-not-verified.html', party_id=party_id)
            elif BAD_AUTH_ERROR in error_message:
                bound_logger.info('Bad credentials provided')
            elif UNKNOWN_ACCOUNT_ERROR in error_message:
                bound_logger.info('User account does not exist in auth service')
            else:
                bound_logger.error('Unexpected error was returned from Auth service', auth_error=error_message)

            return render_template('sign-in/sign-in.html', form=form, data={"error": {"type": "failed"}}, next=request.args.get('next'))

        bound_logger.info("Successfully found user in auth service.  Attempting to find user in party service")
        party_json = party_controller.get_respondent_by_email(username)
        if not party_json or 'id' not in party_json:
            bound_logger.error("Respondent has an account in auth but not in party")
            return render_template('sign-in/sign-in.html', form=form, data={"error": {"type": "failed"}})
        party_id = party_json['id']
        bound_logger = bound_logger.bind(party_id=party_id)

        if request.args.get('next'):
            response = make_response(redirect(request.args.get('next')))
        else:
            response = make_response(redirect(url_for('surveys_bp.get_survey_list', tag='todo', _external=True,
                                                      _scheme=getenv('SCHEME', 'http'))))

        bound_logger.info("Successfully found user in party service")
        bound_logger.info('Creating session')
        session = Session.from_party_id(party_id)
        response.set_cookie('authorization',
                            value=session.session_key,
                            expires=session.get_expires_in(),
                            secure=secure,
                            httponly=secure)
        count = conversation_controller.get_message_count_from_api(session)
        session.set_unread_message_total(count)
        bound_logger.info('Successfully created session', session_key=session.session_key)
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


@sign_in_bp.route('/resend_verification/<party_id>', methods=['GET'])       # Deprecated: to be removed when not in use
@sign_in_bp.route('/resend-verification/<party_id>', methods=['GET'])
def resend_verification(party_id):
    party_controller.resend_verification_email(party_id)
    logger.info('Re-sent verification email.', party_id=party_id)
    return render_template('sign-in/sign-in.verification-email-sent.html')


@sign_in_bp.route('/resend-verification-expired-token/<token>', methods=['GET'])
def resend_verification_expired_token(token):
    party_controller.resend_verification_email_expired_token(token)
    logger.info('Re-sent verification email for expired token.', token=token)
    return render_template('sign-in/sign-in.verification-email-sent.html')
