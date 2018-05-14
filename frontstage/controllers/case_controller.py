import logging

import requests
from flask import current_app as app
from structlog import wrap_logger

from frontstage.exceptions.exceptions import ApiError, InvalidCaseCategory


logger = wrap_logger(logging.getLogger(__name__))


def get_case_by_enrolment_code(enrolment_code):
    logger.debug('Attempting to retrieve case by enrolment code', enrolment_code=enrolment_code)
    url = f"{app.config['CASE_URL']}/cases/iac/{enrolment_code}"
    response = requests.get(url, auth=app.config['CASE_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        log_level = logger.warning if response.status_code == 404 else logger.exception
        log_level('Failed to retrieve case', enrolment_code=enrolment_code)
        raise ApiError(response)

    logger.debug('Successfully retrieved case by enrolment code', enrolment_code=enrolment_code)
    return response.json()


def get_cases_by_party_id(party_id, case_events=False):
    logger.debug('Attempting to retrieve cases by party id', party_id=party_id)
    url = f"{app.config['CASE_URL']}/cases/partyid/{party_id}"
    if case_events:
        url = f'{url}?caseevents=true'
    response = requests.get(url, auth=app.config['CASE_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        log_level = logger.warning if response.status_code == 404 else logger.exception
        log_level('Failed to retrieve cases', party_id=party_id)
        raise ApiError(response)

    logger.debug('Successfully retrieved cases by party id', party_id=party_id)
    return response.json()


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
    return response.json()


def get_case_id_for_group(case_list, case_group_id):
    if case_group_id:
        for case in case_list:
            if case_group_id == case.get('caseGroup', {}).get('id'):
                return case['id']


def validate_case_category(category):
    logger.debug('Validating case category', category=category)
    categories = get_case_categories()
    category_names = [cat['name'] for cat in categories]
    if category not in category_names:
        raise InvalidCaseCategory(category)
    logger.debug('Successfully validated case category', category=category)


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
