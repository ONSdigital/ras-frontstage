from flask import Blueprint, render_template, request, json
import requests
import logging
from structlog import wrap_logger

logger = wrap_logger(logging.getLogger(__name__))


headers = {'Content-Type': 'application/json',
           'Authorization': 'eyJhbGciOiJSU0EtT0FFUCIsImVuYyI6IkEyNTZHQ00ifQ.GXOO8DQItBlk9hO2Lve2G7vjD1AoEdmzrJVn6_woPhPGddNk9dtfUgbHDuCVoQrteTC8ux1zbKnn0VSCSaSIEF8kM-8WQirDTxWtm8F5i339dJk7eM3Bk6-BxQgMcgrSUrGDwjPuQBYaHEvRGPZccB4576JXX4zhBjaqKDYzD_57St5bC1Ve7k_N-97W3w2VqT33OtQdwS6qeDqXFc6DHCgJsvLMFztmJ1BTWzab9PejmWhLup5uBb9s0XWRyx12KcNXJtNuFxFM2z4FMJ2sWPeNqLbgcg8ECfJ0IrO-Cy4JuitphnWegaujpcFnuoZl-FQvHszZF6uoGsjOQUII5w.ll-4VbmGRJL-ROgi.41hFWh6SLlp-y6ZrquxSeNkABGQp_4E6Y5gVkTogTNMbXkDJ2Dd3PRcsp_heGTzD6DEygIW_fAqR4ekfpuLYb4oj5Iax5fUYJfhp1b-FyKIqOExuQoaDCWaisDrIglfLQQYtSsXF49mvRVapIzD9YtSW4FyEJVwYsS6YVykezkk._xidxqOPvdqGocscjyi2wQ'}


modify_data = {'action': '',
               'label': ''}

secure_message_bp = Blueprint('secure_message_bp', __name__, static_folder='static', template_folder='templates')


@secure_message_bp.route('/')
def hello_world():
    logger.debug("test")
    return "Hello World"


@secure_message_bp.route('/create-message', methods=['GET', 'POST'])
def create_message():
    """Handles sending of new message"""

    if request.method == 'POST':
        logger.info("Info - Send Message")
        logger.debug("Debug - Send Message")
        logger.warning("Warning - Send Message")
        logger.error("Error - Send Message")
        logger.critical("Critical - Send Message")
        data = {'urn_to': 'BRES', 'urn_from': 'respondent.000000000', 'subject': request.form['secure-message-subject'], 'body': request.form['secure-message-body'],
                'collection_case': 'test', 'reporting_unit': 'test', 'survey': 'BRES'}

        response = requests.post("http://localhost:5050/message/send", data=json.dumps(data), headers=headers)
        resp_data = json.loads(response.text)
        logger.debug(resp_data['msg_id'])
        return render_template("message-success-temp.html", _theme='default')
    else:
        return render_template('secure-messages-create.html', _theme='default')


@secure_message_bp.route('/reply-message', methods=['GET', 'POST'])
def reply_message():
    """Handles replying to an existing message"""

    if request.method == 'POST':
        logger.info("Reply to Message")
        data = {'urn_to': 'BRES', 'urn_from': 'tom@gmail.com', 'subject': 'reply_subject', 'body': request.form['secure-message-body'],
                'thread_id': 'test', 'collection_case': 'test', 'reporting_unit': 'test', 'survey': 'BRES'}
        response = requests.post("http://localhost:5050/message/send", data=json.dumps(data), headers=headers)
        resp_data = json.loads(response.text)
        logger.debug(resp_data['msg_id'])
        return render_template('message-success-temp.html', _theme='default')
    else:
        return render_template('secure-messages-view.html', _theme='default')


@secure_message_bp.route('/messages/<label>', methods=['GET'])
@secure_message_bp.route('/messages', methods=['GET'])
def messages_get(label='INBOX'):
    """Gets users messages"""
    url = "http://localhost:5050/messages?limit=1000"
    if label is not None:
        url = url + "&label=" + label
    resp = requests.get(url, headers=headers)
    resp_data = json.loads(resp.text)
    return render_template('secure-messages.html', _theme='default', messages=resp_data['messages'], links=resp_data['_links'], label=label)

