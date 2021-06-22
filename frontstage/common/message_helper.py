import logging
from datetime import datetime, date

from dateutil.tz import tz
from structlog import wrap_logger

logger = wrap_logger(logging.getLogger(__name__))


def refine(message):
    return {
        'thread_id': message.get('thread_id'),
        'subject': get_message_subject(message),
        'body': message.get('body'),
        'survey_id': message.get('survey_id', None),
        'ru_ref': get_ru_ref_from_message(message),
        'from': get_from_name(message),  # As displayed to user
        'from_internal': from_internal(message),
        'internal_user': get_internal_user_id(message),
        'sent_date': get_human_readable_date(message.get('sent_date')),
        'unread': get_unread_status(message),
        'message_id': message.get('msg_id')
    }


def from_internal(message):
    """returns True if this message was sent by an internal user, else False"""
    return message.get('from_internal', False)


def get_internal_user_id(message):
    """Determine the secure message id of the internal user associated with this message. Note the @msg_to field
    supports multiple recipients and is a list , hence for msg_to we use the 0th element"""

    return message['@msg_from']['id'] if from_internal(message) else message['@msg_to'][0]['id']


def get_message_subject(message):
    try:
        subject = message["subject"]
        return subject
    except KeyError:
        logger.error('Failed to retrieve Subject from thread')
        raise


def get_from_name(message):
    if from_internal(message):
        return "ONS Business Surveys Team"

    try:
        msg_from = message['@msg_from']
    except KeyError:
        logger.error('Failed to retrieve name from message', message_id=message.get('msg_id'))
        raise

    return f"{msg_from.get('firstName')} {msg_from.get('lastName')}"


def get_ru_ref_from_message(message):
    if not message['@business_details']:
        return None
    try:
        return message['@business_details']['id']
    except (KeyError, TypeError):
        logger.error('Failed to retrieve RU ref from message', message_id=message.get('msg_id'))
        raise


def get_human_readable_date(sent_date):
    try:
        formatted_date = get_formatted_date(sent_date.split('.')[0])
        return formatted_date
    except (AttributeError, ValueError, IndexError, TypeError):
        logger.error('Failed to parse sent date from message', sent_date=sent_date)


def get_unread_status(message):
    return 'UNREAD' in message.get('labels', [])


def get_formatted_date(datetime_string, string_format='%Y-%m-%d %H:%M:%S'):
    """Takes a string date in given format returns a string 'today', 'yesterday' at the time in format '%H:%M'
    if the given date is today or yesterday respectively otherwise returns the full date in the format '%b %d %Y %H:%M'.
    If datetime_string is not a valid date in the given format it is returned with no formatting.
    """
    try:
        datetime_parsed = datetime.strptime(datetime_string, string_format)
    except (OverflowError, ValueError, AttributeError):
        # Passed value wasn't date-ish or date arguments out of range
        logger.error('Failed to parse date', sent_date=datetime_string)
        return datetime_string

    time_difference = datetime_parsed.date() - date.today()

    time = convert_to_bst(datetime_parsed).strftime('%H:%M')

    if time_difference.days == 0:
        return f"Today at {time}"
    elif time_difference.days == -1:
        return f"Yesterday at {time}"
    return "{} {}".format(datetime_parsed.strftime('%d %b %Y'), time)


def convert_to_bst(datetime_parsed):
    """Takes a datetime and adjusts based on BST or GMT.
    Returns adjusted datetime
    """
    return datetime_parsed.replace(tzinfo=tz.gettz('UTC')).astimezone(tz.gettz('Europe/London'))
