import logging
from datetime import datetime, date

from structlog import wrap_logger

logger = wrap_logger(logging.getLogger(__name__))


def refine(message):
    return {
        'thread_id': message.get('thread_id'),
        'subject': _get_message_subject(message),
        'body': message.get('body'),
        'internal': message.get('from_internal'),
        'survey_id': message.get('survey'),
        'ru_ref': _get_ru_ref_from_message(message),
        'business_name': _get_business_name_from_message(message),
        'from': _get_from_name(message),
        'sent_date': _get_human_readable_date(message.get('sent_date')),
        'unread': _get_unread_status(message),
        'message_id': message.get('msg_id')
    }


def _get_message_subject(thread):
    try:
        subject = thread["subject"]
        return subject
    except KeyError:
        logger.exception("Failed to retrieve Subject from thread")
        return None

def _get_from_name(message):
    try:
        msg_from = message['@msg_from']
        return "{} {}".format(msg_from.get('firstName'), msg_from.get('lastName'))
    except KeyError:
        logger.exception("Failed to retrieve message from name", message_id=message.get('msg_id'))


def _get_ru_ref_from_message(message):
    try:
        return message['@ru_id']['id']
    except (KeyError, TypeError):
        logger.exception("Failed to retrieve RU ref from message", message_id=message.get('msg_id'))


def _get_business_name_from_message(message):
    try:
        return message['@ru_id']['name']
    except (KeyError, TypeError):
        logger.exception("Failed to retrieve business name from message", message_id=message.get('msg_id'))


def _get_human_readable_date(sent_date):
    try:
        formatted_date = get_formatted_date(sent_date.split('.')[0])
        return formatted_date
    except (AttributeError, ValueError, IndexError, TypeError):
        logger.exception("Failed to parse sent date from message", sent_date=sent_date)


def _get_unread_status(message):
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
        logger.exception("Failed to parse date", sent_date=datetime_string)
        return datetime_string

    time_difference = datetime.date(datetime_parsed) - date.today()

    if time_difference.days == 0:
        return "Today at {}".format(datetime_parsed.strftime('%H:%M'))
    elif time_difference.days == -1:
        return "Yesterday at {}".format(datetime_parsed.strftime('%H:%M'))
    return "{} {}".format(datetime_parsed.strftime('%d %b %Y').title(), datetime_parsed.strftime('%H:%M'))
