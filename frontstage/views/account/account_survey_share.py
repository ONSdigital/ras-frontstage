import logging

from flask import render_template, request, flash, url_for
from flask import session as flask_session
from structlog import wrap_logger
from werkzeug.utils import redirect

from frontstage import app
from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers import survey_controller
from frontstage.controllers.party_controller import get_list_of_business_for_party, \
    get_surveys_listed_against_party_and_business_id, get_business_by_business_id
from frontstage.exceptions.exceptions import ShareSurveyProcessError
from frontstage.models import AccountSurveyShareBusinessSelectForm, AccountSurveyShareRecipientEmailForm, \
    ConfirmEmailChangeForm
from frontstage.views.account import account_bp

logger = wrap_logger(logging.getLogger(__name__))


@account_bp.route('/share-surveys', methods=['GET'])
@jwt_authorization(request)
def share_survey_overview(session):
    flask_session['business_selected'] = None
    flask_session['surveys_selected'] = None
    flask_session['recipient_email_address'] = None
    return render_template('surveys/surveys-share/overview.html')


@account_bp.route('/share-surveys/business-selection', methods=['GET'])
@jwt_authorization(request)
def share_survey_business_select(session):
    form = AccountSurveyShareBusinessSelectForm(request.values)
    party_id = session.get_party_id()
    businesses = get_list_of_business_for_party(party_id)
    flask_session['business_selected'] = None
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
    flask_session['business_selected'] = form.data['option']
    return redirect(url_for('account_bp.share_survey_survey_select'))


@account_bp.route('/share-surveys/survey-selection', methods=['GET'])
@jwt_authorization(request)
def share_survey_survey_select(session):
    party_id = session.get_party_id()
    surveys = get_surveys_listed_against_party_and_business_id(flask_session['business_selected'], party_id)
    flask_session['surveys_selected'] = None
    selected_business = get_business_by_business_id([flask_session['business_selected']])
    return render_template('surveys/surveys-share/survey-select.html',
                           surveys=surveys, business_name=selected_business[0]['name'])


@account_bp.route('/share-surveys/survey-selection', methods=['POST'])
@jwt_authorization(request)
def share_survey_post_survey_select(session):
    surveys_selected = request.form.getlist("checkbox-answer")
    flask_session['surveys_selected'] = surveys_selected
    if len(surveys_selected) == 0:
        flash('You need to select a survey')
        return redirect(url_for('account_bp.share_survey_survey_select'))
    for survey_selected in surveys_selected:
        # TODO validate of maximum users and reroute for validation failure
        logger.info('This step is still to be completed')

    return redirect(url_for('account_bp.share_survey_email_entry'))


@account_bp.route('/share-surveys/recipient-email-address', methods=['GET'])
@jwt_authorization(request)
def share_survey_email_entry(session):
    form = AccountSurveyShareRecipientEmailForm(request.values)
    flask_session['recipient_email_address'] = None
    return render_template('surveys/surveys-share/recipient-email-address.html',
                           form=form, errors=form.errors)


@account_bp.route('/share-surveys/recipient-email-address', methods=['POST'])
@jwt_authorization(request)
def share_survey_post_email_entry(session):
    form = AccountSurveyShareRecipientEmailForm(request.values)
    if not form.validate():
        return render_template('surveys/surveys-share/recipient-email-address.html',
                               form=form, errors=form.errors)
    flask_session['recipient_email_address'] = form.data['email_address']
    return redirect(url_for('account_bp.send_instruction_get'))


@account_bp.route('/share-surveys/send-instruction', methods=['GET'])
@jwt_authorization(request)
def send_instruction_get(session):
    email = flask_session['recipient_email_address']
    selected_surveys = []
    for survey_id in flask_session['surveys_selected']:
        selected_surveys.append(survey_controller.get_survey(app.config['SURVEY_URL'],
                                                             app.config['BASIC_AUTH'], survey_id))
    selected_business = get_business_by_business_id([flask_session['business_selected']])
    return render_template('surveys/surveys-share/send-instructions.html',
                           email=email, surveys=selected_surveys, form=ConfirmEmailChangeForm(),
                           business_name=selected_business[0]['name'])


@account_bp.route('/share-surveys/send-instruction', methods=['POST'])
@jwt_authorization(request)
def send_instruction(session):
    form = ConfirmEmailChangeForm(request.values)
    email = flask_session['recipient_email_address']
    if form['email_address'].data != email:
        raise ShareSurveyProcessError('Process failed due to session error')
    # TODO for each survey selected in session new row is written to the new survey share table
    # TODO Call given to send confirmation email to the recipient email address
    return render_template('surveys/surveys-share/almost-done.html')


@account_bp.route('/share-surveys/done', methods=['GET'])
@jwt_authorization(request)
def share_survey_done(session):
    flask_session['business_selected'] = None
    flask_session['surveys_selected'] = None
    flask_session['recipient_email_address'] = None
    return redirect(url_for('surveys_bp.get_survey_list', tag='todo'))