from flask import Blueprint


passwords_bp = Blueprint('passwords_bp', __name__,
                         static_folder='static', template_folder='templates/passwords')

