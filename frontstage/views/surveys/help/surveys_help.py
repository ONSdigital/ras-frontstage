import logging

from structlog import wrap_logger
from flask import render_template, request, make_response
from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers import survey_controller
from frontstage.models import HelpOptionsForm, HelpCompletingMonthlyBusinessSurveyForm
from frontstage.views.surveys import surveys_bp

logger = wrap_logger(logging.getLogger(__name__))


@surveys_bp.route('/help/<short_name>', methods=['GET'])
@jwt_authorization(request)
def get_help_page(session, short_name):
    return render_template('surveys/help/surveys-help.html', form=HelpOptionsForm(), short_name=short_name)


@surveys_bp.route('/help/<short_name>', methods=['POST'])
@jwt_authorization(request)
def help_option_select(session, short_name):
    survey = survey_controller.get_survey_by_short_name(short_name)
    form = HelpOptionsForm(request.values)
    form_valid = form.validate()
    if form.data['option'] == 'help_completing_monthly_business_survey':
        logger.info('help_completing_monthly_business_survey selected')
        return render_template('surveys/help/surveys-help-completing-monthly-business-survey.html',
                               form=HelpCompletingMonthlyBusinessSurveyForm(), short_name=short_name)
    if form.data['option'] == 'info_about_monthly_business_survey':
        logger.info('info_about_monthly_business_survey selected')
    if form.data['option'] == 'info_about_ons':
        logger.info('info_about_ons selected')
    if form.data['option'] == 'help_with_my_account':
        logger.info('help_with_my_account selected')
    if form.data['option'] == 'something_else':
        logger.info('something_else selected')



