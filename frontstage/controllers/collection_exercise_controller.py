import logging

import requests
from flask import current_app as app
from structlog import wrap_logger

from frontstage.common.list_helper import flatten_list
from frontstage.common.mappers import convert_events_to_new_format
from frontstage.exceptions.exceptions import ApiError


logger = wrap_logger(logging.getLogger(__name__))


def get_collection_exercise(collection_exercise_id):
    logger.debug('Attempting to retrieve collection exercise', collection_exercise_id=collection_exercise_id)
    url = f"{app.config['COLLECTION_EXERCISE_URL']}/collectionexercises/{collection_exercise_id}"

    response = requests.get(url, auth=app.config['COLLECTION_EXERCISE_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response,
                       collection_exercise_id=collection_exercise_id,
                       log_level='warning' if response.status_code == 404 else 'exception',
                       message='Failed to retrieve collection exercise')

    logger.debug('Successfully retrieved collection exercise', collection_exercise_id=collection_exercise_id)
    collection_exercise = response.json()

    if collection_exercise['events']:
        collection_exercise['events'] = convert_events_to_new_format(collection_exercise['events'])

    return collection_exercise


def get_collection_exercise_events(collection_exercise_id):
    logger.debug('Attempting to retrieve collection exercise events', collection_exercise_id=collection_exercise_id)
    url = f"{app.config['COLLECTION_EXERCISE_URL']}/collectionexercises/{collection_exercise_id}/events"

    response = requests.get(url, auth=app.config['COLLECTION_EXERCISE_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response,
                       collection_exercise_id=collection_exercise_id,
                       log_level='warning' if response.status_code == 404 else 'exception',
                       message='Failed to retrieve collection exercise events')

    logger.debug('Successfully retrieved collection exercise events', collection_exercise_id=collection_exercise_id)
    return response.json()


def get_collection_exercises_for_survey(survey_id):
    logger.debug('Retrieving collection exercises for survey', survey_id=survey_id)

    url = f"{app.config['COLLECTION_EXERCISE_URL']}/collectionexercises/survey/{survey_id}"

    response = requests.get(url, auth=app.config['COLLECTION_EXERCISE_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response,
                       survey_id=survey_id,
                       log_level='warning' if response.status_code == 404 else 'exception',
                       message='Failed to retrieve collection exercises for survey')

    logger.debug("Successfully retrieved collection exercises for survey", survey_id=survey_id)
    collection_exercises = response.json()

    for collection_exercise in collection_exercises:
        if collection_exercise['events']:
            collection_exercise['events'] = convert_events_to_new_format(collection_exercise['events'])

    return collection_exercises


def link_enrolment_with_collection_exercise(enrolment, collection_exercises):
    logger.debug("Attempting to retrieve collection exercise for enrolment",
                 survey=enrolment['survey']['id'],
                 business_party_id=enrolment['business_party']['id'])
    return [{**enrolment,
             "collection_exercise": collection_exercise}
            for collection_exercise in collection_exercises
            if collection_exercise['surveyId'] == enrolment['survey']['id']]


def get_enrolments_with_collection_exercises(enrolments):
    logger.debug("Attempting to retrieve collection exercises for enrolments")
    survey_ids = {enrolment['enrolment_details']['surveyId']
                  for enrolment in enrolments}
    collection_exercises = [get_collection_exercises_for_survey(survey_id)
                            for survey_id in survey_ids]
    flattened_collection_exercises = flatten_list(collection_exercises)
    live_collection_exercises = [collection_exercise
                                 for collection_exercise in flattened_collection_exercises
                                 if collection_exercise['state'] == 'LIVE'
                                 and not collection_exercise['events']['go_live']['is_in_future']]
    enrolments_with_ces = [link_enrolment_with_collection_exercise(enrolment, live_collection_exercises)
                           for enrolment in enrolments]
    logger.debug("Successfully retrieved collection exercises for enrolments")
    return flatten_list(enrolments_with_ces)
