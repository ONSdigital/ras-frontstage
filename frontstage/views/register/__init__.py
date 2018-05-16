from flask import Blueprint


register_bp = Blueprint('register_bp', __name__,
                        static_folder='static', template_folder='templates/register')

from frontstage.views.register import activate_account, check_email, confirm_organisation_survey  # noqa
from frontstage.views.register import create_account, enter_account_details  # noqa
