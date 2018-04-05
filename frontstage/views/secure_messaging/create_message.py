import json
import logging

from flask import redirect, render_template, request, url_for
from frontstage.common.authorisation import jwt_authorization
from structlog import wrap_logger

from frontstage import app
from frontstage.common.api_call import api_call
from frontstage.common.session import SessionHandler
from frontstage.exceptions.exceptions import ApiError
from frontstage.models import SecureMessagingForm
from frontstage.views.secure_messaging import secure_message_bp


logger = wrap_logger(logging.getLogger(__name__))


@secure_message_bp.route('/create-message/', methods=['GET', 'POST'])
@jwt_authorization(request)
def create_message(session):
    case_id = request.args.get('case_id')
    survey = request.args['survey']
    ru_ref = request.args['ru_ref']
    party_id = session['party_id']
    form = SecureMessagingForm(request.form)
    if request.method == 'POST' and form.validate():
        send_message(party_id, case_id, survey, ru_ref)
        return redirect(url_for('secure_message_bp.view_conversation_list'))

    return render_template('secure-messages/secure-messages-view.html',
                           _theme='default', ru_ref=ru_ref,
                           survey=survey, case_id=case_id,
                           form=form, errors=form.errors)


def send_message(party_id, case_id, survey, ru_ref):
    logger.debug('Attempting to send message', party_id=party_id)
    form = SecureMessagingForm(request.form)

    headers = create_headers()
    endpoint = app.config['SEND_MESSAGE_URL']
    subject = form['subject'].data if form['subject'].data else form['hidden_subject'].data
    message_json = {
        'msg_from': party_id,
        'msg_to': ['GROUP'],
        'subject': subject,
        'body': form['body'].data,
        'thread_id': form['thread_id'].data,
        'ru_id': ru_ref,
        'survey': survey,
    }
    if case_id:
        message_json['collection_case'] = case_id

    response = api_call('POST', endpoint, json=message_json, headers=headers)

    if response.status_code != 200:
        logger.debug('Failed to send message', party_id=party_id)
        raise ApiError(response)
    sent_message = json.loads(response.text)

    logger.info('Secure message sent successfully',
                message_id=sent_message['msg_id'], party_id=party_id)
    return sent_message


def create_headers():
    encoded_jwt = SessionHandler().get_encoded_jwt(request.cookies['authorization'])
    headers = {"jwt": encoded_jwt}
    return headers
