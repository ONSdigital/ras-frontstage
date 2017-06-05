from flask import Blueprint, render_template

secure_message_bp = Blueprint('secure_message_bp', __name__, static_folder='static', template_folder='templates')


@secure_message_bp.route('/')
def hello_world():
    return "Hello World"


@secure_message_bp.route('/create-message')
def create_message():
    return render_template('secure-messages-create.html', _theme='default')
