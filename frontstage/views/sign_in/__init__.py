from flask import Blueprint


sign_in_bp = Blueprint('sign_in_bp', __name__, static_folder='static', template_folder='frontstage/templates/sign-in')

from frontstage.views.sign_in import logout, sign_in  # NOQA
