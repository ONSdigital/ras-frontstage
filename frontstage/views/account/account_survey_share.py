import json
import logging

from flask import render_template, request, flash, url_for
from flask import session as flask_session
from structlog import wrap_logger
from werkzeug.utils import redirect

from frontstage import app
from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers import survey_controller
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
    flask_session.pop('share_survey_business_selected', None)
    flask_session.pop('share_survey_surveys_selected', None)
    flask_session.pop('share_survey_recipient_email_address', None)
    return render_template('surveys/surveys-share/overview.html')


@account_bp.route('/share-surveys/business-selection', methods=['GET'])
@jwt_authorization(request)
def share_survey_business_select(session):
    form = AccountSurveyShareBusinessSelectForm(request.values)
    party_id = session.get_party_id()
    businesses = get_list_of_business_for_party(party_id)
    flask_session['share_survey_business_selected'] = None
    return render_template('surveys/surveys-share/business-select.html',
                           businesses=businesses,
                           form=form)


@account_bp.route('/share-surveys/business-selection', methods=['POST'])
@jwt_authorization(request)
def share_survey_post_business_select(session):
    form = AccountSurveyShareBusinessSelectForm(request.values)
    if not form.validate():
        flash('You need to choose a business')
        return redirect(url_for('account_bp.share_survey_business_select'))
    flask_session['share_survey_business_selected'] = form.data['option']
    return redirect(url_for('account_bp.share_survey_survey_select'))


@account_bp.route('/share-surveys/survey-selection', methods=['GET'])
@jwt_authorization(request)
def share_survey_survey_select(session):
    party_id = session.get_party_id()
    surveys = get_surveys_listed_against_party_and_business_id(flask_session['share_survey_business_selected'],
                                                               party_id)
    is_max_share_survey = request.args.get('max_share_survey', False)
    flask_session['share_survey_surveys_selected'] = None
    selected_business = get_business_by_id([flask_session['share_survey_business_selected']])
    return render_template('surveys/surveys-share/survey-select.html',
                           surveys=surveys, business_name=selected_business[0]['name'],
                           is_max_share_survey=is_max_share_survey)


def validate_max_shared_survey():
    """
        This is a validation for maximum user reached against a survey
    """
    business = flask_session['share_survey_business_selected']
    share_survey_surveys_selected = flask_session['share_survey_surveys_selected']
    for survey_selected in share_survey_surveys_selected:
        logger.info('Getting count of users registered against business and survey',
                    business_id=business, survey_id=survey_selected)
        user_count = get_user_count_registered_against_business_and_survey(business, survey_selected)
        if user_count > app.config['MAX_SHARED_SURVEY']:
            return False
    return True


@account_bp.route('/share-surveys/survey-selection', methods=['POST'])
@jwt_authorization(request)
def share_survey_post_survey_select(session):
    share_survey_surveys_selected = request.form.getlist("checkbox-answer")
    flask_session['share_survey_surveys_selected'] = share_survey_surveys_selected
    if len(share_survey_surveys_selected) == 0:
        flash('You need to select a survey')
        return redirect(url_for('account_bp.share_survey_survey_select'))
    if not validate_max_shared_survey():
        return redirect(url_for('account_bp.share_survey_survey_select', max_share_survey=True))

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
    selected_surveys = []
    for survey_id in flask_session['share_survey_surveys_selected']:
        selected_surveys.append(survey_controller.get_survey(app.config['SURVEY_URL'],
                                                             app.config['BASIC_AUTH'], survey_id))
    selected_business = get_business_by_id([flask_session['share_survey_business_selected']])
    return render_template('surveys/surveys-share/send-instructions.html',
                           email=email, surveys=selected_surveys, form=ConfirmEmailChangeForm(),
                           business_name=selected_business[0]['name'])


def build_payload():
    email = flask_session['share_survey_recipient_email_address']
    business_id = flask_session['share_survey_business_selected']
    share_survey_surveys_selected = flask_session['share_survey_surveys_selected']
    payload = {}
    pending_shares = []

    for survey in share_survey_surveys_selected:
        pending_share = {'business_id': business_id, 'survey_id': survey, 'email_address': email}
        pending_shares.append(pending_share)

    payload['pending_shares'] = pending_shares
    return json.dumps(payload)


@account_bp.route('/share-surveys/send-instruction', methods=['POST'])
@jwt_authorization(request)
def send_instruction(session):
    form = ConfirmEmailChangeForm(request.values)
    email = flask_session['share_survey_recipient_email_address']
    if form['email_address'].data != email:
        raise ShareSurveyProcessError('Process failed due to session error')
    json_data = build_payload()
    register_pending_shares(json_data)
    return render_template('surveys/surveys-share/almost-done.html')


@account_bp.route('/share-surveys/done', methods=['GET'])
@jwt_authorization(request)
def share_survey_done(session):
    flask_session.pop('share_survey_business_selected', None)
    flask_session.pop('share_survey_surveys_selected', None)
    flask_session.pop('share_survey_recipient_email_address', None)
    return redirect(url_for('surveys_bp.get_survey_list', tag='todo'))
