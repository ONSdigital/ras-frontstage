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


@account_bp.route('/', methods=['GET', 'POST'])
@jwt_authorization(request)
def get_account(session):
    form = OptionsForm()
    form_valid = form.validate()
    party_id = session.get_party_id()
    respondent_details = party_controller.get_respondent_party_by_id(party_id)
    if request.method == 'POST':
        if not form_valid:
            flash('At least one option should be selected!')
            return redirect(url_for('account_bp.get_account'))
        if form.data['option'] == 'contact_details':
            return redirect(url_for('account_bp.change_account_details'))
    else:
        return render_template('account/account.html', form=form, respondent=respondent_details)


@account_bp.route('/change-account-details', methods=['GET', 'POST'])
@jwt_authorization(request)
def change_account_details(session):
    form = ContactDetailsChangeForm(request.values)
    party_id = session.get_party_id()
    respondent_details = party_controller.get_respondent_party_by_id(party_id)
    update_required_flag = False
    if request.method == 'POST' and form.validate():
        logger.info('Attempting to create account')
        message = "We've updated your"
        if request.form.get('first_name') != respondent_details['firstName']:
            respondent_details['firstName'] = request.form.get('first_name')
            update_required_flag = True
            message += " first name"
        if request.form.get('last_name') != respondent_details['lastName']:
            respondent_details['lastName'] = request.form.get('last_name')
            update_required_flag = True
            if message == "We've updated your":
                message += " last name"
            else:
                message += ", last name"
        if request.form.get('phone_number') != respondent_details['telephone']:
            respondent_details['telephone'] = request.form.get('phone_number')
            update_required_flag = True
            if message == "We've updated your":
                message += " phone number"
            else:
                message += ", phone number"

        if update_required_flag:
            try:
                party_controller.update_account(respondent_details)
            except ApiError as exc:
                logger.error('Failed to updated account', status=exc.status_code)
                raise exc
            logger.info('Successfully updated account')
            success_panel = message
            return redirect(url_for('surveys_bp.get_survey_list', tag='todo', success_panel=success_panel))
        else:
            return redirect(url_for('surveys_bp.get_survey_list', tag='todo'))
    else:
        return render_template('account/account.contact-detail-change.html',
                               form=form, errors=form.errors, respondent=respondent_details)
