import json
import logging

from flask import current_app as app
import requests
from structlog import wrap_logger

from frontstage.exceptions.exceptions import ApiError, InvalidCaseCategory, NoSurveyPermission


logger = wrap_logger(logging.getLogger(__name__))


def get_case_by_case_id(case_id):
    logger.debug('Retrieving case', case_id=case_id)
    url = f"{app.config['CASE_URL']}/cases/{case_id}"
    response = requests.get(url, auth=app.config['CASE_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        log_level = logger.warning if response.status_code == 404 else logger.exception
        log_level('Failed to retrieve case', case_id=case_id)
        raise ApiError(response)

    logger.debug('Successfully retrieved case', case_id=case_id)
    return json.loads(response.text)


def get_case_categories():
    logger.debug('Retrieving case categories')
    url = f"{app.config['CASE_URL']}/categories"
    response = requests.get(url, auth=app.config['CASE_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        log_level = logger.warning if response.status_code == 404 else logger.exception
        log_level('Failed to get case categories')
        raise ApiError(response)

    logger.debug('Successfully retrieved case categories')
    return json.loads(response.text)


def validate_case_category(category):
    logger.debug('Validating case category', category=category)
    categories = get_case_categories()
    category_names = [cat['name'] for cat in categories]
    if category not in category_names:
        raise InvalidCaseCategory(category)


def post_case_event(case_id, party_id, category, description):
    logger.debug('Posting case event', case_id=case_id)
    validate_case_category(category)
    url = f"{app.config['CASE_URL']}/cases/{case_id}/events"
    message = {
        'description': description,
        'category': category,
        'partyId': party_id,
        'createdBy': 'RAS_FRONTSTAGE'
    }
    response = requests.post(url, auth=app.config['CASE_AUTH'], json=message)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        log_level = logger.warning if response.status_code == 404 else logger.exception
        log_level('Failed to post case event', case_id=case_id)
        raise ApiError(response)

    logger.debug('Successfully posted case event', case_id=case_id)


def check_case_permissions(party_id, case_party_id, case_id=None):
    logger.debug('Party requesting access to case', party_id=party_id, case_id=case_id, case_party_id=case_party_id)
    if party_id != case_party_id:
        raise NoSurveyPermission(party_id, case_id, case_party_id)

    logger.debug('Party has permission to access case', party_id=party_id, case_id=case_id, case_party_id=case_party_id)
