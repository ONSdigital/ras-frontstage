import json
import logging

from flask import abort, flash, request
from flask import session as flask_session
from flask import url_for
from markupsafe import Markup
from structlog import wrap_logger
from werkzeug.utils import redirect

from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers import (
    conversation_controller,
    party_controller,
    survey_controller,
)
from frontstage.models import (
    HelpCompletingThisSurveyForm,
    HelpInfoAboutTheONSForm,
    HelpInfoAboutThisSurveyForm,
    HelpOptionsForm,
    HelpSomethingElseForm,
    SecureMessagingForm,
)
from frontstage.views.surveys import surveys_bp
from frontstage.views.template_helper import render_template

logger = wrap_logger(logging.getLogger(__name__))
help_completing_this_survey_title = "Help completing this survey"
info_about_this_survey_title = "Information about this survey"
info_about_the_ons = "Information about the ONS"
something_else_title = "Something else"
option_template_url_mapping = {
    "help-completing-this-survey": "surveys/help/surveys-help-completing-this-survey.html",
    "info-about-this-survey": "surveys/help/surveys-help-info-about-this-survey.html",
    "info-about-the-ons": "surveys/help/surveys-help-info-about-the-ons.html",
    "something-else": "surveys/help/surveys-help-something-else.html",
}
option_template_title_mapping = {
    "help-completing-this-survey": "Help completing this survey",
    "info-about-this-survey": "Help information about this survey",
    "info-about-the-ons": "Help information about the ONS",
    "something-else": "Help with something else",
}
sub_option_template_url_mapping = {
    "do-not-have-specific-figures": "surveys/help/surveys-help-specific-figure-for-response.html",
    "unable-to-return-by-deadline": "surveys/help/surveys-help-return-data-by-deadline.html",
    "exemption-completing-survey": "surveys/help/surveys-help-exemption-completing-survey.html",
    "why-selected": "surveys/help/surveys-help-why-selected.html",
    "time-to-complete": "surveys/help/surveys-help-time-to-complete.html",
    "how-long-selected-for": "surveys/help/surveys-help-how-long-selected-for.html",
    "penalties": "surveys/help/surveys-help-penalties.html",
    "info-something-else": "surveys/help/surveys-help-info-something-else.html",
    "who-is-the-ons": "surveys/help/surveys-help-who-is-the-ons.html",
    "how-safe-is-my-data": "surveys/help/surveys-help-how-safe-is-my-data.html",
    "my-survey-is-not-listed": "surveys/help/surveys-help-my-survey-is-not-listed.html",
}
sub_option_template_title_mapping = {
    "do-not-have-specific-figures": "Help with specific figures",
    "unable-to-return-by-deadline": "Help with deadline",
    "exemption-completing-survey": "Help with exemption completing survey",
    "why-selected": "Help with why business selected",
    "time-to-complete": "Help with time to complete",
    "how-long-selected-for": "Help with how long selected for",
    "penalties": "Help with penalties",
    "info-something-else": "Help survey info something else",
    "who-is-the-ons": "Help with who is the ONS",
    "how-safe-is-my-data": "Help with how safe is my data",
    "my-survey-is-not-listed": "Help my survey is not listed",
    "answer-survey-question": "Send message",
    "completing-this-survey-something-else": "Send message",
    "info-ons-something-else": "Send message",
    "something-else": "Send message",
}
subject_text_mapping = {
    "do-not-have-specific-figures": "I don’t have specific figures for a response",
    "unable-to-return-by-deadline": "What if I cannot return the survey by the deadline?",
    "exemption-completing-survey": "Can I be exempt from completing the survey questionnaire?",
    "why-selected": "How  was my business selected?",
    "time-to-complete": "How long will it take to complete?",
    "how-long-selected-for": "How long will my business be selected for?",
    "penalties": "Are there penalties for not completing this survey?",
    "info-something-else": info_about_this_survey_title,
    "who-is-the-ons": "Who is the ONS?",
    "how-safe-is-my-data": "How safe is my data?",
    "my-survey-is-not-listed": "My survey is not listed",
    "something-else": "Something else",
    "answer-survey-question": "Help answering a survey question",
    "info-about-the-ons": info_about_the_ons,
    "completing-this-survey-something-else": help_completing_this_survey_title,
    "info-ons-something-else": info_about_the_ons,
}
breadcrumb_text_mapping = {
    "do-not-have-specific-figures": [help_completing_this_survey_title, "I don’t have specific figures for a response"],
    "unable-to-return-by-deadline": [
        help_completing_this_survey_title,
        "I am unable to return the data by the deadline",
    ],
    "exemption-completing-survey": [
        info_about_this_survey_title,
        "Can I be exempt from completing the survey questionnaire?",
    ],
    "why-selected": [info_about_this_survey_title, "How  was my business selected?"],
    "time-to-complete": [info_about_this_survey_title, "How long will it take to complete?"],
    "how-long-selected-for": [info_about_this_survey_title, "How long will my business be selected for?"],
    "penalties": [info_about_this_survey_title, "What are the penalties for not completing a survey?"],
    "info-something-else": [info_about_this_survey_title, "More information"],
    "who-is-the-ons": [info_about_the_ons, "Who is the ONS?"],
    "how-safe-is-my-data": [info_about_the_ons, "How safe is my data?"],
    "my-survey-is-not-listed": [something_else_title, "My survey is not listed"],
    "help-completing-this-survey": [help_completing_this_survey_title],
    "completing-this-survey-something-else": [help_completing_this_survey_title],
    "answer-survey-question": [help_completing_this_survey_title],
    "info-ons-something-else": [info_about_the_ons],
    "something-else": [something_else_title],
}


@surveys_bp.route("/surveys-help", methods=["GET"])
@jwt_authorization(request)
def get_surveys_help_page(session):
    """Gets Survey Help page provided survey_ref and ru_ref and creates flash session for selection"""
    flask_session["help_survey_ref"] = request.args.get("survey_ref", None)
    flask_session["help_ru_ref"] = request.args.get("ru_ref", None)
    flask_session["collection_exercise_id"] = request.args.get("collection_exercise_id", None)
    flask_session["survey_id"] = request.args.get("survey_id")
    flask_session["survey_ref"] = request.args.get("survey_ref")
    flask_session["period_ref"] = request.args.get("period_ref")
    abort_help_if_session_not_set()
    return redirect(
        url_for(
            "surveys_bp.help_page",
        )
    )


@surveys_bp.route("/help", methods=["GET", "POST"])
@jwt_authorization(request)
def help_page(session):
    """Get survey help page provided survey_ref and ru_ref are in session and post help completing this survey option
    for respective survey"""
    abort_help_if_session_not_set()
    business_id, ru_ref, short_name, survey, survey_ref = get_selected_survey_business_details()
    page_title = "Help"
    if request.method == "POST":
        form = HelpOptionsForm(request.values)
        if form.validate():
            option = form.data["option"]
            if option == "help-with-my-account":
                return redirect(url_for("account_bp.account"))
            return redirect(url_for("surveys_bp.help_option_select", option=option))
        else:
            flash("You need to choose an option")
            page_title = "Error: " + page_title

    return render_template(
        "surveys/help/surveys-help.html",
        session=session,
        form=HelpOptionsForm(),
        short_name=short_name,
        survey_name=survey["longName"],
        business_id=business_id,
        survey_ref=survey_ref,
        ru_ref=ru_ref,
        page_title=page_title,
    )


@surveys_bp.route("/help/<option>", methods=["GET", "POST"])
@jwt_authorization(request)
def help_option_select(session, option: str):
    """Gets and provides additional options once sub options are selected"""
    page_title = option_template_title_mapping.get(option, "Invalid template")
    abort_help_if_session_not_set()
    business_id, ru_ref, short_name, survey, survey_ref = get_selected_survey_business_details()
    template = option_template_url_mapping.get(option, "Invalid template")

    if request.method == "POST":
        if option == "help-completing-this-survey":
            form = HelpCompletingThisSurveyForm(request.values)
            form_valid = form.validate()
            if form_valid:
                sub_option = form.data["option"]
                if sub_option == "answer-survey-question" or sub_option == "completing-this-survey-something-else":
                    return redirect_to_send_message_page(option, sub_option)
                if sub_option == "do-not-have-specific-figures" or sub_option == "unable-to-return-by-deadline":
                    return redirect_to_sub_option_select_page(option, sub_option)
            else:
                page_title = flash_error_and_set_title(page_title)
        if option == "info-about-this-survey":
            form = HelpInfoAboutThisSurveyForm(request.values)
            form_valid = form.validate()
            if form_valid:
                sub_option = form.data["option"]
                return redirect_to_sub_option_select_page(option=option, sub_option=sub_option)
            else:
                page_title = flash_error_and_set_title(page_title)
        if option == "info-about-the-ons":
            form = HelpInfoAboutTheONSForm(request.values)
            form_valid = form.validate()
            if form_valid:
                sub_option = form.data["option"]
                if sub_option == "info-ons-something-else":
                    return redirect_to_send_message_page(option, sub_option)
                return redirect_to_sub_option_select_page(option=option, sub_option=sub_option)
            else:
                page_title = flash_error_and_set_title(page_title)
        if option == "something-else":
            form = HelpSomethingElseForm(request.values)
            form_valid = form.validate()
            if form_valid:
                sub_option = form.data["option"]
                if sub_option == "something-else":
                    return redirect_to_send_message_page(option, sub_option)
                return redirect_to_sub_option_select_page(option, sub_option)
            else:
                page_title = flash_error_and_set_title(page_title)
    else:
        if template == "Invalid template":
            abort(404)

    return render_template(
        template,
        session=session,
        short_name=short_name,
        business_id=business_id,
        option=option,
        form=HelpCompletingThisSurveyForm(),
        survey_name=survey["longName"],
        survey_ref=survey_ref,
        ru_ref=ru_ref,
        page_title=page_title,
    )


@surveys_bp.route("/help/<option>/<sub_option>", methods=["GET"])
@jwt_authorization(request)
def get_help_option_sub_option_select(session, option, sub_option):
    """Provides additional options with sub option provided"""
    template = sub_option_template_url_mapping.get(sub_option, "Invalid template")
    page_title = sub_option_template_title_mapping.get(sub_option, "Invalid option")
    abort_help_if_session_not_set()
    business_id, ru_ref, short_name, survey, survey_ref = get_selected_survey_business_details()
    if template == "Invalid template":
        abort(404)
    else:
        return render_template(
            template,
            session=session,
            short_name=short_name,
            option=option,
            sub_option=sub_option,
            business_id=business_id,
            survey_name=survey["longName"],
            inside_legal_basis=is_legal_basis_mandatory(survey["legalBasisRef"]),
            survey_ref=survey_ref,
            ru_ref=ru_ref,
            is_survey_help_page=True,  # currently used by survey not listed.
            page_title=page_title,
        )


@surveys_bp.route("/help/<option>/<sub_option>/send-message", methods=["GET", "POST"])
@jwt_authorization(request)
def send_help_message(session, option, sub_option):
    """Handles requests to send a secure message for the help pages"""
    print(sub_option)
    page_title = sub_option_template_title_mapping.get(sub_option, "Invalid option")
    abort_help_if_session_not_set()
    business_id, ru_ref, short_name, survey, survey_ref = get_selected_survey_business_details()
    subject = subject_text_mapping.get(sub_option)
    breadcrumb_text = breadcrumb_text_mapping.get(sub_option, None)
    breadcrumb_title_one = breadcrumb_text[0] if len(breadcrumb_text) > 0 else None
    breadcrumb_title_two = breadcrumb_text[1] if len(breadcrumb_text) > 1 else None

    if request.method == "POST":
        form = SecureMessagingForm(request.form)
        if not form.validate():
            flash(form.errors["body"][0])
            page_title = "Error: " + page_title
            # return redirect(url_for("surveys_bp.send_help_message", option=option, sub_option=sub_option))
        else:
            party_id = session.get_party_id()
            business_id = business_id
            logger.info("Form validation successful", party_id=party_id)
            category = "SURVEY"
            if option == "info-about-the-ons":
                category = "TECHNICAL"
            sent_message = _send_new_message(subject, party_id, survey["id"], business_id, category)
            thread_url = (
                url_for("secure_message_bp.view_conversation", thread_id=sent_message["thread_id"]) + "#latest-message"
            )
            flash(Markup(f"Message sent. <a href={thread_url}>View Message</a>"))
            return redirect(url_for("surveys_bp.get_survey_list", tag="todo"))

    return render_template(
        "secure-messages/help/secure-message-send-messages-view.html",
        session=session,
        short_name=short_name,
        option=option,
        sub_option=sub_option,
        form=SecureMessagingForm(),
        subject=subject,
        breadcrumb_title_one=breadcrumb_title_one,
        breadcrumb_title_two=breadcrumb_title_two,
        business_id=business_id,
        survey_ref=survey_ref,
        ru_ref=ru_ref,
        page_title=page_title,
    )


def abort_help_if_session_not_set():
    """
    Aborts the process if flask session attributes are not set
    :raises HTTPException: Raised when help_survey_ref and help_ru_ref are both not set in the session
    """
    if flask_session.get("help_survey_ref") is None or flask_session.get("help_ru_ref") is None:
        logger.info("Both help_survey_ref and help_ru_ref is not in session, hence aborting")
        abort(404)


def get_selected_survey_business_details() -> tuple[str, str, str, str, str]:
    """
    Gets the business_id, ru_ref, short_name, survey, survey_ref using flask session
    returns business_id, ru_ref, short_name, survey, survey_ref using flask session
    """
    survey_ref = flask_session["help_survey_ref"]
    ru_ref = flask_session["help_ru_ref"]
    survey = survey_controller.get_survey_by_survey_ref(survey_ref)
    business = party_controller.get_business_by_ru_ref(ru_ref)
    short_name = survey["shortName"]
    business_id = business["id"]
    return business_id, ru_ref, short_name, survey, survey_ref


def redirect_to_sub_option_select_page(option: str, sub_option: str):
    """
    redirect to get_help_option_sub_option_select
    """
    return redirect(
        url_for(
            "surveys_bp.get_help_option_sub_option_select",
            option=option,
            sub_option=sub_option,
        )
    )


def redirect_to_send_message_page(option: str, sub_option: str):
    """
    redirect to send_help_message
    """
    return redirect(url_for("surveys_bp.send_help_message", option=option, sub_option=sub_option))


def flash_error_and_set_title(page_title: str):
    flash("You need to choose an option")
    return "Error: " + page_title


def _send_new_message(subject, party_id, survey_id, business_id, category):
    logger.info("Attempting to send message", party_id=party_id, business_id=business_id)

    form = SecureMessagingForm(request.form)
    message_json = {
        "msg_from": party_id,
        "msg_to": ["GROUP"],
        "subject": subject,
        "body": form["body"].data,
        "thread_id": form["thread_id"].data,
        "business_id": business_id,
        "survey_id": survey_id,
        "category": category,
    }

    response = conversation_controller.send_message(json.dumps(message_json))

    collection_exercise_id = (
        flask_session["collection_exercise_id"] if "collection_exercise_id" in flask_session else None
    )

    period_ref = flask_session["period_ref"] if "period_ref" in flask_session else None

    survey_ref = flask_session["survey_ref"] if "survey_ref" in flask_session else None

    logger.info(
        "Secure message sent successfully",
        message_id=response["msg_id"],
        party_id=party_id,
        business_id=business_id,
        collection_exercise_id=collection_exercise_id,
        period_ref=period_ref,
        survey_id=survey_id,
        survey_ref=survey_ref,
        category=category,
        internal_user=False,
    )

    return response


def is_legal_basis_mandatory(legal_basis):
    """
    Checks whether the provided legal basis is for a survey which is mandatory.

    :param legal_basis: The legal basis reference
    :type legal_basis: str
    :return: True if mandatory, false otherwise
    :rtype: bool
    """
    inside_legal_basis = ["STA1947", "STA1947_BEIS", "GovERD"]
    return any(item == legal_basis for item in inside_legal_basis)
