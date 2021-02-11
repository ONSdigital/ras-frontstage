import logging

from flask import render_template, request, flash, url_for
from structlog import wrap_logger
from werkzeug.utils import redirect

from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers import party_controller
from frontstage.exceptions.exceptions import ApiError
from frontstage.models import OptionsForm, ContactDetailsChangeForm, ConfirmEmailChangeForm

from frontstage.views.account import account_bp

logger = wrap_logger(logging.getLogger(__name__))


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
        flash('At least one option should be selected!')
        return redirect(url_for('account_bp.get_account'))
    if form.data['option'] == 'contact_details':
        return redirect(url_for('account_bp.change_account_details'))


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
    if request.method == 'POST' and form.validate():
        logger.info('Attempting to update contact details changes on the account', party_id=party_id)
        is_contact_details_update_required = check_attribute_change(form,
                                                                    attributes_changed,
                                                                    respondent_details,
                                                                    is_contact_details_update_required)
        is_email_update_required = form['email_address'].data != respondent_details['emailAddress']
        if is_contact_details_update_required:
            try:
                party_controller.update_account(respondent_details)
            except ApiError as exc:
                logger.error('Failed to updated account', status=exc.status_code)
                raise exc
            logger.info('Successfully updated account', party_id=party_id)
            success_panel = create_success_message(attributes_changed, "We have updated your ")
            flash(success_panel)

        if is_email_update_required:
            return render_template('account/account-change-email-address.html',
                                   new_email=form['email_address'].data,
                                   form=ConfirmEmailChangeForm())
        return redirect(url_for('surveys_bp.get_survey_list', tag='todo'))
    else:
        return render_template('account/account-contact-detail-change.html',
                               form=form, errors=form.errors, respondent=respondent_details)


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
