import logging

from flask import render_template, request, flash, url_for
from structlog import wrap_logger
from werkzeug.utils import redirect

from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers import party_controller
from frontstage.exceptions.exceptions import ApiError
from frontstage.models import OptionsForm, ContactDetailsChangeForm

from frontstage.views.account import account_bp

logger = wrap_logger(logging.getLogger(__name__))


@account_bp.route('/', methods=['GET'])
@jwt_authorization(request)
def get_account(session):
    form = OptionsForm()
    party_id = session.get_party_id()
    respondent_details = party_controller.get_respondent_party_by_id(party_id)
    error_panel = request.args.get('error_panel')
    return render_template('account/account.html', form=form, respondent=respondent_details, error_panel=error_panel)


@account_bp.route('/', methods=['POST'])
@jwt_authorization(request)
def update_account(session):
    form = OptionsForm()
    form_valid = form.validate()
    if not form_valid:
        error_panel = 'At least one option should be selected.'
        return redirect(url_for('account_bp.get_account', error_panel=error_panel))
    if form.data['option'] == 'contact_details':
        return redirect(url_for('account_bp.change_account_details'))


@account_bp.route('/change-account-details', methods=['GET', 'POST'])
@jwt_authorization(request)
def change_account_details(session):
    form = ContactDetailsChangeForm(request.values)
    party_id = session.get_party_id()
    respondent_details = party_controller.get_respondent_party_by_id(party_id)
    update_required_flag = False
    attributes_changed = []
    if request.method == 'POST' and form.validate():
        logger.info('Attempting to update contact details changes on the account')
        update_required_flag = check_attribute_change(attributes_changed, respondent_details, update_required_flag)
        if update_required_flag:
            try:
                party_controller.update_account(respondent_details)
            except ApiError as exc:
                logger.error('Failed to updated account', status=exc.status_code)
                raise exc
            logger.info('Successfully updated account')
            success_panel = create_success_message(attributes_changed, "We've updated your ")
            return redirect(url_for('surveys_bp.get_survey_list', tag='todo', success_panel=success_panel))
        else:
            return redirect(url_for('surveys_bp.get_survey_list', tag='todo'))
    else:
        return render_template('account/account-contact-detail-change.html',
                               form=form, errors=form.errors, respondent=respondent_details)


def check_attribute_change(attributes_changed, respondent_details, update_required_flag):
    if request.form.get('first_name') != respondent_details['firstName']:
        respondent_details['firstName'] = request.form.get('first_name')
        update_required_flag = True
        attributes_changed.append('first name')
    if request.form.get('last_name') != respondent_details['lastName']:
        respondent_details['lastName'] = request.form.get('last_name')
        update_required_flag = True
        attributes_changed.append('last name')
    if request.form.get('phone_number') != respondent_details['telephone']:
        respondent_details['telephone'] = request.form.get('phone_number')
        update_required_flag = True
        attributes_changed.append('telephone number')
    return update_required_flag


def create_success_message(attr, message):
    for x in attr:
        if x == attr[-1] and len(attr) >= 2:
            message += ' and ' + x
        elif x != attr[0] and len(attr) > 2:
            message += ', ' + x
        else:
            message += x

    return message
