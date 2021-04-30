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
info_about_this_survey_title = "Information about this survey"
option_template_url_mapping = {
        'help-completing-this-survey': 'surveys/help/surveys-help-completing-this-survey.html',
        'info-about-this-survey': 'surveys/help/surveys-help-info-about-this-survey.html'
}
sub_option_template_url_mapping = {
        'do-not-have-specific-figures': 'surveys/help/surveys-help-specific-figure-for-response.html',
        'unable-to-return-by-deadline': 'surveys/help/surveys-help-return-data-by-deadline.html',
        'exemption-completing-survey': 'surveys/help/surveys-help-exemption-completing-survey.html',
        'why-selected': 'surveys/help/surveys-help-why-selected.html',
        'time-to-complete': 'surveys/help/surveys-help-time-to-complete.html',
        'how-long-selected-for': 'surveys/help/surveys-help-how-long-selected-for.html',
        'penalties': 'surveys/help/surveys-help-penalties.html',
        'info-something-else': 'surveys/help/surveys-help-info-something-else.html'
}
subject_text_mapping = {
        'do-not-have-specific-figures': 'I don’t have specific figures for a response',
        'unable-to-return-by-deadline': 'I’m unable to return the data by the deadline',
        'exemption-completing-survey': 'Can I be exempt from completing the survey questionnaire?',
        'why-selected': 'How  was my business selected?',
        'time-to-complete': 'How long will it take to complete?',
        'how-long-selected-for': 'How long will my business be selected for?',
        'penalties': 'What are the penalties for not completing a survey?',
        'info-something-else': info_about_this_survey_title
}
breadcrumb_text_mapping = {
        'do-not-have-specific-figures': [help_completing_this_survey_title,
                                         'I don’t have specific figures for a response'],
        'unable-to-return-by-deadline': [help_completing_this_survey_title,
                                         'I’m unable to return the data by the deadline'],
        'exemption-completing-survey': [info_about_this_survey_title,
                                        'Can I be exempt from completing the survey questionnaire?'],
        'why-selected': [info_about_this_survey_title,
                         'How  was my business selected?'],
        'time-to-complete': [info_about_this_survey_title,
                             'How long will it take to complete?'],
        'how-long-selected-for': [info_about_this_survey_title,
                                  'How long will my business be selected for?'],
        'penalties': [info_about_this_survey_title,
                      'What are the penalties for not completing a survey?'],
        'info-something-else': [info_about_this_survey_title, 'More information']
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
    if form.validate():
        option = form.data['option']
        if option == "help-with-my-account":
            return redirect(url_for('account_bp.get_account'))
        return redirect(url_for('surveys_bp.get_help_option_select', short_name=short_name, business_id=business_id,
                                option=option))
    else:
        flash('You need to choose an option')
        return redirect(url_for('surveys_bp.get_help_page', short_name=short_name, business_id=business_id))


@surveys_bp.route('/help/<short_name>/<business_id>/<option>', methods=['GET'])
@jwt_authorization(request)
def get_help_option_select(session, short_name, business_id, option):
    """Gets help completing this survey's additional options (sub options)"""
    template = option_template_url_mapping.get(option, "Invalid template")
    if template == 'Invalid template':
        abort(404)
    else:
        survey = survey_controller.get_survey_by_short_name(short_name)
        return render_template(template,
                               short_name=short_name, business_id=business_id, option=option,
                               form=HelpCompletingThisSurveyForm(),
                               survey_name=survey['longName'])


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
            if form.data['option'] == 'something-else':
                return render_template('secure-messages/help/secure-message-send-messages-view.html',
                                       short_name=short_name, option=option, form=SecureMessagingForm(),
                                       subject=help_completing_this_survey_title, text_one=breadcrumbs_title,
                                       business_id=business_id
                                       )
        else:
            flash('You need to choose an option')
            return redirect(url_for('surveys_bp.get_help_option_select',
                                    short_name=short_name, business_id=business_id,
                                    option=option))
    if option == 'info-about-this-survey':
        form = HelpInfoAboutThisSurveyForm(request.values)
        form_valid = form.validate()
        if form_valid:
            sub_option = form.data['option']
            return redirect(url_for('surveys_bp.get_help_option_sub_option_select', short_name=short_name,
                                    option=option, business_id=business_id,
                                    sub_option=sub_option))
        else:
            flash('You need to choose an option')
            return redirect(url_for('surveys_bp.get_help_option_select',
                                    short_name=short_name, business_id=business_id,
                                    option=option))
    else:
        abort(404)


@surveys_bp.route('/help/<short_name>/<business_id>/<option>/<sub_option>', methods=['GET'])
@jwt_authorization(request)
def get_help_option_sub_option_select(session, short_name, business_id, option, sub_option):
    """Provides additional options with sub option provided"""
    template = sub_option_template_url_mapping.get(sub_option, "Invalid template")
    survey = survey_controller.get_survey_by_short_name(short_name)
    if template == 'Invalid template':
        abort(404)
    else:
        return render_template(template,
                               short_name=short_name, option=option, sub_option=sub_option,
                               business_id=business_id, survey_name=survey['longName'],
                               inside_legal_basis=is_legal_basis_mandatory(survey['legalBasisRef']))


@surveys_bp.route('/help/<short_name>/<business_id>/<option>/send-message', methods=['GET'])
@jwt_authorization(request)
def get_send_help_message(session, short_name, business_id, option):
    """Gets the send message page once the option is selected"""

    if option == 'help-completing-this-survey':
        breadcrumbs_title = help_completing_this_survey_title
    return render_template('secure-messages/help/secure-message-send-messages-view.html',
                           short_name=short_name, option=option, form=SecureMessagingForm(),
                           subject='Help answering a survey question', breadcrumb_title_one=breadcrumbs_title,
                           business_id=business_id
                           )


@surveys_bp.route('/help/<short_name>/<business_id>/<option>/<sub_option>/send-message', methods=['GET'])
@jwt_authorization(request)
def get_send_help_message_page(session, short_name, business_id, option, sub_option):
    """Gets the send message page once the option and sub option is selected"""
    subject = subject_text_mapping.get(sub_option)
    text = breadcrumb_text_mapping.get(sub_option)
    return render_template('secure-messages/help/secure-message-send-messages-view.html',
                           short_name=short_name, option=option, sub_option=sub_option, form=SecureMessagingForm(),
                           subject=subject, breadcrumb_title_one=text[0], breadcrumb_title_two=text[1],
                           business_id=business_id)


@surveys_bp.route('/help/<short_name>/<business_id>/send-message', methods=['POST'])
@jwt_authorization(request)
def send_help_message(session, short_name, business_id):
    """Sends secure message for the help pages"""
    form = SecureMessagingForm(request.form)
    option = request.args['option']
    sub_option = request.args['sub_option']
    if not form.validate():
        flash(form.errors['body'][0])
        if sub_option == 'not_defined':
            return redirect(url_for('surveys_bp.get_send_help_message', short_name=short_name, business_id=business_id,
                                    option=option))
        else:
            return redirect(url_for('surveys_bp.get_send_help_message_page', short_name=short_name,
                                    business_id=business_id, option=option, sub_option=sub_option))
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


def is_legal_basis_mandatory(legal_basis):
    """
        Checks whether the provided legal basis is for a survey which is mandatory.

        :param legal_basis: The legal basis reference
        :type legal_basis: str
        :return: True if mandatory, false otherwise
        :rtype: bool
    """
    inside_legal_basis = ['STA1947', 'STA1947_BEIS', 'GovERD']
    return any(item == legal_basis for item in inside_legal_basis)
