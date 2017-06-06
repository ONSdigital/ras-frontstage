from flask import Blueprint, render_template, request, json
from app.authentication.jwt import encode
from app.authentication.jwe import Encrypter
import requests
import settings
import logging

logger = logging.getLogger(__name__)


headers = {'Content-Type': 'application/json', 'Authorization': 'eyJhbGciOiJSU0EtT0FFUCIsImVuYyI6IkEyNTZHQ00ifQ.GXOO8DQItBlk9hO2Lve2G7vjD1AoEdmzrJVn6_woPhPGddNk9dtfUgbHDuCVoQrteTC8ux1zbKnn0VSCSaSIEF8kM-8WQirDTxWtm8F5i339dJk7eM3Bk6-BxQgMcgrSUrGDwjPuQBYaHEvRGPZccB4576JXX4zhBjaqKDYzD_57St5bC1Ve7k_N-97W3w2VqT33OtQdwS6qeDqXFc6DHCgJsvLMFztmJ1BTWzab9PejmWhLup5uBb9s0XWRyx12KcNXJtNuFxFM2z4FMJ2sWPeNqLbgcg8ECfJ0IrO-Cy4JuitphnWegaujpcFnuoZl-FQvHszZF6uoGsjOQUII5w.ll-4VbmGRJL-ROgi.41hFWh6SLlp-y6ZrquxSeNkABGQp_4E6Y5gVkTogTNMbXkDJ2Dd3PRcsp_heGTzD6DEygIW_fAqR4ekfpuLYb4oj5Iax5fUYJfhp1b-FyKIqOExuQoaDCWaisDrIglfLQQYtSsXF49mvRVapIzD9YtSW4FyEJVwYsS6YVykezkk._xidxqOPvdqGocscjyi2wQ'}


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
        try:
            data = {'urn_to': 'BRES', 'urn_from': 'tom@gmail.com', 'subject': request.form['secure-message-subject'], 'body': request.form['secure-message-body'],
                    'collection_case': 'test', 'reporting_unit': 'test', 'survey': 'BRES'}
        except Exception as e:
            logger.info(e)
        response = requests.post("http://localhost:5050/message/send", data=json.dumps(data), headers=headers)
        resp_data = json.loads(response.text)
        logger.debug(resp_data['msg_id'])
        return render_template('message-success-temp.html', _theme='default')
    else:
        return render_template('secure-messages-create.html', _theme='default')
