import logging

from flask import Blueprint, flash, render_template, request, url_for
from structlog import wrap_logger
from werkzeug.utils import redirect

from frontstage.models import HelpForm, HelpInfoOnsForm, HelpPasswordForm

logger = wrap_logger(logging.getLogger(__name__))

help_bp = Blueprint("help_bp", __name__, static_folder="static", template_folder="templates")

form_redirect_mapper = {
    "info-ons": "help_bp.info_ons_get",
    "password": "help_bp.help_with_password_get",
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


@help_bp.route("/", methods=["GET"])
def help_get():
    return render_template("help/help.html", form=HelpForm(), page_title="Help")


@help_bp.route("/", methods=["POST"])
def help_submit():
    form = HelpForm(request.values)
    if form.validate():
        return redirect(url_for(form_redirect_mapper.get(form.data["option"])))
    else:
        flash("At least one option should be selected.")
        return render_template("help/help.html", form=HelpForm(), page_title="Error: Help")


@help_bp.route("/info-ons", methods=["GET"])
def info_ons_get():
    return render_template("help/help-info-ons.html", form=HelpInfoOnsForm(), page_title="Help info ONS")


@help_bp.route("/info-ons", methods=["POST"])
def info_ons_submit():
    form = HelpInfoOnsForm(request.values)
    if form.validate():
        return render_template(form_render_page_mapper.get(form.data["option"]))
    else:
        flash("At least one option should be selected.")
        return render_template("help/help-info-ons.html", form=HelpInfoOnsForm(), page_title="Error: Help info ONS")


@help_bp.route("/help-with-my-password", methods=["GET"])
def help_with_password_get():
    return render_template("help/help-with-password.html", form=HelpPasswordForm(), page_title="Help with my password")


@help_bp.route("/help-with-my-password", methods=["POST"])
def help_with_password_submit():
    form = HelpPasswordForm(request.values)
    if form.validate():
        return render_template(form_render_page_mapper.get(form.data["option"]))
    else:
        flash("At least one option should be selected.")
        return render_template("help/help-with-password.html", form=HelpPasswordForm(),
                               page_title="Error: Help with my password")


@help_bp.route("/something-else", methods=["GET"])
def something_else():
    return render_template("help/help-something-else.html")
