import logging

from flask import render_template, request
from structlog import wrap_logger

from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers import party_controller

from frontstage.views.account import account_bp

logger = wrap_logger(logging.getLogger(__name__))


@account_bp.route('/', methods=['GET'])
@jwt_authorization(request)
def get_account(session):
    party_id = session.get_party_id()
    respondent_details = party_controller.get_respondent_party_by_id(party_id)
    return render_template('account/account.html', respondent=respondent_details)

