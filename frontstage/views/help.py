import logging

from flask import Blueprint, flash, request, url_for
from structlog import wrap_logger
from werkzeug.utils import redirect

from frontstage.models import HelpForm, HelpInfoOnsForm, HelpPasswordForm
from frontstage.views.template_helper import render_template

logger = wrap_logger(logging.getLogger(__name__))

help_bp = Blueprint("help_bp", __name__, static_folder="static", template_folder="templates")

form_redirect_mapper = {
    "info-ons": "help_bp.info_ons_page",
    "password": "help_bp.help_with_password_page",
    "something-else": "help_bp.something_else",
}
form_render_page_mapper = {
    "ons": "help/help-who-is-ons.html",
    "data": "help/help-info-how-safe-data.html",
    "info-something-else": "help/help-info-something-else.html",
    "reset-email": "help/help-with-password-reset-email.html",
    "password-not-accept": "help/help-with-password-not-accept.html",
    "reset-password": "help/help-with-password-reset.html",
    "password-something-else": "help/help-with-password-something-else.html",
}


@help_bp.route("/vulnerability-reporting", methods=["GET"])
def help():
    return render_template("vunerability_disclosure.html")


@help_bp.route("/", methods=["GET", "POST"])
def help_page():
    page_title = "Help"
    form = HelpForm(request.values)
    if request.method == "POST":
        if form.validate():
            return redirect(url_for(form_redirect_mapper.get(form.data["option"])))
        else:
            flash("At least one option should be selected.")
            page_title = "Error: " + page_title

    return render_template("help/help.html", form=HelpForm(), page_title=page_title)


@help_bp.route("/info-ons", methods=["GET", "POST"])
def info_ons_page():
    page_title = "Help info ONS"
    form = HelpInfoOnsForm(request.values)
    if request.method == "POST":
        if form.validate():
            return render_template(form_render_page_mapper.get(form.data["option"]))
        else:
            flash("At least one option should be selected.")
            page_title = "Error: " + page_title

    return render_template("help/help-info-ons.html", form=HelpInfoOnsForm(), page_title=page_title)


@help_bp.route("/help-with-my-password", methods=["GET", "POST"])
def help_with_password_page():
    page_title = "Help with my password"
    form = HelpPasswordForm(request.values)
    if request.method == "POST":
        if form.validate():
            return render_template(form_render_page_mapper.get(form.data["option"]))
        else:
            flash("At least one option should be selected.")
            page_title = "Error: " + page_title

    return render_template("help/help-with-password.html", form=HelpPasswordForm(), page_title=page_title)


@help_bp.route("/something-else", methods=["GET"])
def something_else():
    return render_template("help/help-something-else.html")
