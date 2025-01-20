import logging
from uuid import UUID

from flask import abort
from flask import current_app as app
from flask import flash, request, url_for
from markupsafe import Markup
from structlog import wrap_logger
from werkzeug.utils import redirect
from werkzeug.wrappers.response import Response

from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers.conversation_controller import (
    InvalidSecureMessagingForm,
    send_message,
)
from frontstage.controllers.survey_controller import get_survey
from frontstage.models import (
    HelpCompletingThisSurveyForm,
    HelpInfoAboutTheONSForm,
    HelpInfoAboutThisSurveyForm,
    HelpOptionsForm,
    HelpSomethingElseForm,
)
from frontstage.views.surveys import surveys_bp
from frontstage.views.template_helper import render_template

logger = wrap_logger(logging.getLogger(__name__))

help_completing_this_survey_title = "Help completing this survey"
info_about_this_survey_title = "Information about this survey"
info_about_the_ons = "Information about the ONS"
something_else_title = "Something else"

OPTION_MAPPER = {
    "help-completing-this-survey": {
        "form": HelpCompletingThisSurveyForm,
        "template": "surveys-help-completing-this-survey.html",
        "sub_options": [
            "answer-survey-question",
            "completing-this-survey-something-else",
            "do-not-have-specific-figures",
            "unable-to-return-by-deadline",
        ],
        "title": "Help completing this survey",
    },
    "info-about-this-survey": {
        "form": HelpInfoAboutThisSurveyForm,
        "template": "surveys-help-info-about-this-survey.html",
        "title": "Help information about this survey",
    },
    "info-about-the-ons": {
        "form": HelpInfoAboutTheONSForm,
        "template": "surveys-help-info-about-the-ons.html",
        "title": "Help information about the ONS1",
    },
    "something-else": {
        "form": HelpSomethingElseForm,
        "template": "surveys-help-something-else.html",
        "title": "Help with something else",
    },
}


def _send_help_message_url(
    survey_name: str, business_id: UUID, survey_id: UUID, ce_id: UUID, option: str, sub_option: str
) -> str:
    return url_for(
        "surveys_bp.send_help_message",
        survey_name=survey_name,
        business_id=business_id,
        survey_id=survey_id,
        ce_id=ce_id,
        option=option,
        sub_option=sub_option,
    )


SUB_OPTION_MAPPER = {
    "do-not-have-specific-figures": {
        "template": "surveys-help-specific-figure-for-response.html",
        "title": "Help with specific figures",
        "subject": "I don’t have specific figures for a response",
        "breadcrumbs": [help_completing_this_survey_title, "I don’t have specific figures for a response"],
    },
    "unable-to-return-by-deadline": {
        "template": "surveys-help-return-data-by-deadline.html",
        "title": "Help with deadline",
        "subject": "What if I cannot return the survey by the deadline?",
        "breadcrumbs": [help_completing_this_survey_title, "I am unable to return the data by the deadline"],
    },
    "exemption-completing-survey": {
        "template": "surveys-help-exemption-completing-survey.html",
        "title": "Help with exemption completing survey",
        "subject": "Can I be exempt from completing the survey questionnaire?",
        "breadcrumbs": [info_about_this_survey_title, "Can I be exempt from completing the survey questionnaire?"],
    },
    "why-selected": {
        "template": "surveys-help-why-selected.html",
        "title": "Help with why business selected",
        "subject": "How  was my business selected?",
        "breadcrumbs": [info_about_this_survey_title, "How  was my business selected?"],
    },
    "time-to-complete": {
        "template": "surveys-help-time-to-complete.html",
        "title": "Help with time to complete",
        "subject": "How long will it take to complete?",
        "breadcrumbs": [info_about_this_survey_title, "How long will it take to complete?"],
    },
    "how-long-selected-for": {
        "template": "surveys-help-how-long-selected-for.html",
        "title": "Help with how long selected for",
        "subject": "How long will my business be selected for?",
        "breadcrumbs": [info_about_this_survey_title, "How long will my business be selected for?"],
    },
    "penalties": {
        "template": "surveys-help-penalties.html",
        "title": "Help with penalties",
        "subject": "Are there penalties for not completing this survey?",
        "breadcrumbs": [info_about_this_survey_title, "What are the penalties for not completing a survey?"],
    },
    "info-something-else": {
        "template": "surveys-help-info-something-else.html",
        "title": "Help survey info something else",
        "subject": info_about_this_survey_title,
        "breadcrumbs": [info_about_this_survey_title, "More information"],
    },
    "who-is-the-ons": {
        "template": "surveys-help-who-is-the-ons.html",
        "title": "Help with who is the ONS",
        "subject": "Who is the ONS?",
        "breadcrumbs": [info_about_the_ons, "Who is the ONS?"],
    },
    "how-safe-is-my-data": {
        "template": "surveys-help-how-safe-is-my-data.html",
        "title": "Help with how safe is my data",
        "subject": "How safe is my data?",
        "breadcrumbs": [info_about_the_ons, "How safe is my data?"],
    },
    "my-survey-is-not-listed": {
        "template": "surveys-help-my-survey-is-not-listed.html",
        "title": "Help my survey is not listed",
        "subject": "My survey is not listed",
        "breadcrumbs": [something_else_title, "My survey is not listed"],
    },
    "answer-survey-question": {
        "title": "Send message",
        "subject": "Help answering a survey question",
        "breadcrumbs": [help_completing_this_survey_title],
        "url": _send_help_message_url,
    },
    "completing-this-survey-something-else": {
        "title": "Send message",
        "subject": help_completing_this_survey_title,
        "breadcrumbs": [help_completing_this_survey_title],
        "url": _send_help_message_url,
    },
    "info-ons-something-else": {
        "title": "Send message",
        "subject": "Information about the ONS",
        "breadcrumbs": [info_about_the_ons],
        "url": _send_help_message_url,
    },
    "something-else": {
        "title": "Send message",
        "subject": info_about_the_ons,
        "breadcrumbs": [something_else_title],
        "url": _send_help_message_url,
    },
}


@surveys_bp.route("/help", methods=["GET", "POST"])
@jwt_authorization(request)
def surveys_help_page(_) -> (Response, str):
    business_id, survey_id, survey_name, ce_id = _help_details()
    page_title = "Help"

    if request.method == "POST":
        form = HelpOptionsForm(request.values)
        if form.validate():
            option = form.data["option"]
            if option == "help-with-my-account":
                return redirect(url_for("account_bp.account"))
            return redirect(
                url_for(
                    "surveys_bp.help_option_select",
                    survey_name=survey_name,
                    business_id=business_id,
                    survey_id=survey_id,
                    ce_id=ce_id,
                    option=option,
                )
            )
        else:
            page_title = _flash_error_and_set_title(page_title)

    return render_template(
        template="surveys/help/surveys-help.html",
        page_title=page_title,
        survey_name=survey_name,
        survey_id=survey_id,
        business_id=business_id,
        ce_id=ce_id,
    )


@surveys_bp.route("/help/<option>", methods=["GET", "POST"])
@jwt_authorization(request)
def help_option_select(_, option: str) -> (Response, str):
    if not (option_dict := OPTION_MAPPER.get(option)):
        abort(404)

    business_id, survey_id, survey_name, ce_id = _help_details()
    page_title = option_dict["title"]
    if request.method == "POST":
        form = option_dict["form"](request.values)
        if form.validate():
            sub_option = form.data["option"]
            sub_option_dict = SUB_OPTION_MAPPER.get(sub_option)
            option_url = sub_option_dict.get("url", _sub_option_select_page_url)
            return redirect(option_url(survey_name, business_id, survey_id, ce_id, option, sub_option))
        else:
            page_title = _flash_error_and_set_title(page_title)

    return render_template(
        template=f"surveys/help/{option_dict['template']}",
        page_title=page_title,
        survey_name=survey_name,
        business_id=business_id,
        survey_id=survey_id,
        ce_id=ce_id,
        option=option,
        breadcrumbs=_create_breadcrumbs(),
    )


@surveys_bp.route("/help/<option>/<sub_option>", methods=["GET"])
@jwt_authorization(request)
def get_help_option_sub_option_select(_, option, sub_option) -> str:
    if not (sub_option_dict := SUB_OPTION_MAPPER.get(sub_option)):
        abort(404)
    business_id, survey_id, survey_name, ce_id = _help_details()

    return render_template(
        template=f"surveys/help/{sub_option_dict['template']}",
        page_title=sub_option_dict["title"],
        survey_name=survey_name,
        business_id=business_id,
        survey_id=survey_id,
        ce_id=ce_id,
        option=option,
        sub_option=sub_option,
        send_help_message_url=_send_help_message_url(survey_name, business_id, survey_id, ce_id, option, sub_option),
        inside_legal_basis=(
            _is_legal_basis_mandatory(survey_id)
            if sub_option in ("penalties", "unable-to-return-by-deadline", "exemption-completing-survey")
            else None
        ),
        breadcrumbs=_create_breadcrumbs(option),
    )


@surveys_bp.route("/help/<option>/<sub_option>/send-message", methods=["GET", "POST"])
@jwt_authorization(request)
def send_help_message(session, option: str, sub_option: str):
    if not (sub_option_dict := SUB_OPTION_MAPPER.get(sub_option)):
        abort(404)

    business_id, survey_id, survey_name, ce_id = _help_details()
    page_title = sub_option_dict["title"]
    if request.method == "POST":
        party_id = session.get_party_id()
        category = "TECHNICAL" if option == "info-about-the-ons" else "SURVEY"
        subject = sub_option_dict["subject"]
        try:
            msg_id = send_message(
                request.form, party_id, subject, category, survey_id=survey_id, business_id=business_id, ce_id=ce_id
            )

            thread_url = url_for("secure_message_bp.view_conversation", thread_id=msg_id)
            flash(Markup(f"Message sent. <a href={thread_url}>View Message</a>"))
            return redirect(url_for("surveys_bp.get_survey_list", tag="todo"))

        except InvalidSecureMessagingForm as e:
            page_title = _flash_error_and_set_title(page_title)
            flash(e.errors["body"][0])

    breadcrumb_text = sub_option_dict["breadcrumbs"]
    breadcrumb_title_one = breadcrumb_text[0] if len(breadcrumb_text) > 0 else None
    breadcrumb_title_two = breadcrumb_text[1] if len(breadcrumb_text) > 1 else None

    return render_template(
        "secure-messages/help/secure-message-send-messages-view.html",
        page_title=page_title,
        subject=sub_option_dict["subject"],
        breadcrumb_title_one=breadcrumb_title_one,
        breadcrumb_title_two=breadcrumb_title_two,
        survey_name=survey_name,
        business_id=business_id,
        survey_id=survey_id,
        ce_id=ce_id,
        option=option,
        sub_option=sub_option,
        breadcrumbs=_create_breadcrumbs(option, sub_option),
    )


def _sub_option_select_page_url(
    survey_name: str, business_id: UUID, survey_id: UUID, ce_id: UUID, option: str, sub_option: str
) -> str:
    return url_for(
        "surveys_bp.get_help_option_sub_option_select",
        survey_name=survey_name,
        business_id=business_id,
        survey_id=survey_id,
        ce_id=ce_id,
        option=option,
        sub_option=sub_option,
    )


def _flash_error_and_set_title(page_title: str) -> str:
    flash("You need to choose an option")
    return "Error: " + page_title


def _is_legal_basis_mandatory(survey_id: UUID) -> bool:
    """
    Checks whether the provided legal basis is for a survey which is mandatory.
    :param survey_id: The survey_id to check
    :return: True if mandatory, false otherwise
    :rtype: bool
    """
    survey = get_survey(app.config["SURVEY_URL"], app.config["BASIC_AUTH"], survey_id)
    inside_legal_basis = ["STA1947", "STA1947_BEIS", "GovERD"]
    return any(item == survey["legalBasisRef"] for item in inside_legal_basis)


def _help_details() -> (UUID, str, UUID, UUID):
    business_id = request.args.get("business_id")
    survey_name = request.args.get("survey_name")
    survey_id = request.args.get("survey_id")
    ce_id = request.args.get("ce_id")
    return business_id, survey_id, survey_name, ce_id


def _create_breadcrumbs(option=None, sub_option=None):
    query_string = request.query_string.decode("utf-8")
    breadcrumbs = {"help": f"/surveys/help?{query_string}"}

    if option:
        breadcrumbs["option"] = f"/surveys/help/{option}?{query_string}"
    if sub_option:
        breadcrumbs["sub_option"] = f"/surveys/help/{option}/{sub_option}?{query_string}"

    return breadcrumbs
