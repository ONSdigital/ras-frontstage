from flask import Blueprint, render_template, request, json, redirect, url_for, session
import requests
import logging
from structlog import wrap_logger
from app.config import SecureMessaging


logger = wrap_logger(logging.getLogger(__name__))


headers = {'Content-Type': 'application/json',
           'Authorization': 'eyJhbGciOiJSU0EtT0FFUCIsImVuYyI6IkEyNTZHQ00ifQ.XMrQ2QMNcoWqv6Pm4KGPZRPAHMSNuCRrmdp-glDvf_9gDzYDoXkxbZEBqy6_pdMTIFINUWUABYa7PdLLuJh5uoU9L7lmvJKEYCq0e5rS076KLRc5pFKHJesgJLNijj7scLke3y4INkd0px82SHhnbek0bGLeu3i8FgRt4vD0Eu8TWODM7kEfAT_eRmvPBM1boyOqrpyhYgE9p0_NklwloFXdYZKjTvHxlHtbiuYmvXSTFkbbp_t8T1xZmDrfgS2EDWTFEagzyKBFFAH4Z5QRUUJPiuAxI3lSNS2atFFtDWiZRhuuhRyJzNA4vqTpmFPUE6h_iggkcbiUPofSBx3CUw.QK4lX7z2vN6jryJz.G9C1zoAvWHfAJywiuijq6E78xCMZ5NOAZD1g3e6PTWhveQKNecBJAPgXyRDVgljgIwSq_vBY2AVTIE5xWapwF3oLZyiC0T0H2LrjlpKFUa51-VU_-Yj8u4ax0iLvyWyRRepQneYJ0riF4zbmcGf1vCCEO3WOwcD5wXBFVXVH6wPqExmI2tjWWLdz2F7oK1Wnh1pbQX_EW5rYb2I4mPuc2J6ijXAr73qcJLAzJbjDo1uk.QrPCckVYuNlcWeCwQmws9A'}


modify_data = {'action': '',
               'label': ''}

secure_message_bp = Blueprint('secure_message_bp', __name__, static_folder='static', template_folder='templates')


@secure_message_bp.route('/create-message', methods=['GET', 'POST'])
def create_message():
    """Handles sending of new message"""

    if session.get('jwt_token'):
        if request.method == 'POST':
            if request.form['submit'] == 'Send message':
                data = {'msg_to': 'BRES', 'msg_from': '0a7ad740-10d5-4ecb-b7ca-3c0384afb882', 'subject': request.form['secure-message-subject'],
                        'body': request.form['secure-message-body'],
                        'collection_case': 'test', 'ru_id': 'f1a5e99c-8edf-489a-9c72-6cabe6c387fc', 'survey': 'BRES'}

                response = requests.post(SecureMessaging.CREATE_MESSAGE_API_URL, data=json.dumps(data), headers=headers)
                if response.status_code != 201:
                    # TODO replace with custom error page when available
                    return redirect(url_for('error_page'))
                resp_data = json.loads(response.text)
                logger.debug(resp_data['msg_id'])
                return render_template('message-success-temp.html', _theme='default')

            if request.form['submit'] == 'Save draft':
                data = {'msg_to': 'BRES', 'msg_from': '0a7ad740-10d5-4ecb-b7ca-3c0384afb882',
                        'subject': request.form['secure-message-subject'], 'body': request.form['secure-message-body'],
                        'collection_case': 'test', 'ru_id': 'f1a5e99c-8edf-489a-9c72-6cabe6c387fc', 'survey': 'BRES'}

                if "msg_id" in request.form:
                    data['msg_id'] = request.form['msg_id']
                    response = requests.put(SecureMessaging.DRAFT_PUT_API_URL.format(request.form['msg_id']), data=json.dumps(data), headers=headers)
                    if response.status_code != 200:
                        # TODO replace with custom error page when available
                        return redirect(url_for('error_page'))
                else:
                    response = requests.post(SecureMessaging.DRAFT_SAVE_API_URL, data=json.dumps(data), headers=headers)
                    if response.status_code != 201:
                        # TODO replace with custom error page when available
                        return redirect(url_for('error_page'))
                resp_data = json.loads(response.text)
                logger.debug(resp_data['msg_id'])
                get_draft = requests.get(SecureMessaging.DRAFT_GET_API_URL.format(resp_data['msg_id']), headers=headers)
                if get_draft.status_code != 200:
                    # TODO replace with custom error page when available
                    return redirect(url_for('error_page'))
                get_json = json.loads(get_draft.content)

                return render_template('secure-messages-draft.html', _theme='default', draft=get_json)

        return render_template('secure-messages-create.html', _theme='default')
    return render_template('not-signed-in.html', _theme='default', data={"error": {"type": "failed"}})


@secure_message_bp.route('/reply-message', methods=['GET', 'POST'])
def reply_message():
    """Handles replying to an existing message"""

    if session.get('jwt_token'):
        if request.method == 'POST':
            logger.info("Reply to Message")
            data = {'msg_to': 'BRES', 'msg_from': '0a7ad740-10d5-4ecb-b7ca-3c0384afb882',
                    'subject': 'reply_subject', 'body': request.form['secure-message-body'],
                    'thread_id': 'test', 'collection_case': 'test', 'ru_id': 'f1a5e99c-8edf-489a-9c72-6cabe6c387fc', 'survey': 'BRES'}

            response = requests.post(SecureMessaging.CREATE_MESSAGE_API_URL, data=json.dumps(data), headers=headers)
            if response.status_code != 201:
                # TODO replace with custom error page when available
                return redirect(url_for('error_page'))
            resp_data = json.loads(response.text)
            logger.debug(resp_data.get('msg_id', 'No response data.'))
            return render_template('message-success-temp.html', _theme='default')
    return render_template('not-signed-in.html', _theme='default', data={"error": {"type": "failed"}})


@secure_message_bp.route('/messages/<label>', methods=['GET'])
@secure_message_bp.route('/messages', methods=['GET'])
def messages_get(label='INBOX'):
    """Gets users messages"""

    if session.get('jwt_token'):
        url = SecureMessaging.MESSAGES_API_URL
        if label is not None:
            url = url + "&label=" + label
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            # TODO replace with custom error page when available
            return redirect(url_for('error_page'))
        resp_data = json.loads(resp.text)
        total_msgs = 0
        for x in range(0, len(resp_data['messages'])):
            if "UNREAD" in resp_data['messages'][x]["labels"]:
                total_msgs += 1
        return render_template('secure-messages.html', _theme='default', messages=resp_data['messages'], links=resp_data['_links'], label=label, total=total_msgs)
    return render_template('not-signed-in.html', _theme='default', data={"error": {"type": "failed"}})


@secure_message_bp.route('/draft/<draft_id>', methods=['GET'])
def draft_get(draft_id):
    """Get draft message"""
    if session.get('jwt_token'):
        url = SecureMessaging.DRAFT_GET_API_URL.format(draft_id)

        get_draft = requests.get(url, headers=headers)
        if get_draft.status_code != 200:
            # TODO replace with custom error page when available
            return redirect(url_for('error_page'))
        draft = json.loads(get_draft.text)

        return render_template('secure-messages-draft.html', _theme='default', draft=draft)
    return render_template('not-signed-in.html', _theme='default', data={"error": {"type": "failed"}})


@secure_message_bp.route('/message/<msg_id>', methods=['GET'])
def message_get(msg_id):
    """Get message"""

    if session.get('jwt_token'):
        if request.method == 'GET':
            data ={"label": 'UNREAD', "action": 'remove'}
            resp = requests.put(SecureMessaging.MESSAGE_MODIFY_URL.format(msg_id), data=json.dumps(data), headers=headers)

            url = SecureMessaging.MESSAGE_GET_URL.format(msg_id)

            get_message = requests.get(url, headers=headers)
            if get_message.status_code != 200:
                # TODO replace with custom error page when available
                return redirect(url_for('error_page'))
            message = json.loads(get_message.text)

            return render_template('secure-messages-view.html', _theme='default', message=message)
    return render_template('not-signed-in.html', _theme='default', data={"error": {"type": "failed"}})
