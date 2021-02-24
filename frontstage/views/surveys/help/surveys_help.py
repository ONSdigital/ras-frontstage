import json
import logging
from os import abort

from flask import render_template, request, url_for, flash
from markupsafe import Markup
from structlog import wrap_logger
from werkzeug.utils import redirect

from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers import survey_controller, conversation_controller
from frontstage.models import HelpOptionsForm, HelpCompletingThisSurveyForm, SecureMessagingForm, \
    HelpInfoAboutThisSurveyForm
from frontstage.views.surveys import surveys_bp

logger = wrap_logger(logging.getLogger(__name__))
help_completing_this_survey_title = "Help completing this survey"
template_url = {
        'do-not-have-specific-figures': 'surveys/help/surveys-help-specific-figure-for-response.html',
        'unable-to-return-by-deadline': 'surveys/help/surveys-help-return-data-by-deadline.html',
        'exemption-completing-survey': 'surveys/help/surveys-help-exemption-completing-survey.html',
        'why-selected': 'surveys/help/surveys-help-why-selected.html',
        'time-to-complete': 'surveys/help/surveys-help-time-to-complete.html',
        'how-long-selected-for': 'surveys/help/surveys-help-how-long-selected-for.html',
        'penalties': 'surveys/help/surveys-help-penalties.html',
        'info-something-else': 'surveys/help/surveys-help-info-something-else.html'
}


@surveys_bp.route('/help/<short_name>/<business_id>', methods=['GET'])
@jwt_authorization(request)
def get_help_page(session, short_name, business_id):
    """Gets Survey Help page provided survey short name and business_id"""
    survey = survey_controller.get_survey_by_short_name(short_name)
    return render_template('surveys/help/surveys-help.html',
                           form=HelpOptionsForm(),
                           short_name=short_name, survey_name=survey['longName'], business_id=business_id)


@surveys_bp.route('/help/<short_name>/<business_id>', methods=['POST'])
@jwt_authorization(request)
def post_help_page(session, short_name, business_id):
    """Post help completing this survey option for respective survey provided
    survey short name and business_id"""
    form = HelpOptionsForm(request.values)
    form_valid = form.validate()
    option = form.data['option']
    if form_valid:
        return redirect(url_for('surveys_bp.get_help_option_select', short_name=short_name, business_id=business_id,
                                option=option))
    else:
        flash('At least one option should be selected.')
        return redirect(url_for('surveys_bp.get_help_page', short_name=short_name, business_id=business_id))


@surveys_bp.route('/help/<short_name>/<business_id>/<option>', methods=['GET'])
@jwt_authorization(request)
def get_help_option_select(session, short_name, business_id, option):
    """Gets help completing this survey's additional options (sub options)"""
    survey = survey_controller.get_survey_by_short_name(short_name)
    if option == 'help-completing-this-survey':
        return render_template('surveys/help/surveys-help-completing-this-survey.html',
                               short_name=short_name, business_id=business_id, option=option,
                               form=HelpCompletingThisSurveyForm(),
                               survey_name=survey['longName'])
    if option == 'info-about-this-survey':
        return render_template('surveys/help/surveys-help-info-about-this-survey.html',
                               short_name=short_name, business_id=business_id, option=option,
                               form=HelpInfoAboutThisSurveyForm(),
                               survey_name=survey['longName'])
    else:
        abort(404)


@surveys_bp.route('/help/<short_name>/<business_id>/<option>', methods=['POST'])
@jwt_authorization(request)
def post_help_option_select(session, short_name, business_id, option):
    """Provides additional options once sub options are selected"""
    if option == 'help-completing-this-survey':
        form = HelpCompletingThisSurveyForm(request.values)
        form_valid = form.validate()
        breadcrumbs_title = help_completing_this_survey_title
        if form_valid:
            sub_option = form.data['option']
            if sub_option == 'answer-survey-question':
                return redirect(url_for('surveys_bp.get_send_help_message', short_name=short_name,
                                        option=option, business_id=business_id))
            if sub_option == 'do-not-have-specific-figures' or sub_option == 'unable-to-return-by-deadline':
                return redirect(url_for('surveys_bp.get_help_option_sub_option_select', short_name=short_name,
                                        option=option, sub_option=sub_option,
                                        business_id=business_id))
            if form.data['option'] == 'something-else' and form_valid:
                return render_template('secure-messages/help/secure-message-send-messages-view.html',
                                       short_name=short_name, option=option, form=SecureMessagingForm(),
                                       subject=help_completing_this_survey_title, text_one=breadcrumbs_title,
                                       business_id=business_id
                                       )
        else:
            flash('At least one option should be selected.')
            return redirect(url_for('surveys_bp.get_help_option_select',
                                    short_name=short_name, business_id=business_id,
                                    option=option))
    if option == 'info-about-this-survey':
        form = HelpInfoAboutThisSurveyForm(request.values)
        form_valid = form.validate()
        breadcrumbs_title = 'Information about this survey'
        if form_valid:
            sub_option = form.data['option']
            return redirect(url_for('surveys_bp.get_help_option_sub_option_select', short_name=short_name,
                                    option=option, business_id=business_id,
                                    sub_option=sub_option))
        else:
            flash('At least one option should be selected.')
            return redirect(url_for('surveys_bp.get_help_option_select',
                                    short_name=short_name, business_id=business_id,
                                    option=option))


@surveys_bp.route('/help/<short_name>/<business_id>/<option>/<sub_option>', methods=['GET'])
@jwt_authorization(request)
def get_help_option_sub_option_select(session, short_name, business_id, option, sub_option):
    """Provides additional options with sub option provided"""
    template = template_url.get(sub_option, "Invalid template")
    if template == 'Invalid template':
        abort(404)
    else:
        return render_template(template,
                               short_name=short_name, option=option, sub_option=sub_option,
                               business_id=business_id)


@surveys_bp.route('/help/<short_name>/<business_id>/<option>/send-message', methods=['GET'])
@jwt_authorization(request)
def get_send_help_message(session, short_name, business_id, option):
    """Gets the send message page once the option is selected"""
    if 'errors' in request.args:
        errors = request.args['errors']
        flash(errors)
    if option == 'help-completing-this-survey':
        breadcrumbs_title = help_completing_this_survey_title
    return render_template('secure-messages/help/secure-message-send-messages-view.html',
                           short_name=short_name, option=option, form=SecureMessagingForm(),
                           subject='Help answering a survey question', text_one=breadcrumbs_title,
                           business_id=business_id
                           )


@surveys_bp.route('/help/<short_name>/<business_id>/<option>/<sub_option>/send-message', methods=['GET'])
@jwt_authorization(request)
def get_send_help_message_page(session, short_name, business_id, option, sub_option):
    """Gets the send message page once the option and sub option is selected"""
    if 'errors' in request.args:
        errors = request.args['errors']
        flash(errors)
    subject, text_one, text_two = _get_subject_and_breadcrumbs_title(sub_option, f'surveys/help/{short_name}/{option}')
    return render_template('secure-messages/help/secure-message-send-messages-view.html',
                           short_name=short_name, option=option, sub_option=sub_option, form=SecureMessagingForm(),
                           subject=subject, text_one=text_one, text_two=text_two, business_id=business_id)


@surveys_bp.route('/help/<short_name>/<business_id>/send-message', methods=['POST'])
@jwt_authorization(request)
def send_help_message(session, short_name, business_id):
    """Sends secure message for the help pages"""
    form = SecureMessagingForm(request.form)
    option = request.args['option']
    sub_option = request.args['sub_option']
    if not form.validate():
        if sub_option == 'not_defined':
            return redirect(url_for('surveys_bp.get_send_help_message', short_name=short_name, business_id=business_id,
                                    option=option, errors=form.errors['body']))
        else:
            return redirect(url_for('surveys_bp.get_send_help_message_page', short_name=short_name,
                                    business_id=business_id, option=option, sub_option=sub_option,
                                    errors=form.errors['body']))
    else:
        subject = request.args['subject']
        party_id = session.get_party_id()
        survey = survey_controller.get_survey_by_short_name(short_name)
        business_id = business_id
        logger.info("Form validation successful", party_id=party_id)
        sent_message = _send_new_message(subject, party_id, survey['id'], business_id)
        thread_url = url_for("secure_message_bp.view_conversation",
                             thread_id=sent_message['thread_id']) + "#latest-message"
        flash(Markup(f'Message sent. <a href={thread_url}>View Message</a>'))
        return redirect(url_for('surveys_bp.get_survey_list', tag='todo'))


def _send_new_message(subject, party_id, survey, business_id):
    logger.info('Attempting to send message', party_id=party_id, business_id=business_id)
    form = SecureMessagingForm(request.form)
    message_json = {
        "msg_from": party_id,
        "msg_to": ['GROUP'],
        "subject": subject,
        "body": form['body'].data,
        "thread_id": form['thread_id'].data,
        "business_id": business_id,
        "survey": survey,
    }

    response = conversation_controller.send_message(json.dumps(message_json))

    logger.info('Secure message sent successfully',
                message_id=response['msg_id'], party_id=party_id, business_id=business_id)
    return response


def _get_subject_and_breadcrumbs_title(option, uri):
    """Gets the subject line for the secure message, the title of the breadcrumbs for sub options """
    if option == 'do-not-have-specific-figures':
        return 'I don’t have specific figures for a response', \
               help_completing_this_survey_title, \
               "I don’t have specific figures for a response"
    if option == 'unable-to-return-by-deadline':
        return 'I’m unable to return the data by the deadline', \
               help_completing_this_survey_title, \
               "I’m unable to return the data by the deadline"
    if option == 'exemption-completing-survey':
        return "Can I be exempt from completing the survey questionnaire?", \
               "Information about this survey", \
               "Can I be exempt from completing the survey questionnaire?"
    if option == 'why-selected':
        return "How / why was my business selected?", \
               "Information about this survey", \
               "How / why was my business selected?"
    if option == 'time-to-complete':
        return "How long will it take to complete?", \
               "Information about this survey", \
               "How long will it take to complete?"
    if option == 'how-long-selected-for':
        return "How long will I be selected for?", \
               "Information about this survey", \
               "How long will I be selected for?"
    if option == 'penalties':
        return "What are the penalties for not completing a survey?", \
               "Information about this survey", \
               "What are the penalties for not completing a survey?"
    if option == 'info-something-else':
        return "Information about this survey", \
               "Information about this survey", \
               "More information"


def _inside_legal_basis(short_name):
    survey = survey_controller.get_survey_by_short_name(short_name)
    inside_legal_basis = ['STA1947', 'STA1947_BEIS', 'GovERD']
    return any(item == survey['legalBasis'] for item in inside_legal_basis)
