import logging
import os

from flask import Blueprint, json, redirect, render_template, request, session, url_for
from frontstage.common.authorisation import jwt_authorization
import requests
from structlog import wrap_logger

from frontstage import app
from frontstage.exceptions.exceptions import ExternalServiceError


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


def get_party_ru_id(party_id):
    url = app.config['RAS_PARTY_GET_BY_RESPONDENT'].format(app.config['RAS_PARTY_SERVICE'], party_id)
    party_response = requests.get(url)
    if party_response.status_code == 404:
        logger.error("No respondent with party_id: {}".format(party_id))
        return None
    elif party_response.status_code != 200:
        raise ExternalServiceError(party_response)
    party_response_json = party_response.json()
    associations = party_response_json.get('associations')
    if associations:
        ru_id = associations[0].get('partyId')
    else:
        ru_id = None
    return ru_id


def get_collection_case(party_id):
    url = app.config['RM_CASE_GET_BY_PARTY'].format(app.config['RM_CASE_SERVICE'], party_id)
    collection_response = requests.get(url)
    if collection_response.status_code == 204:
        logger.error('"event" : "No case found for party id", "ID" : "{}"'.format(party_id))
        return None
    elif collection_response.status_code != 200:
        raise ExternalServiceError(collection_response)
    collection_response_json = collection_response.json()
    return collection_response_json[0].get('id')


def get_survey_id(party_id):
    url = app.config['RAS_PARTY_GET_BY_RESPONDENT'].format(app.config['RAS_PARTY_SERVICE'], party_id)
    survey_response = requests.get(url)
    if survey_response is None:
        logger.error('"event" : "No case found for party id", "ID" : "{}"'.format(party_id))
        return None
    elif survey_response.status_code != 200:
        raise ExternalServiceError(survey_response)
    survey_response_json = survey_response.json()
    associations = survey_response_json.get('associations')
    if associations:
        survey_name = associations[0].get('enrolments')[0].get('surveyId')
    else:
        survey_name = None

    return survey_name


@secure_message_bp.route('/create-message', methods=['GET', 'POST'])
@jwt_authorization(request)
def create_message(session):
    """Handles sending of new message"""
    if request.method == 'POST':
        party_id = session['party_id']
        collection_case = get_collection_case(party_id)
        if collection_case is None:
            return redirect(url_for('error_bp.default_error_page'))
        ru_id = get_party_ru_id(party_id)
        if ru_id is None:
            return redirect(url_for('error_bp.default_error_page'))
        survey_name = get_survey_id(party_id)
        if survey_name is None:
            return redirect(url_for('error_bp.default_error_page'))
        data = {'msg_to': ['BRES'],
                'msg_from': session['party_id'],
                'subject': request.form['secure-message-subject'],
                'body': request.form['secure-message-body'],
                'thread_id': '',
                'collection_case': collection_case,
                'ru_id': ru_id,
                'survey': survey_name}

        # Message already saved as draft
        if "msg_id" in request.form:
            data["msg_id"] = request.form['msg_id']

        if request.form['submit'] == 'Send':
            return message_check_response(data)

        if request.form['submit'] == 'Save draft':
            if "msg_id" in request.form and len(request.form['msg_id']) != 0:
                data['msg_id'] = request.form['msg_id']
                headers['Authorization'] = request.cookies['authorization']
                response = requests.put(DRAFT_PUT_API_URL.format(request.form['msg_id']), data=json.dumps(data), headers=headers)
                if response.status_code == 400:
                    get_json = json.loads(response.content)
                    return render_template('secure-messages/secure-messages-draft.html', _theme='default', draft=data, errors=get_json)
                elif response.status_code != 200:
                    raise ExternalServiceError(response)
            else:
                response = requests.post(DRAFT_SAVE_API_URL, data=json.dumps(data), headers=headers)
                if response.status_code == 400:
                    get_json = json.loads(response.content)
                    return render_template('secure-messages/secure-messages-draft.html', _theme='default', draft=data, errors=get_json)
                elif response.status_code != 201:
                    raise ExternalServiceError(response)

            response_data = json.loads(response.text)
            logger.debug('"event" : "save draft response", "Data" : ' + response_data['msg_id'])
            get_draft = requests.get(DRAFT_GET_API_URL.format(response_data['msg_id']), headers=headers)

            if get_draft.status_code != 200:
                raise ExternalServiceError(get_draft)
            get_json = json.loads(get_draft.content)
            return render_template('secure-messages/secure-messages-draft.html', _theme='default', draft=get_json, errors={})

    return render_template('secure-messages/secure-messages-create.html', _theme='default', draft={})


@secure_message_bp.route('/reply-message', methods=['GET', 'POST'])
@jwt_authorization(request)
def reply_message(session):
    """Handles replying to an existing message"""

    if request.method == 'POST':
        party_id = session['party_id']
        collection_case = get_collection_case(party_id)
        if collection_case is None:
            return redirect(url_for('error_bp.default_error_page'))
        ru_id = get_party_ru_id(party_id)
        if ru_id is None:
            return redirect(url_for('error_bp.default_error_page'))
        survey_name = get_survey_id(party_id)
        if survey_name is None:
            return redirect(url_for('error_bp.default_error_page'))

        if request.form['submit'] == 'Send':
            logger.info('"event" : "Reply to Message"')
            data = {'msg_to': ['BRES'],
                    'msg_from': session['party_id'],
                    'subject': request.form['secure-message-subject'],
                    'body': request.form['secure-message-body'],
                    'thread_id': '',
                    'collection_case': collection_case,
                    'ru_id': ru_id,
                    'survey': survey_name}

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
                    'ru_id': ru_id,
                    'survey': 'BRES'}

            if "msg_id" in request.form:
                data['msg_id'] = request.form['msg_id']
                response = requests.put(DRAFT_PUT_API_URL.format(request.form['msg_id']), data=json.dumps(data), headers=headers)
                if response.status_code == 400:
                    get_json = json.loads(response.content)
                    return render_template('secure-messages/secure-messages-draft.html',
                                           _theme='default',
                                           draft=data,
                                           errors=get_json)
                elif response.status_code != 200:
                    raise ExternalServiceError(response)
            else:
                response = requests.post(DRAFT_SAVE_API_URL, data=json.dumps(data), headers=headers)
                if response.status_code == 400:
                    get_json = json.loads(response.content)
                    return render_template('secure-messages/secure-messages-draft.html',
                                           _theme='default',
                                           draft=data,
                                           errors=get_json)
                elif response.status_code != 201:
                    raise ExternalServiceError(response)

            response_data = json.loads(response.text)
            logger.debug('"event" : "save draft response", "Data" : ' + response_data['msg_id'])
            get_draft = requests.get(DRAFT_GET_API_URL.format(response_data['msg_id']), headers=headers)

            if get_draft.status_code != 200:
                raise ExternalServiceError(get_draft)
            get_json = json.loads(get_draft.content)

            return render_template('secure-messages/secure-messages-draft.html', _theme='default', draft=get_json)

    return render_template('secure-messages/secure-messages-create.html', _theme='default', draft={})


def message_check_response(data):
    headers['Authorization'] = request.cookies['authorization']
    response = requests.post(CREATE_MESSAGE_API_URL, data=json.dumps(data), headers=headers)
    if response.status_code == 400:
        get_json = json.loads(response.content)
        return render_template('secure-messages/secure-messages-create.html', _theme='default', draft=data, errors=get_json)
    elif response.status_code != 201:
        raise ExternalServiceError(response)
    response_data = json.loads(response.text)
    logger.debug('"event" : "check response data", "Data" : ' + response_data.get('msg_id', 'No response data.'))
    return render_template('secure-messages/message-success-temp.html', _theme='default')


@secure_message_bp.route('/messages/', methods=['GET'])
@secure_message_bp.route('/messages/<label>', methods=['GET'])
@jwt_authorization(request)
def messages_get(session, label="INBOX"):
    """Gets users messages"""

    headers['Authorization'] = request.cookies['authorization']
    headers['Content-Type'] = 'application/json'
    url = MESSAGES_API_URL

    if label is not None:
        url = url + "&label=" + label

    resp = requests.get(url, headers=headers)

    if resp.status_code != 200:
        raise ExternalServiceError(resp)

    response_data = json.loads(resp.text)
    total_msgs = 0

    for x in range(0, len(response_data['messages'])):
        if "UNREAD" in response_data['messages'][x]["labels"]:
            total_msgs += 1

    return render_template('secure-messages/secure-messages.html', _theme='default', messages=response_data['messages'],
                           links=response_data['_links'], label=label, total=total_msgs)


@secure_message_bp.route('/draft/<draft_id>', methods=['GET'])
@jwt_authorization(request)
def draft_get(session, draft_id):
    """Get draft message"""
    url = DRAFT_GET_API_URL.format(draft_id)

    get_draft = requests.get(url, headers=headers)

    if get_draft.status_code != 200:
        raise ExternalServiceError(get_draft)

    draft = json.loads(get_draft.text)

    return render_template('secure-messages/secure-messages-draft.html', _theme='default', draft=draft)


@secure_message_bp.route('/sent/<sent_id>', methods=['GET'])
@jwt_authorization(request)
def sent_get(session, sent_id):
    """Get sent message"""
    url = MESSAGE_GET_URL.format(sent_id)
    get_sent = requests.get(url, headers=headers)

    if get_sent.status_code != 200:
        raise ExternalServiceError(get_sent)

    sent = json.loads(get_sent.text)

    return render_template('secure-messages/secure-messages-sent-view.html', _theme='default', message=sent)


@secure_message_bp.route('/message/<msg_id>', methods=['GET'])
@jwt_authorization(request)
def message_get(session, msg_id):
    """Get message"""

    if request.method == 'GET':
        data = {"label": 'UNREAD', "action": 'remove'}
        response = requests.put(MESSAGE_MODIFY_URL.format(msg_id), data=json.dumps(data), headers=headers)  # noqa: F841
        if response.status_code != 200:
            raise ExternalServiceError(response)

        url = MESSAGE_GET_URL.format(msg_id)
        get_message = requests.get(url, headers=headers)
        if get_message.status_code != 200:
            raise ExternalServiceError(get_message)
        message = json.loads(get_message.text)

        return render_template('secure-messages/secure-messages-view.html', _theme='default', message=message)
