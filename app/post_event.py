import requests
from flask import request
from json import loads, dumps
from ons_ras_common import ons_env
from ons_ras_common.ons_decorators import before_request
from app.config import Config

_categories = None


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
        ons_env.logger.error('Insufficient arguments', arguments=msg)
        return 500, {'code': 500, 'text': 'insufficient arguments'}
    #
    #   If this is our first time, we need to acquire the current set of valid categories
    #   form the case service in order to validate the type of the message we're going to post
    #
    global _categories
    if not _categories:
        ons_env.logger.info('@ caching event category list')
        resp = requests.get('{}categories'.format(Config.RM_CASE_SERVICE))
        if not resp.status_code:
            return 404, {'code': 404, 'text': 'error loading categories'}
        _categories = {}
        categories = loads(resp.text)
        for cat in categories:
            action = cat.get('name')
            if action:
                _categories[action] = cat
            else:
                ons_env.logger.warn('received unknown category "{}"'.format(str(cat)))
        ons_env.logger.info('@ cached ({}) categories'.format(len(categories)))
    #
    #   Make sure the category we have is valid
    #
    if category not in _categories:
        ons_env.logger.error(error='invalid category code', category=category)
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
    headers = {'Content-Type': 'application/json'}
    resp = requests.post(
                    '{}cases/{}/events'.format(Config.RM_CASE_SERVICE, case_id),
                    data=dumps(message),
                    headers=headers)
    if resp.status_code == 200:
        ons_env.logger.info('case event posted OK')
        return 200, 'OK'

    ons_env.logger.info(loads(resp.text))
    return resp.status_code, {'code': resp.status_code, 'text': resp.text}


#if __name__ == '__main__':
#    """
#    Try a test post against the currently defined case logging service.
#    HINT: set RM_CASE_SERVICE_PORT and RM_CASE_SERVICE_HOST
#    """
#    ons_env.setup()
#    post_event(
#        'ab548d78-c2f1-400f-9899-79d944b87300',
#        description="Test Event",
#        category='UNSUCCESSFUL_RESPONSE_UPLOAD',
#        party_id='db036fd7-ce17-40c2-a8fc-932e7c228397',
#        created_by='SYSTEM',
#        payload=None)

#    post_event(
#        'ab548d78-c2f1-400f-9899-79d944b87300',
#        description="Test Event",
#        category='SUCCESSFUL_RESPONSE_UPLOAD',
#        party_id='db036fd7-ce17-40c2-a8fc-932e7c228397',
#        created_by='SYSTEM',
#        payload=None)
