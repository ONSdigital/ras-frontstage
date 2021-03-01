import logging

from flask import render_template, request, flash, url_for
from structlog import wrap_logger
from werkzeug.utils import redirect

from frontstage import app
from frontstage.common.authorisation import jwt_authorization
from frontstage.common.utilities import obfuscate_email
from frontstage.controllers import party_controller, auth_controller
from frontstage.exceptions.exceptions import ApiError, AuthError
from frontstage.models import OptionsForm, ContactDetailsChangeForm, ConfirmEmailChangeForm, ChangePasswordFrom
from frontstage.views.account import account_bp

logger = wrap_logger(logging.getLogger(__name__))

BAD_AUTH_ERROR = 'Unauthorized user credentials'
form_redirect_mapper = {
    'contact_details': 'account_bp.change_account_details',
    'change_password': 'account_bp.change_password',
}


@account_bp.route('/', methods=['GET'])
@jwt_authorization(request)
def get_account(session):
    form = OptionsForm()
    party_id = session.get_party_id()
    respondent_details = party_controller.get_respondent_party_by_id(party_id)
    return render_template('account/account.html', form=form, respondent=respondent_details)


@account_bp.route('/', methods=['POST'])
@jwt_authorization(request)
def update_account(session):
    form = OptionsForm()
    form_valid = form.validate()
    if not form_valid:
        flash('At least one option should be selected.')
        return redirect(url_for('account_bp.get_account'))
    else:
        return redirect(url_for(form_redirect_mapper.get(form.data['option'])))


@account_bp.route('/change-password', methods=['GET', 'POST'])
@jwt_authorization(request)
def change_password(session):
    form = ChangePasswordFrom(request.values)
    party_id = session.get_party_id()
    respondent_details = party_controller.get_respondent_party_by_id(party_id)
    if request.method == 'POST' and form.validate():
        username = respondent_details['emailAddress']
        password = request.form.get('password')
        new_password = request.form.get('new_password')
        bound_logger = logger.bind(email=obfuscate_email(username))
        bound_logger.info("Attempting to find user in auth service")
        try:
            auth_controller.sign_in(username, password)
            bound_logger.info("Attempting to change password via party service")
            party_controller.change_password(username, new_password)
            bound_logger.info("password changed via party service")
            flash('Your password has been changed.')
            return redirect(url_for('surveys_bp.get_survey_list', tag='todo'))
        except AuthError as exc:
            error_message = exc.auth_error
            if BAD_AUTH_ERROR in error_message:
                bound_logger.info('Bad credentials provided')
                return render_template('account/account-change-password.html', form=form,
                                       errors={"password": ["Incorrect current password"]})
    else:
        errors = form.errors

    return render_template('account/account-change-password.html', form=form, errors=errors)


@account_bp.route('/change-account-email-address', methods=['POST'])
@jwt_authorization(request)
def change_email_address(session):
    form = ConfirmEmailChangeForm(request.values)
    party_id = session.get_party_id()
    respondent_details = party_controller.get_respondent_party_by_id(party_id)
    respondent_details['email_address'] = respondent_details['emailAddress']
    respondent_details['new_email_address'] = form['email_address'].data
    respondent_details['change_requested_by_respondent'] = True
    logger.info('Attempting to update email address changes on the account', party_id=party_id)
    try:
        party_controller.update_account(respondent_details)
    except ApiError as exc:
        logger.error('Failed to updated email on account', status=exc.status_code, party_id=party_id)
        raise exc
    logger.info('Successfully updated email on account', party_id=party_id)
    return render_template('account/account-change-email-address-almost-done.html')


@account_bp.route('/change-account-details', methods=['GET', 'POST'])
@jwt_authorization(request)
def change_account_details(session):
    form = ContactDetailsChangeForm(request.values)
    party_id = session.get_party_id()
    respondent_details = party_controller.get_respondent_party_by_id(party_id)
    is_contact_details_update_required = False
    attributes_changed = []
    # TODO: is_account_detail_change_enabled to be removed once account change is worked again
    is_account_email_change_enabled = app.config['ACCOUNT_EMAIL_CHANGE_ENABLED']
    if request.method == 'POST' and form.validate():
        logger.info('Attempting to update contact details changes on the account', party_id=party_id)
        # check_attribute changes also magically updates the respondent_details as a side effect of running this
        # function
        is_contact_details_update_required = check_attribute_change(form,
                                                                    attributes_changed,
                                                                    respondent_details,
                                                                    is_contact_details_update_required)
        if is_contact_details_update_required:
            try:
                party_controller.update_account(respondent_details)
            except ApiError as exc:
                logger.error('Failed to updated account', status=exc.status_code)
                raise exc
            logger.info('Successfully updated account', party_id=party_id)
            success_panel = create_success_message(attributes_changed, "We have updated your ")
            flash(success_panel)
        if is_account_email_change_enabled:
            is_email_update_required = form['email_address'].data != respondent_details['emailAddress']
            if is_email_update_required:
                return render_template('account/account-change-email-address.html',
                                       new_email=form['email_address'].data,
                                       form=ConfirmEmailChangeForm())
        return redirect(url_for('surveys_bp.get_survey_list', tag='todo'))
    else:
        return render_template('account/account-contact-detail-change.html',
                               form=form, errors=form.errors, respondent=respondent_details,
                               is_email_change_enabled=is_account_email_change_enabled)


def check_attribute_change(form, attributes_changed, respondent_details, update_required_flag):
    """
    Checks if the form data matches with the respondent details

    :param form: the form data
    :param attributes_changed: which attribute changed
    :param respondent_details: respondent data
    :param update_required_flag: boolean flag if update is required
    """
    if form['first_name'].data != respondent_details['firstName']:
        respondent_details['firstName'] = form['first_name'].data
        update_required_flag = True
        attributes_changed.append('first name')
    if form['last_name'].data != respondent_details['lastName']:
        respondent_details['lastName'] = form['last_name'].data
        update_required_flag = True
        attributes_changed.append('last name')
    if form['phone_number'].data != respondent_details['telephone']:
        respondent_details['telephone'] = form['phone_number'].data
        update_required_flag = True
        attributes_changed.append('telephone number')
    return update_required_flag


def create_success_message(attr, message):
    """
    Takes a string as message and a list of strings attr
    to append message with attributes adding ',' and 'and'

    for example: if message = "I ate "
    and attr = ["apple","banana","grapes"]
    result will be = "I ate apple, banana and grapes."

    :param attr: list of string
    :param message: string
    :returns: A string formatted using the two supplied variables
    :rtype: str
    """
    for x in attr:
        if x == attr[-1] and len(attr) >= 2:
            message += ' and ' + x
        elif x != attr[0] and len(attr) > 2:
            message += ', ' + x
        else:
            message += x

    return message
