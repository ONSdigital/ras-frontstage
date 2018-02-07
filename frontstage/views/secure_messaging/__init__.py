from flask import Blueprint


secure_message_bp = Blueprint('secure_message_bp', __name__, static_folder='static', template_folder='templates')
