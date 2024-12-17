import logging

from flask import flash, request, url_for
from structlog import wrap_logger
from werkzeug.utils import redirect

from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers import party_controller
from frontstage.controllers.auth_controller import delete_account
from frontstage.views.account import account_bp
from frontstage.views.template_helper import render_template

logger = wrap_logger(logging.getLogger(__name__))


@account_bp.route("/delete", methods=["GET", "POST"])
@jwt_authorization(request)
def delete_user_account(session):
    party_id = session.get_party_id()
    enrolments = party_controller.get_respondent_enrolments(party_id)
    if enrolments:
        flash("This operation is not allowed as you are currently assigned to a survey.", "info")
        return render_template("account/account-delete.html", is_validated=False)
    if request.method == "POST":
        respondent = party_controller.get_respondent_party_by_id(party_id)
        delete_account(respondent["emailAddress"])
        return redirect(url_for("sign_in_bp.logout"))

    return render_template("account/account-delete.html", session=session, is_validated=True)
