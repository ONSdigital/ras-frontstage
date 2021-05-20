from flask import Blueprint


account_bp = Blueprint('account_bp', __name__, static_folder='static', template_folder='templates/account')

from frontstage.views.account import account, account_email_change, account_survey_share # NOQA
