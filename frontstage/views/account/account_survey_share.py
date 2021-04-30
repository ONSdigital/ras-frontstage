import json
import logging

from flask import render_template, request, flash, url_for
from flask import session as flask_session
from structlog import wrap_logger
from werkzeug.utils import redirect

from frontstage import app
from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers import survey_controller, party_controller
from frontstage.controllers.party_controller import get_list_of_business_for_party, \
    get_surveys_listed_against_party_and_business_id, get_business_by_id, \
    get_user_count_registered_against_business_and_survey, register_pending_shares
from frontstage.exceptions.exceptions import ShareSurveyProcessError
from frontstage.models import AccountSurveyShareBusinessSelectForm, AccountSurveyShareRecipientEmailForm, \
    ConfirmEmailChangeForm
from frontstage.views.account import account_bp

logger = wrap_logger(logging.getLogger(__name__))


@account_bp.route('/share-surveys', methods=['GET'])
@jwt_authorization(request)
def share_survey_overview(session):
    flask_session.pop('share', None)
    flask_session.pop('share_survey_recipient_email_address', None)
    return render_template('surveys/surveys-share/overview.html')


@account_bp.route('/share-surveys/business-selection', methods=['GET'])
@jwt_authorization(request)
def share_survey_business_select(session):
    form = AccountSurveyShareBusinessSelectForm(request.values)
    party_id = session.get_party_id()
    businesses = get_list_of_business_for_party(party_id)
    return render_template('surveys/surveys-share/business-select.html',
                           businesses=businesses,
                           form=form)


@account_bp.route('/share-surveys/business-selection', methods=['POST'])
@jwt_authorization(request)
def share_survey_post_business_select(session):
    share_survey_business_selected = request.form.getlist("checkbox-answer")
    if len(share_survey_business_selected) == 0:
        flash('You need to choose a business')
        return redirect(url_for('account_bp.share_survey_business_select'))
    flask_session['share'] = {k: [] for k in share_survey_business_selected}
    return redirect(url_for('account_bp.share_survey_survey_select'))


@account_bp.route('/share-surveys/survey-selection', methods=['GET'])
@jwt_authorization(request)
def share_survey_survey_select(session):
    party_id = session.get_party_id()
    share_dict = {}
    for key in flask_session['share']:
        selected_business = get_business_by_id(key)
        surveys = get_surveys_listed_against_party_and_business_id(key,
                                                                   party_id)
        share_dict[selected_business[0]['name']] = surveys
    is_max_share_survey = request.args.get('max_share_survey', False)
    failed_survey_key = request.args.get('key', None)
    return render_template('surveys/surveys-share/survey-select.html',
                           share_dict=share_dict, is_max_share_survey=is_max_share_survey,
                           failed_survey_key=failed_survey_key)


def validate_max_shared_survey(key: str, share_survey_surveys_selected: list):
    """
        This is a validation for maximum user reached against a survey
        param: key : business id str
        param: share_survey_surveys_selected : selected business list
        return:boolean
    """
    for survey_selected in share_survey_surveys_selected:
        logger.info('Getting count of users registered against business and survey',
                    business_id=key, survey_id=survey_selected)
        user_count = get_user_count_registered_against_business_and_survey(key, survey_selected)
        if user_count > app.config['MAX_SHARED_SURVEY']:
            return False
    return True


@account_bp.route('/share-surveys/survey-selection', methods=['POST'])
@jwt_authorization(request)
def share_survey_post_survey_select(session):
    share_dictionary_copy = flask_session['share']
    for key in share_dictionary_copy:
        selected_business = get_business_by_id(key)
        share_surveys_selected_against_business = request.form.getlist(selected_business[0]['name'])
        if len(share_surveys_selected_against_business) == 0:
            flash('Select at least one answer', selected_business[0]['name'])
            return redirect(url_for('account_bp.share_survey_survey_select'))
        if not validate_max_shared_survey(key, share_surveys_selected_against_business):
            return redirect(url_for('account_bp.share_survey_survey_select', max_share_survey=True,
                                    key=selected_business[0]['name']))
        share_dictionary_copy[key] = share_surveys_selected_against_business
    flask_session.pop('share', None)
    flask_session['share'] = share_dictionary_copy
    return redirect(url_for('account_bp.share_survey_email_entry'))


@account_bp.route('/share-surveys/recipient-email-address', methods=['GET'])
@jwt_authorization(request)
def share_survey_email_entry(session):
    form = AccountSurveyShareRecipientEmailForm(request.values)
    flask_session['share_survey_recipient_email_address'] = None
    return render_template('surveys/surveys-share/recipient-email-address.html',
                           form=form, errors=form.errors)


@account_bp.route('/share-surveys/recipient-email-address', methods=['POST'])
@jwt_authorization(request)
def share_survey_post_email_entry(session):
    form = AccountSurveyShareRecipientEmailForm(request.values)
    if not form.validate():
        return render_template('surveys/surveys-share/recipient-email-address.html',
                               form=form, errors=form.errors)
    flask_session['share_survey_recipient_email_address'] = form.data['email_address']
    return redirect(url_for('account_bp.send_instruction_get'))


@account_bp.route('/share-surveys/send-instruction', methods=['GET'])
@jwt_authorization(request)
def send_instruction_get(session):
    email = flask_session['share_survey_recipient_email_address']
    share_dict = {}
    for key in flask_session['share']:
        selected_business = get_business_by_id(key)
        surveys = []
        for survey_id in flask_session['share'][key]:
            surveys.append(survey_controller.get_survey(app.config['SURVEY_URL'],
                                                        app.config['BASIC_AUTH'], survey_id))
        share_dict[selected_business[0]['name']] = surveys
    return render_template('surveys/surveys-share/send-instructions.html',
                           email=email, share_dict=share_dict, form=ConfirmEmailChangeForm())


def build_payload(respondent_id):
    """
        This method builds payload required for the party endpoint to register new pending shares.
        TODO: The logic should change for multiple business once the story is in play.
        payload example:
        {  pending_shares: [{
            "business_id": "business_id"
            "survey_id": "survey_id",
            "email_address": "email_address",
            "shared_by": "party_uuid"
        },
        {
            "business_id": "business_id":
            "survey_id": "survey_id",
            "email_address": "email_address",
            "shared_by": "party_uuid"
        }]
        }
    """
    email = flask_session['share_survey_recipient_email_address']
    payload = {}
    pending_shares = []
    share_dictionary = flask_session['share']
    for key in share_dictionary:
        for survey in share_dictionary[key]:
            pending_share = {'business_id': key,
                             'survey_id': survey,
                             'email_address': email,
                             'shared_by': respondent_id}
            pending_shares.append(pending_share)
    payload['pending_shares'] = pending_shares
    return json.dumps(payload)


@account_bp.route('/share-surveys/send-instruction', methods=['POST'])
@jwt_authorization(request)
def send_instruction(session):
    form = ConfirmEmailChangeForm(request.values)
    email = flask_session['share_survey_recipient_email_address']
    party_id = session.get_party_id()
    respondent_details = party_controller.get_respondent_party_by_id(party_id)
    if form['email_address'].data != email:
        raise ShareSurveyProcessError('Process failed due to session error')
    json_data = build_payload(respondent_details['id'])
    register_pending_shares(json_data)
    return render_template('surveys/surveys-share/almost-done.html')


@account_bp.route('/share-surveys/done', methods=['GET'])
@jwt_authorization(request)
def share_survey_done(session):
    flask_session.pop('share', None)
    flask_session.pop('share_survey_recipient_email_address', None)
    return redirect(url_for('surveys_bp.get_survey_list', tag='todo'))
