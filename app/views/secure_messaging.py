from flask import Blueprint

secure_message_bp = Blueprint('secure_message_bp', __name__, static_folder='static', template_folder='templates')


@secure_message_bp.route('/')
def hello_world():
    return "Hello World"
