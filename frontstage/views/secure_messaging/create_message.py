import json
import logging

from flask import redirect, render_template, request, url_for
from frontstage.common.authorisation import jwt_authorization
from structlog import wrap_logger

from frontstage import app
from frontstage.common.api_call import api_call
from frontstage.exceptions.exceptions import ApiError
from frontstage.models import SecureMessagingForm
from frontstage.views.secure_messaging.message_get import create_headers, get_message, message_get
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
        is_draft = form.save_draft.data
        sent_message = send_message(party_id, is_draft, case_id, survey, ru_ref)

        # If draft was saved retrieve the saved draft
        if is_draft:
            logger.info('Draft sent successfully', message_id=sent_message['msg_id'], party_id=party_id)
            return message_get('DRAFT', sent_message['msg_id'])

        return redirect(url_for('secure_message_bp.messages_get', new_message=True))

    else:
        if form['thread_message_id'].data:
            message = get_message(form['thread_message_id'].data, 'INBOX', party_id)
        else:
            message = {}
        return render_template('secure-messages/secure-messages-view.html', _theme='default', ru_ref=ru_ref,
                               survey=survey, case_id=case_id, form=form, errors=form.errors, message=message.get('message', {}))


def send_message(party_id, is_draft, case_id, survey, ru_ref):
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

    # If message has previously been saved as a draft add through the message id
    if form["msg_id"].data:
        message_json["msg_id"] = form['msg_id'].data
    response = api_call('POST', endpoint, parameters={"is_draft": is_draft},
                        json=message_json, headers=headers)

    if response.status_code != 200:
        logger.debug('Failed to send message', party_id=party_id)
        raise ApiError(response)
    sent_message = json.loads(response.text)

    logger.info('Secure message sent successfully',
                message_id=sent_message['msg_id'], party_id=party_id)
    return sent_message
