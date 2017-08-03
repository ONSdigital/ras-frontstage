import logging
import os

from flask import Blueprint, json, redirect, render_template, request, session, url_for
from ons_ras_common.ons_decorators import jwt_session
import requests
from structlog import wrap_logger
from frontstage import app

logger = wrap_logger(logging.getLogger(__name__))

headers = {}

modify_data = {'action': '',
               'label': ''}

secure_message_bp = Blueprint('secure_message_bp', __name__, static_folder='static', template_folder='templates')

# Constants
MESSAGE_LIMIT = 1000

SM_API_URL = os.environ.get('SM_URL', 'http://localhost:5050')
SM_UI_URL = os.environ.get('SM_UI_URL', 'http://localhost:5001/secure-message')
CREATE_MESSAGE_API_URL = SM_API_URL + '/message/send'
CREATE_MESSAGE_UI_URL = SM_UI_URL + '/create-message'
MESSAGE_DRAFT_URL = SM_UI_URL + '/DRAFT'
MESSAGES_API_URL = SM_API_URL + '/messages?limit=' + str(MESSAGE_LIMIT)
MESSAGE_GET_URL = SM_API_URL + '/message/{0}'
MESSAGE_MODIFY_URL = SM_API_URL + '/message/{0}/modify'
MESSAGES_UI_URL = SM_UI_URL + '/messages'
DRAFT_SAVE_API_URL = SM_API_URL + '/draft/save'
DRAFT_GET_API_URL = SM_API_URL + '/draft/{0}'
DRAFT_ID_API_URL = SM_API_URL + '/draft/<draft_id>'
DRAFT_PUT_API_URL = SM_API_URL + '/draft/{0}/modify'

# Selenium Driver Path
chrome_driver = "{}/tests/selenium_scripts/drivers/chromedriver".format(os.environ.get('RAS_FRONTSTAGE_PATH'))


@secure_message_bp.route('/create-message', methods=['GET', 'POST'])
@jwt_session(request)
def create_message(session):
    """Handles sending of new message"""

    url = app.config['RM_CASE_GET_BY_PARTY'].format(app.config['RM_CASE_SERVICE'], session['party_id'])
    collection_response = requests.get(url)
    if collection_response.status_code != 200:
        return redirect(url_for('error_bp.error_page'))
    collection_response_json = collection_response.json()
    collection_id = collection_response_json[0].get('id')
    if collection_id:
        collection_case = collection_id
    else:
        collection_case = None

    # url = app.config['RM_SURVEY_GET'].format(app.config['RM_SURVEY_SERVICE'], 'cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87')
    # # to get cb0711..... need associations -> enrolments -> surveyID
    # survey_response = requests.get(url)
    # if survey_response.status_code != 200:
    #     return redirect(url_for('error_bp.error_page'))
    # survey_response_json = survey_response.json()
    # survey_id = survey_response_json.get('shortName')
    # if survey_id:
    #     survey_name = survey_id
    # else:
    #     survey_name = None

    if request.method == 'POST':
        data = {'msg_to': ['BRES'],
                'msg_from': session['party_id'],
                'subject': request.form['secure-message-subject'],
                'body': request.form['secure-message-body'],
                'collection_case': collection_case,
                'ru_id': 'f1a5e99c-8edf-489a-9c72-6cabe6c387fc',
                'survey': 'BRES'}

        if request.form['submit'] == 'Send':
            return message_check_response(data)

        if request.form['submit'] == 'Save draft':
            if "msg_id" in request.form:
                data['msg_id'] = request.form['msg_id']
                response = requests.put(DRAFT_PUT_API_URL.format(request.form['msg_id']), data=json.dumps(data), headers=headers)
                if response.status_code != 200:
                    # TODO replace with custom error page when available
                    return redirect(url_for('error_bp.error_page'))
            else:
                response = requests.post(DRAFT_SAVE_API_URL, data=json.dumps(data), headers=headers)
                if response.status_code != 201:
                    # TODO replace with custom error page when available
                    return redirect(url_for('error_bp.error_page'))

            response_data = json.loads(response.text)
            logger.debug(response_data['msg_id'])
            get_draft = requests.get(DRAFT_GET_API_URL.format(response_data['msg_id']), headers=headers)

            if get_draft.status_code != 200:
                # TODO replace with custom error page when available
                return redirect(url_for('error_bp.error_page'))
            get_json = json.loads(get_draft.content)

            return render_template('secure-messages-draft.html', _theme='default', draft=get_json)

    return render_template('secure-messages-create.html', _theme='default')


@secure_message_bp.route('/reply-message', methods=['GET', 'POST'])
@jwt_session(request)
def reply_message(session):
    """Handles replying to an existing message"""

    if request.method == 'POST':
        if request.form['submit'] == 'Send':
            logger.info("Reply to Message")
            data = {'msg_to': ['BRES'],
                    'msg_from': session['party_id'],
                    'subject': request.form['secure-message-subject'],
                    'body': request.form['secure-message-body'],
                    'thread_id': '',
                    'collection_case': 'test',
                    'ru_id': 'f1a5e99c-8edf-489a-9c72-6cabe6c387fc',
                    'survey': 'BRES'}

            # Message already saved as draft
            if "msg_id" in request.form:
                data["msg_id"] = request.form['msg_id']

            return message_check_response(data)

        if request.form['submit'] == 'Save draft':
            data = {'msg_to': ['BRES'],
                    'msg_from': session['party_id'],
                    'subject': request.form['secure-message-subject'],
                    'body': request.form['secure-message-body'],
                    'collection_case': 'test',
                    'ru_id': 'f1a5e99c-8edf-489a-9c72-6cabe6c387fc',
                    'survey': 'BRES'}

            if "msg_id" in request.form:
                data['msg_id'] = request.form['msg_id']
                response = requests.put(DRAFT_PUT_API_URL.format(request.form['msg_id']), data=json.dumps(data), headers=headers)
                if response.status_code != 200:
                    # TODO replace with custom error page when available
                    return redirect(url_for('error_bp.error_page'))
            else:
                response = requests.post(DRAFT_SAVE_API_URL, data=json.dumps(data), headers=headers)
                if response.status_code != 201:
                    # TODO replace with custom error page when available
                    return redirect(url_for('error_bp.error_page'))

            response_data = json.loads(response.text)
            logger.debug(response_data['msg_id'])
            get_draft = requests.get(DRAFT_GET_API_URL.format(response_data['msg_id']), headers=headers)

            if get_draft.status_code != 200:
                # TODO replace with custom error page when available
                return redirect(url_for('error_bp.error_page'))
            get_json = json.loads(get_draft.content)

            return render_template('secure-messages-draft.html', _theme='default', draft=get_json)

    return render_template('secure-messages-create.html', _theme='default')


def message_check_response(data):
    headers['Authorization'] = request.cookies['authorization']
    response = requests.post(CREATE_MESSAGE_API_URL, data=json.dumps(data), headers=headers)
    if response.status_code != 201:
        # TODO replace with custom error page when available
        return redirect(url_for('error_bp.error_page'))
    response_data = json.loads(response.text)
    logger.debug(response_data.get('msg_id', 'No response data.'))
    return render_template('message-success-temp.html', _theme='default')


@secure_message_bp.route('/messages/', methods=['GET'])
@secure_message_bp.route('/messages/<label>', methods=['GET'])
@jwt_session(request)
def messages_get(session, label="INBOX"):
    """Gets users messages"""

    headers['Authorization'] = request.cookies['authorization']
    headers['Content-Type'] = 'application/json'
    url = MESSAGES_API_URL

    if label is not None:
        url = url + "&label=" + label

    resp = requests.get(url, headers=headers)

    if resp.status_code != 200:
        # TODO replace with custom error page when available
        return redirect(url_for('error_bp.error_page'))

    response_data = json.loads(resp.text)
    total_msgs = 0

    for x in range(0, len(response_data['messages'])):
        if "UNREAD" in response_data['messages'][x]["labels"]:
            total_msgs += 1

    return render_template('secure-messages.html', _theme='default', messages=response_data['messages'],
                           links=response_data['_links'], label=label, total=total_msgs)


@secure_message_bp.route('/draft/<draft_id>', methods=['GET'])
@jwt_session(request)
def draft_get(session, draft_id):
    """Get draft message"""
    url = DRAFT_GET_API_URL.format(draft_id)

    get_draft = requests.get(url, headers=headers)

    if get_draft.status_code != 200:
        # TODO replace with custom error page when available
        return redirect(url_for('error_bp.error_page'))

    draft = json.loads(get_draft.text)

    return render_template('secure-messages-draft.html', _theme='default', draft=draft)


@secure_message_bp.route('/message/<msg_id>', methods=['GET'])
@jwt_session(request)
def message_get(session, msg_id):
    """Get message"""

    if request.method == 'GET':
        data = {"label": 'UNREAD', "action": 'remove'}
        response = requests.put(MESSAGE_MODIFY_URL.format(msg_id), data=json.dumps(data), headers=headers)  # noqa: F841
        # TODO check this response
        url = MESSAGE_GET_URL.format(msg_id)

        get_message = requests.get(url, headers=headers)
        if get_message.status_code != 200:
            # TODO replace with custom error page when available
            return redirect(url_for('error_bp.error_page'))
        message = json.loads(get_message.text)

        return render_template('secure-messages-view.html', _theme='default', message=message)
