import json
import logging

from flask import flash, redirect, request
from flask import session as flask_session
from flask import url_for
from markupsafe import Markup
from structlog import wrap_logger

from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers import conversation_controller
from frontstage.models import SecureMessagingForm
from frontstage.views.secure_messaging import secure_message_bp
from frontstage.views.template_helper import render_template

logger = wrap_logger(logging.getLogger(__name__))


@secure_message_bp.route("/create-message/", methods=["GET", "POST"])
@jwt_authorization(request)
def create_message(session):
    """Creates and sends a message outside of the context of an existing conversation"""
    survey_id = request.args["survey"]
    ru_ref = request.args["ru_ref"]
    party_id = session.get_party_id()
    form = SecureMessagingForm(request.form)
    if request.method == "POST" and form.validate():
        logger.info("Form validation successful", party_id=party_id)
        sent_message = _send_new_message(party_id, survey_id, ru_ref)
        thread_url = (
            url_for("secure_message_bp.view_conversation", thread_id=sent_message["thread_id"]) + "#latest-message"
        )
        flash(Markup(f"Message sent. <a href={thread_url}>View Message</a>"))
        return redirect(url_for("secure_message_bp.view_conversation_list"))

    else:
        unread_message_count = {"unread_message_count": conversation_controller.try_message_count_from_session(session)}
        return render_template(
            "secure-messages/secure-messages-view.html",
            session=session,
            ru_ref=ru_ref,
            survey_id=survey_id,
            form=form,
            errors=form.errors,
            message={},
            unread_message_count=unread_message_count,
        )


def _send_new_message(party_id, survey_id, business_id):
    logger.info("Attempting to send message", party_id=party_id, business_id=business_id)
    form = SecureMessagingForm(request.form)

    subject = form["subject"].data if "subject" in form else None

    message_json = {
        "msg_from": party_id,
        "msg_to": ["GROUP"],
        "subject": subject,
        "body": form["body"].data,
        "thread_id": form["thread_id"].data,
        "business_id": business_id,
        "survey_id": survey_id,
    }

    response = conversation_controller.send_message(json.dumps(message_json))

    collection_exercise_id = (
        flask_session["collection_exercise_id"] if "collection_exercise_id" in flask_session else None
    )

    category = form["category"].data if "category" in form else None

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
