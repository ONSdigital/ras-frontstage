import logging

from flask import Blueprint, flash, request
from structlog import wrap_logger

from frontstage.common.authorisation import is_authorization
from frontstage.models import HelpInfoOnsForm
from frontstage.views.template_helper import render_template

logger = wrap_logger(logging.getLogger(__name__))

help_bp = Blueprint("help_bp", __name__, static_folder="static", template_folder="templates")

form_render_page_mapper = {
    "ons": "help/help-who-is-ons.html",
    "data": "help/help-info-how-safe-data.html",
    "info-something-else": "help/help-info-something-else.html",
}


@help_bp.route("/", methods=["GET", "POST"])
def info_ons_page():
    page_title = "Help info ONS"
    form = HelpInfoOnsForm(request.values)
    if request.method == "POST":
        if form.validate():
            return render_template(form_render_page_mapper.get(form.data["option"]), authorization=is_authorization())
        else:
            flash("At least one option should be selected.")
            page_title = "Error: " + page_title

    return render_template("help/help-info-ons.html", form=HelpInfoOnsForm(), page_title=page_title)
