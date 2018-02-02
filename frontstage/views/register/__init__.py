from flask import Blueprint


register_bp = Blueprint('register_bp', __name__,
                        static_folder='static', template_folder='templates/register')
