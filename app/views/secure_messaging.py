from flask import Blueprint, render_template, request, json
from authentication.jwt import encode
from authentication.jwe import Encrypter
import requests
import settings
import logging

logger = logging.getLogger(__name__)
token_data = {
            "user_urn": "0000"
        }

headers = {'Content-Type': 'application/json', 'Authorization': ''}


def update_encrypted_jwt():
    encrypter = Encrypter(_private_key=settings.SM_USER_AUTHENTICATION_PRIVATE_KEY,
                          _private_key_password=settings.SM_USER_AUTHENTICATION_PRIVATE_KEY_PASSWORD,
                          _public_key=settings.SM_USER_AUTHENTICATION_PUBLIC_KEY)
    signed_jwt = encode(token_data)
    return encrypter.encrypt_token(signed_jwt)

headers['Authorization'] = update_encrypted_jwt()

modify_data = {'action': '',
               'label': ''}

secure_message_bp = Blueprint('secure_message_bp', __name__, static_folder='static', template_folder='templates')


@secure_message_bp.route('/')
def hello_world():
    return "Hello World"


@secure_message_bp.route('/create-message', methods=['GET', 'POST'])
def create_message():
    if request.method == 'POST':
        logger.info("Send Message")
        headers['Authorization'] = update_encrypted_jwt()
        try:
            data = {'urn_to': 'BRES', 'urn_from': 'tom@gmail.com', 'subject': request.form['secure-message-subject'], 'body': request.form['secure-message-body'],
                    'collection_case': 'test', 'reporting_unit': 'test', 'survey': 'BRES'}
        except Exception as e:
            logger.info(e)
        response = requests.post("http://localhost:5050/message/send", data=json.dumps(data), headers=headers)
        resp_data = json.loads(response.text)
        logger.debug(resp_data['msg_id'])
    else:
        return render_template('secure-messages-create.html', _theme='default')
