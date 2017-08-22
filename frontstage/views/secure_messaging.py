import logging
import os

from flask import Blueprint, json, redirect, render_template, request, session, url_for
from frontstage.common.authorisation import jwt_authorization
import requests
from structlog import wrap_logger

from frontstage import app
from frontstage.exceptions.exceptions import ExternalServiceError


logger = wrap_logger(logging.getLogger(__name__))

headers = {"Content-Type": "application/json"}

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
    logger.debug('Retrieving ru_id', party_id=party_id)
    party_response = requests.get(url)
    if party_response.status_code == 404:
        logger.error('No respondent found in party service', party_id=party_id)
        return None
    elif party_response.status_code != 200:
        logger.error('Failed to retrieve ru_id')
        raise ExternalServiceError(party_response)
    party_response_json = party_response.json()
    associations = party_response_json.get('associations')
    if associations:
        ru_id = associations[0].get('partyId')
    else:
        logger.error('Respondent has no associations', party_id=party_id)
        ru_id = None
    return ru_id


def get_collection_case(party_id):
    url = app.config['RM_CASE_GET_BY_PARTY'].format(app.config['RM_CASE_SERVICE'], party_id)
    logger.debug('Retrieving collection case id', party_id=party_id)
    collection_response = requests.get(url)
    if collection_response.status_code == 204:
        logger.error('No case found', party_id=party_id)
        return None
    elif collection_response.status_code != 200:
        logger.error('Failed to retrieve collection case id', party_id=party_id)
        raise ExternalServiceError(collection_response)
    collection_response_json = collection_response.json()
    return collection_response_json[0].get('id')


def get_survey_id(party_id):
    url = app.config['RAS_PARTY_GET_BY_RESPONDENT'].format(app.config['RAS_PARTY_SERVICE'], party_id)
    logger.debug('Retrieving survey id', party_id=party_id)
    survey_response = requests.get(url)
    if survey_response is None:
        logger.error('No respondent found in party service', party_id=party_id)
        return None
    elif survey_response.status_code != 200:
        logger.error('Failed to retrieve survey id', party_id=party_id)
        raise ExternalServiceError(survey_response)
    survey_response_json = survey_response.json()
    associations = survey_response_json.get('associations')
    if associations:
        survey_name = associations[0].get('enrolments')[0].get('surveyId')
    else:
        logger.error('Respondent has no associations', party_id=party_id)
        survey_name = None
    return survey_name


@secure_message_bp.route('/create-message', methods=['GET', 'POST'])
@jwt_authorization(request)
def create_message(session):
    """Handles sending of new message"""
    if request.method == 'POST':
        party_id = session['party_id']
        loggerb = logger.bind(party_id=party_id)

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
            loggerb = loggerb.bind(message_id=data["msg_id"])
            loggerb.debug('Message already exists as draft')

        if request.form['submit'] == 'Send':
            return message_check_response(data, loggerb)

        if request.form['submit'] == 'Save draft':
            if "msg_id" in request.form and len(request.form['msg_id']) != 0:
                headers['Authorization'] = request.cookies['authorization']

                loggerb.info('Attempting to modify draft')
                response = requests.put(DRAFT_PUT_API_URL.format(request.form['msg_id']),
                                        data=json.dumps(data),
                                        headers=headers)
                if response.status_code == 400:
                    loggerb.warning("Bad request to secure message service")
                    get_json = json.loads(response.content)
                    return render_template('secure-messages/secure-messages-draft.html',
                                           _theme='default',
                                           draft=data,
                                           errors=get_json)
                elif response.status_code != 200:
                    loggerb.error('Failed to modify draft')
                    raise ExternalServiceError(response)
            else:
                loggerb.info("Attempting to save draft")
                response = requests.post(DRAFT_SAVE_API_URL, data=json.dumps(data), headers=headers)
                if response.status_code == 400:
                    loggerb.warning("Bad request to secure message service")
                    get_json = json.loads(response.content)
                    return render_template('secure-messages/secure-messages-draft.html',
                                           _theme='default',
                                           draft=data,
                                           errors=get_json)
                elif response.status_code != 201:
                    loggerb.error("Failed to save draft")
                    raise ExternalServiceError(response)

            response_data = json.loads(response.text)
            loggerb = loggerb.bind(message_id=response_data['msg_id'])
            loggerb.info('Saved draft successfully')
            loggerb.debug('Retrieving saved draft')
            get_draft = requests.get(DRAFT_GET_API_URL.format(response_data['msg_id']), headers=headers)

            if get_draft.status_code != 200:
                loggerb.error('Failed to retrieve saved draft')
                raise ExternalServiceError(get_draft)
            loggerb.debug('Retrieved saved draft')
            get_json = json.loads(get_draft.content)
            return render_template('secure-messages/secure-messages-draft.html',
                                   _theme='default',
                                   draft=get_json,
                                   errors={})

    return render_template('secure-messages/secure-messages-create.html', _theme='default', draft={})


@secure_message_bp.route('/reply-message', methods=['GET', 'POST'])
@jwt_authorization(request)
def reply_message(session):
    """Handles replying to an existing message"""

    if request.method == 'POST':
        party_id = session['party_id']
        loggerb = logger.bind(party_id=party_id)

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

        if "msg_id" in request.form:
            data["msg_id"] = request.form['msg_id']
            loggerb = loggerb.bind(message_id=data["msg_id"])
            loggerb.debug('Message already exists as draft')

        if request.form['submit'] == 'Send':
            return message_check_response(data, loggerb)

        if request.form['submit'] == 'Save draft':

            if "msg_id" in request.form:
                loggerb.info('Attempting to modify draft')
                response = requests.put(DRAFT_PUT_API_URL.format(request.form['msg_id']),
                                        data=json.dumps(data),
                                        headers=headers)
                if response.status_code == 400:
                    logger.warning("Bad request to secure message service")
                    get_json = json.loads(response.content)
                    return render_template('secure-messages/secure-messages-draft.html',
                                           _theme='default',
                                           draft=data,
                                           errors=get_json)
                elif response.status_code != 200:
                    logger.error("Failed to modify draft")
                    raise ExternalServiceError(response)
            else:
                loggerb.info("Attempting to save draft")
                response = requests.post(DRAFT_SAVE_API_URL, data=json.dumps(data), headers=headers)
                if response.status_code == 400:
                    loggerb.warning("Bad request to secure message service")
                    get_json = json.loads(response.content)
                    return render_template('secure-messages/secure-messages-draft.html',
                                           _theme='default',
                                           draft=data,
                                           errors=get_json)
                elif response.status_code != 201:
                    loggerb.error("Failed to save draft")
                    raise ExternalServiceError(response)

            response_data = json.loads(response.text)

            loggerb.debug('Successfully saved draft')
            loggerb.debug('Retrieving saved draft')
            get_draft = requests.get(DRAFT_GET_API_URL.format(response_data['msg_id']), headers=headers)
            get_json = json.loads(get_draft.content)
            loggerb = loggerb.bind(message_id=get_json['msg_id'])
            if get_draft.status_code != 200:
                logger.error('Failed to retrieve saved draft')
                raise ExternalServiceError(get_draft)
            loggerb.debug('Retrieved saved draft')
            return render_template('secure-messages/secure-messages-draft.html', _theme='default', draft=get_json)

    return render_template('secure-messages/secure-messages-create.html', _theme='default', draft={})


def message_check_response(data, logger):
    headers['Authorization'] = request.cookies['authorization']
    logger.info("Attempting to send message")

    response = requests.post(CREATE_MESSAGE_API_URL, data=json.dumps(data), headers=headers)
    if response.status_code == 400:
        logger.warning("Bad request to secure message service")
        get_json = json.loads(response.content)
        return render_template('secure-messages/secure-messages-create.html',
                               _theme='default',
                               draft=data,
                               errors=get_json)
    elif response.status_code != 201:
        logger.error('Failed to create message')
        raise ExternalServiceError(response)

    response_data = json.loads(response.text)
    logger.debug('Secure Message sent successfully', message_id=response_data['msg_id'])
    return render_template('secure-messages/message-success-temp.html', _theme='default')


@secure_message_bp.route('/messages/', methods=['GET'])
@secure_message_bp.route('/messages/<label>', methods=['GET'])
@jwt_authorization(request)
def messages_get(session, label="INBOX"):
    """Gets users messages"""
    party_id = session['party_id']
    loggerb = logger.bind(party_id=party_id)
    headers['Authorization'] = request.cookies['authorization']
    headers['Content-Type'] = 'application/json'
    loggerb.info('Attempting to retrieve messages', label=label)
    url = MESSAGES_API_URL

    if label is not None:
        url = url + "&label=" + label

    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        logger.error('Error retrieving user messages', label=label)
        raise ExternalServiceError(resp)

    response_data = json.loads(resp.text)
    total_msgs = 0

    for x in range(0, len(response_data['messages'])):
        if "UNREAD" in response_data['messages'][x]["labels"]:
            total_msgs += 1
    logger.info('Retrieved messages successfully')
    return render_template('secure-messages/secure-messages.html', _theme='default', messages=response_data['messages'],
                           links=response_data['_links'], label=label, total=total_msgs)


@secure_message_bp.route('/draft/<draft_id>', methods=['GET'])
@jwt_authorization(request)
def draft_get(session, draft_id):
    """Get draft message"""
    party_id = session['party_id']
    loggerb = logger.bind(message_id=draft_id, party_id=party_id)
    loggerb.debug('Retrieving draft')

    url = DRAFT_GET_API_URL.format(draft_id)
    get_draft = requests.get(url, headers=headers)
    if get_draft.status_code != 200:
        logger.error('Failed to retrieve draft')
        raise ExternalServiceError(get_draft)

    draft = json.loads(get_draft.text)
    logger.info('Retrieved draft successfully')
    return render_template('secure-messages/secure-messages-draft.html', _theme='default', draft=draft)


@secure_message_bp.route('/sent/<sent_id>', methods=['GET'])
@jwt_authorization(request)
def sent_get(session, sent_id):
    """Get sent message"""
    party_id = session['party_id']
    loggerb = logger.bind(message_id=sent_id, party_id=party_id)

    url = MESSAGE_GET_URL.format(sent_id)
    loggerb.debug('Retrieving message')
    get_sent = requests.get(url, headers=headers)
    if get_sent.status_code != 200:
        loggerb.error('Failed to retrieve message')
        raise ExternalServiceError(get_sent)

    sent = json.loads(get_sent.text)
    loggerb.info('Retrieved message successfully')
    return render_template('secure-messages/secure-messages-sent-view.html', _theme='default', message=sent)


@secure_message_bp.route('/message/<msg_id>', methods=['GET'])
@jwt_authorization(request)
def message_get(session, msg_id):
    """Get message"""
    party_id = session['party_id']
    loggerb = logger.bind(message_id=msg_id, party_id=party_id)

    loggerb.debug('Attempting to remove unread label')
    data = {"label": 'UNREAD', "action": 'remove'}
    response = requests.put(MESSAGE_MODIFY_URL.format(msg_id), data=json.dumps(data), headers=headers)  # noqa: F841
    if response.status_code != 200:
        loggerb.error("Failed to remove unread label")
        raise ExternalServiceError(response)

    loggerb.debug('Retrieving message')
    url = MESSAGE_GET_URL.format(msg_id)
    get_message = requests.get(url, headers=headers)
    if get_message.status_code != 200:
        loggerb.error('Failed to retrieve message')
        raise ExternalServiceError(get_message)
    message = json.loads(get_message.text)
    loggerb.debug('Retrieved message successfully')
    return render_template('secure-messages/secure-messages-view.html', _theme='default', message=message)
