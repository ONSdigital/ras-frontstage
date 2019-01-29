import logging

import requests
from flask import current_app as app
from structlog import wrap_logger

from frontstage.common.thread_wrapper import ThreadWrapper
from frontstage.controllers import case_controller, collection_exercise_controller, collection_instrument_controller, \
    survey_controller
from frontstage.exceptions.exceptions import ApiError, UserDoesNotExist

CLOSED_STATE = ['COMPLETE', 'COMPLETEDBYPHONE', 'NOLONGERREQUIRED']

logger = wrap_logger(logging.getLogger(__name__))


def get_respondent_party_by_id(party_id):
    logger.debug('Retrieving party from party service by id', party_id=party_id)

    url = f"{app.config['PARTY_URL']}/party-api/v1/respondents/id/{party_id}"
    response = requests.get(url, auth=app.config['PARTY_AUTH'])

    if response.status_code == 404:
        return

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response,
                       message='Failed to find respondent',
                       party_id=party_id)

    logger.debug('Successfully retrieved party details', party_id=party_id)
    return response.json()


def add_survey(party_id, enrolment_code):
    logger.debug('Attempting to add a survey', party_id=party_id)

    url = f"{app.config['PARTY_URL']}/party-api/v1/respondents/add_survey"
    request_json = {'party_id': party_id, 'enrolment_code': enrolment_code}
    response = requests.post(url, auth=app.config['PARTY_AUTH'], json=request_json)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response,
                       log_level='warning' if response.status_code == 404 else 'error',
                       message='Failed to add a survey',
                       party_id=party_id)

    logger.debug('Successfully added a survey', party_id=party_id)


def change_password(password, token):
    logger.debug('Attempting to change password through the party service')

    data = {'new_password': password}
    url = f"{app.config['PARTY_URL']}/party-api/v1/respondents/change_password/{token}"
    response = requests.put(url, auth=app.config['PARTY_AUTH'], json=data)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response,
                       log_level='warning' if response.status_code == 404 else 'exception',
                       message='Failed to send change password request to party service',
                       token=token)

    logger.debug('Successfully changed password through the party service')


def create_account(registration_data):
    logger.debug('Attempting to create account')

    url = f"{app.config['PARTY_URL']}/party-api/v1/respondents"
    registration_data['status'] = 'CREATED'
    response = requests.post(url, auth=app.config['PARTY_AUTH'], json=registration_data)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        if response.status_code == 400:
            message = 'Email has already been used'
        else:
            message = 'Failed to create account'
        raise ApiError(logger, response,
                       log_level='debug' if response.status_code == 400 else 'error',
                       message=message)

    logger.debug('Successfully created account')


def get_party_by_business_id(party_id, party_url, party_auth, collection_exercise_id=None):
    logger.debug('Attempting to retrieve party by business', party_id=party_id)

    url = f"{party_url}/party-api/v1/businesses/id/{party_id}"
    if collection_exercise_id:
        url += f"?collection_exercise_id={collection_exercise_id}&verbose=True"
    response = requests.get(url, auth=party_auth)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response,
                       collection_exercise_id=collection_exercise_id,
                       log_level='warning' if response.status_code == 404 else 'exception',
                       message='Failed to retrieve party by business',
                       party_id=party_id)

    logger.debug('Successfully retrieved party by business',
                 collection_exercise_id=collection_exercise_id,
                 party_id=party_id)
    return response.json()


def get_respondent_by_email(email):
    logger.debug('Attempting to find respondent party by email')

    url = f"{app.config['PARTY_URL']}/party-api/v1/respondents/email"
    response = requests.get(url, json={"email": email}, auth=app.config['PARTY_AUTH'])

    if response.status_code == 404:
        logger.debug('Failed to retrieve party by email')
        return

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response, message='Error retrieving respondent by email')

    logger.debug('Successfully retrieved respondent by email')
    return response.json()


def resend_verification_email(party_id):
    logger.debug('Re-sending verification email', party_id=party_id)
    url = f'{app.config["PARTY_URL"]}/party-api/v1/resend-verification-email/{party_id}'
    response = requests.post(url, auth=app.config['PARTY_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.exception('Re-sending of verification email failed', party_id=party_id)
        raise ApiError(logger, response, log_level='exception', message='Re-sending of verification email failed')

    logger.debug('Successfully re-sent verification email', party_id=party_id)


def resend_verification_email_expired_token(token):
    logger.debug('Re-sending verification email', token=token)
    url = f'{app.config["PARTY_URL"]}/party-api/v1/resend-verification-email-expired-token/{token}'
    response = requests.post(url, auth=app.config['PARTY_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response, log_level='exception',
                       message='Re-sending of verification email for expired token failed')


def reset_password_request(username):
    logger.debug('Attempting to send reset password request to party service')

    url = f"{app.config['PARTY_URL']}/party-api/v1/respondents/request_password_change"
    data = {"email_address": username}
    response = requests.post(url, auth=app.config['PARTY_AUTH'], json=data)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        if response.status_code == 404:
            raise UserDoesNotExist("User does not exist in party service")
        message = 'Failed to send reset password request to party service'
        raise ApiError(logger, response, log_level='exception', message=message)

    logger.debug('Successfully sent reset password request to party service')


def resend_password_email_expired_token(token):
    logger.debug('Re-sending verification email', token=token)
    url = f'{app.config["PARTY_URL"]}/party-api/v1/resend-password-email-expired-token/{token}'
    response = requests.post(url, auth=app.config['PARTY_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response, log_level='exception',
                       message='Re-sending of password email for expired token failed')


def verify_email(token):
    logger.debug('Attempting to verify email address', token=token)

    url = f"{app.config['PARTY_URL']}/party-api/v1/emailverification/{token}"
    response = requests.put(url, auth=app.config['PARTY_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        log_level = 'warning' if response.status_code == 404 else 'error'
        raise ApiError(logger, response, log_level=log_level, message='Failed to verify email', token=token)

    logger.debug('Successfully verified email address', token=token)


def verify_token(token):
    logger.debug('Attempting to verify token with party service')

    url = f"{app.config['PARTY_URL']}/party-api/v1/tokens/verify/{token}"
    response = requests.get(url, auth=app.config['PARTY_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        log_level = 'warning' if response.status_code == 404 else 'error'
        raise ApiError(logger, response, log_level=log_level, message='Failed to verify token', token=token)

    logger.debug('Successfully verified token')


def get_respondent_enrolments(party_id):
    respondent = get_respondent_party_by_id(party_id)
    for association in respondent['associations']:
        for enrolment in association['enrolments']:
            if enrolment['enrolmentStatus'] == 'ENABLED':
                yield {
                    'business_id': association['partyId'],
                    'survey_id': enrolment['surveyId']
                }


def set_enrolment_data(enrolment_data):
    surveys_ids = set()
    business_ids = set()
    for enrolment in enrolment_data:
        surveys_ids.add(enrolment['survey_id'])
        business_ids.add(enrolment['business_id'])
    return surveys_ids, business_ids


def caching_data_for_survey_list(cache_data, surveys_ids, business_ids, tag):
    # Creates a list of threads which will call functions to set the survey, case, party and collex responses
    # in the cache_data.

    threads = []

    for survey_id in surveys_ids:
        threads.append(ThreadWrapper(get_survey, cache_data, survey_id, app.config['SURVEY_URL'],
                                     app.config['SURVEY_AUTH']))
        threads.append(ThreadWrapper(get_collex, cache_data, survey_id, app.config['COLLECTION_EXERCISE_URL'],
                                     app.config['COLLECTION_EXERCISE_AUTH']))

    for business_id in business_ids:
        threads.append(ThreadWrapper(get_case, cache_data, business_id, app.config['CASE_URL'],
                                     app.config['CASE_AUTH'], tag))
        threads.append(ThreadWrapper(get_party, cache_data, business_id, app.config['PARTY_URL'],
                                     app.config['PARTY_AUTH']))

    for thread in threads:
        thread.start()

    # We do a thread join to make sure that the threads have all terminated before it carries on
    for thread in threads:
        thread.join()


def caching_data_for_collection_instrument(cache_data):
    # This function creates a list of threads from the collection instrument id in the cache_data of the cases.
    collection_instrument_ids = set()
    threads = []
    for business_id, cases in cache_data['cases'].items():
        for case in cases:
            collection_instrument_ids.add(case['collectionInstrumentId'])
    for collection_instrument_id in collection_instrument_ids:
        threads.append(ThreadWrapper(get_collection_instrument, cache_data, collection_instrument_id,
                                     app.config['COLLECTION_INSTRUMENT_URL'], app.config['COLLECTION_INSTRUMENT_AUTH']))

    for thread in threads:
        thread.start()

    # We do a thread join to make sure that the threads have all terminated before it carries on
    for thread in threads:
        thread.join()


def get_survey_list_details_for_party(party_id, tag, business_party_id, survey_id):

    """
    This function uses threads to get responses from Case, Party, Collection exercise, Survey and
    Collection Instrument services. Some respondents to-do pages can have so many Surveys/Collection exercises
    that it'll cause the page to timeout before finishing the load. Doing this in threads speeds it up and using
    sets makes sure we're not using repeating calls to the services.

    :party_id: This is the respondents uuid
    :tag: This is the page that is being called e.g. to-do, history
    :business_party_id: This is the businesses uuid
    :survey_id: This is the surveys uuid

    """
    enrolment_data = get_respondent_enrolments(party_id)

    # Gets the survey ids and business ids from the enrolment data that has been generated.

    surveys_ids, business_ids = set_enrolment_data(enrolment_data)

    # This is a dictionary that will store all of the data that is going to be cached instead of making multiple calls
    # inside of the for loop for get_respondent_enrolments.

    cache_data = {'surveys': dict(),
                  'businesses': dict(),
                  'collexes': dict(),
                  'cases': dict(),
                  'instrument': dict()}

    # These two will call the services to get responses and cache the data for later use.

    caching_data_for_survey_list(cache_data, surveys_ids, business_ids, tag)
    caching_data_for_collection_instrument(cache_data)

    for enrolment in get_respondent_enrolments(party_id):

        business_party = cache_data['businesses'][enrolment['business_id']]
        survey = cache_data['surveys'][enrolment['survey_id']]
        live_collection_exercises = cache_data['collexes'][survey['id']]
        collection_exercises_by_id = dict((ce['id'], ce) for ce in live_collection_exercises)
        cases = cache_data['cases'][business_party['id']]
        enrolled_cases = [case for case in cases if case['caseGroup']['collectionExerciseId'] in collection_exercises_by_id.keys()]

        for case in enrolled_cases:
            collection_exercise = collection_exercises_by_id[case['caseGroup']['collectionExerciseId']]
            added_survey = True if business_party_id == business_party['id'] and survey_id == survey['id'] else None
            display_access_button = display_button(case['caseGroup']['caseGroupStatus'], cache_data['instrument']
                                                                    [case['collectionInstrumentId']]['type'])

            yield {

                'case_id': case['id'],
                'status': case_controller.calculate_case_status(case['caseGroup']['caseGroupStatus'],
                                                                cache_data['instrument']
                                                                [case['collectionInstrumentId']]['type']),
                'collection_instrument_type': cache_data['instrument'][case['collectionInstrumentId']]['type'],
                'survey_id': survey['id'],
                'survey_long_name': survey['longName'],
                'survey_short_name': survey['shortName'],
                'survey_ref': survey['surveyRef'],
                'business_party_id': business_party['id'],
                'business_name': business_party['name'],
                'trading_as': business_party['trading_as'],
                'business_ref': business_party['sampleUnitRef'],
                'period': collection_exercise['userDescription'],
                'submit_by': collection_exercise['events']['return_by']['date'],
                'collection_exercise_ref': collection_exercise['exerciseRef'],
                'added_survey': added_survey,
                'display_button': display_access_button
            }


def get_survey(cache_data, survey_id, survey_url, survey_auth):
    cache_data['surveys'][survey_id] = survey_controller.get_survey(survey_url, survey_auth, survey_id)


def get_collex(cache_data, survey_id, collex_url, collex_auth):
    cache_data['collexes'][survey_id] = collection_exercise_controller.\
        get_live_collection_exercises_for_survey(survey_id, collex_url, collex_auth)


def get_case(cache_data, business_id, case_url, case_auth, tag):
    cache_data['cases'][business_id] = case_controller.get_cases_for_list_type_by_party_id(business_id, case_url,
                                                                                           case_auth, tag)


def get_party(cache_data, business_id, party_url, party_auth):
    cache_data['businesses'][business_id] = get_party_by_business_id(business_id, party_url, party_auth)


def get_collection_instrument(cache_data, collection_instrument_id, collection_instrument_url,
                              collection_instrument_auth):
    cache_data['instrument'][collection_instrument_id] = collection_instrument_controller. \
        get_collection_instrument(collection_instrument_id, collection_instrument_url, collection_instrument_auth)


def display_button(status, ci_type):
    return not(ci_type == 'EQ' and status in CLOSED_STATE)


def is_respondent_enrolled(party_id, business_party_id, survey_short_name, return_survey=False):
    survey = survey_controller.get_survey_by_short_name(survey_short_name)
    for enrolment in get_respondent_enrolments(party_id):
        if enrolment['business_id'] == business_party_id and enrolment['survey_id'] == survey['id']:
            if return_survey:
                return {'survey': survey}
            return True


def notify_party_and_respondent_account_locked(respondent_id, email_address, status=None):
    logger.debug('Notifying respondent and party service that account is locked')
    url = f'{app.config["PARTY_URL"]}/party-api/v1/respondents/edit-account-status/{respondent_id}'

    data = {
        'respondent_id': respondent_id,
        'email_address': email_address,
        'status_change': status
    }

    response = requests.put(url, json=data, auth=app.config['PARTY_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error('Failed to notify party', respondent_id=respondent_id, status=status)
        raise ApiError(logger, response)

    logger.info('Successfully notified party and respondent', respondent_id=respondent_id, status=status)
