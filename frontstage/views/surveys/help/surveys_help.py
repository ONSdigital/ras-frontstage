import json
import logging

from structlog import wrap_logger
from flask import render_template, request, make_response, url_for
from werkzeug.utils import redirect

from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers import survey_controller, conversation_controller
from frontstage.models import HelpOptionsForm, HelpCompletingMonthlyBusinessSurveyForm, SecureMessagingForm
from frontstage.views.surveys import surveys_bp

logger = wrap_logger(logging.getLogger(__name__))


@surveys_bp.route('/help/<short_name>', methods=['GET'])
@jwt_authorization(request)
def get_help_page(session, short_name):
    return render_template('surveys/help/surveys-help.html', form=HelpOptionsForm(), short_name=short_name)


@surveys_bp.route('/help/<short_name>', methods=['POST'])
@jwt_authorization(request)
def post_help_page(session, short_name):
    form = HelpOptionsForm(request.values)
    form_valid = form.validate()
    if form.data['option'] == 'help_completing_monthly_business_survey':
        logger.info('help_completing_monthly_business_survey selected')
        return redirect(url_for('surveys_bp.get_help_option_select', short_name=short_name,
                                option='completingThisSurvey'))
    if form.data['option'] == 'info_about_monthly_business_survey':
        logger.info('info_about_monthly_business_survey selected')
    if form.data['option'] == 'info_about_ons':
        logger.info('info_about_ons selected')
    if form.data['option'] == 'help_with_my_account':
        logger.info('help_with_my_account selected')
    if form.data['option'] == 'something_else':
        logger.info('something_else selected')


@surveys_bp.route('/help/<short_name>/<option>', methods=['GET'])
@jwt_authorization(request)
def get_help_option_select(session, short_name, option):
    if option == 'completingThisSurvey':
        logger.info('help_completing_monthly_business_survey selected')
        return render_template('surveys/help/surveys-help-completing-monthly-business-survey.html',
                               short_name=short_name, option=option, form=HelpCompletingMonthlyBusinessSurveyForm())


@surveys_bp.route('/help/<short_name>/<option>', methods=['POST'])
@jwt_authorization(request)
def post_help_option_select(session, short_name, option):
    if option == 'completingThisSurvey':
        form = HelpCompletingMonthlyBusinessSurveyForm(request.values)
        form_valid = form.validate()
        breadcrumbs_title = 'Help completing this survey'
        if form.data['option'] == 'answer_survey_question':
            return render_template('secure-messages/help/secure-message-send-messages-view.html',
                                   short_name=short_name, option=option, form=SecureMessagingForm(),
                                   subject='Help answering a survey question', breadcrumbs_title=breadcrumbs_title)
        if form.data['option'] == 'do_not_have_specific_figures':
            return render_template('surveys/help/surveys-help-completing-monthly-business-survey.html',
                                   short_name=short_name, option=option, form=HelpCompletingMonthlyBusinessSurveyForm())
        if form.data['option'] == 'unable_to_return_by_deadline':
            return render_template('surveys/help/surveys-help-completing-monthly-business-survey.html',
                                   short_name=short_name, option=option, form=HelpCompletingMonthlyBusinessSurveyForm())
        if form.data['option'] == 'something_else':
            return render_template('surveys/help/surveys-help-completing-monthly-business-survey.html',
                                   short_name=short_name, option=option, form=HelpCompletingMonthlyBusinessSurveyForm())