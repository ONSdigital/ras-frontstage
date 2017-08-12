import requests
import logging
from json import loads, dumps
from frontstage import app
from structlog import wrap_logger
_categories = None

logger = wrap_logger(logging.getLogger(__name__))

def post_event(case_id, description=None, category=None, party_id=None, created_by=None, payload=None):
    """
    Post an event to the case service ...

    :param case_id: The Id if the case to post against
    :param description: Event description
    :param category: Event category (must be a valid category)
    :param party_id: Party Id
    :param created_by: Who created the event
    :param payload: An optional event payload
    :return: status, message
    """
    #
    #   Start by making sure we were given a working data set
    #
    if not (description and category and party_id and created_by):
        msg = 'description={} category={} party_id={} created_by={}'.format(
            description, category, party_id, created_by
        )
        logger.error('Insufficient arguments', arguments=msg)
        return 500, {'code': 500, 'text': 'insufficient arguments'}
    #
    #   If this is our first time, we need to acquire the current set of valid categories
    #   form the case service in order to validate the type of the message we're going to post
    #
    global _categories
    if not _categories:
        logger.debug('@ caching event category list')
        resp = requests.get('{}categories'.format(app.config['RM_CASE_SERVICE']))
        if resp.status_code != 200:
            return 404, {'code': 404, 'text': 'error loading categories'}
        _categories = {}
        categories = loads(resp.text)
        for cat in categories:
            action = cat.get('name')
            if action:
                _categories[action] = cat
            else:
                logger.error('received unknown category "{}"'.format(str(cat)))
        logger.debug('@ cached ({}) categories'.format(len(categories)))
    #
    #   Make sure the category we have is valid
    #
    if category not in _categories:
        logger.error(error='invalid category code', category=category)
        return 404, {'code': 404, 'text': 'invalid category code - {}'.format(category)}
    #
    #   Build a message to post
    #
    message = {
        'description': description,
        'category': category,
        'partyId': party_id,
        'createdBy': created_by
    }
    #
    #   If we have anything in the optional payload, add it to the message
    #
    if payload:
        message = dict(message, **payload)
    #
    #   Call the poster, returning the actual status and text to the caller
    #

    logger.info("Posting case event: {} for case_id: {} party_id: {} ".format(category, case_id, party_id))

    headers = {'Content-Type': 'application/json'}
    resp = requests.post(
                    '{}cases/{}/events'.format(app.config['RM_CASE_SERVICE'], case_id),
                    data=dumps(message),
                    headers=headers)
    if resp.status_code == 201:
        logger.debug('case event posted OK')
        return 200, 'OK'

    logger.debug(str(loads(resp.text)))

    return resp.status_code, {'code': resp.status_code, 'text': resp.text}
