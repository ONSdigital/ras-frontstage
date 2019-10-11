import logging
from datetime import datetime

import requests
from flask import current_app as app
from iso8601 import parse_date, ParseError
from structlog import wrap_logger

from frontstage.exceptions.exceptions import ApiError


logger = wrap_logger(logging.getLogger(__name__))


def get_collection_exercise(collection_exercise_id):
    logger.info('Attempting to retrieve collection exercise', collection_exercise_id=collection_exercise_id)
    url = f"{app.config['COLLECTION_EXERCISE_URL']}/collectionexercises/{collection_exercise_id}"

    response = requests.get(url, auth=app.config['COLLECTION_EXERCISE_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error('Failed to retrieve collection exercise', collection_exercise_id=collection_exercise_id)
        raise ApiError(logger, response)

    logger.info('Successfully retrieved collection exercise', collection_exercise_id=collection_exercise_id)
    collection_exercise = response.json()

    if collection_exercise['events']:
        collection_exercise['events'] = convert_events_to_new_format(collection_exercise['events'])

    return collection_exercise


def get_collection_exercise_events(collection_exercise_id):
    logger.info('Attempting to retrieve collection exercise events', collection_exercise_id=collection_exercise_id)
    url = f"{app.config['COLLECTION_EXERCISE_URL']}/collectionexercises/{collection_exercise_id}/events"

    response = requests.get(url, auth=app.config['COLLECTION_EXERCISE_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error('Failed to retrieve collection exercise events', collection_exercise_id=collection_exercise_id)
        raise ApiError(logger, response)

    logger.info('Successfully retrieved collection exercise events', collection_exercise_id=collection_exercise_id)
    return response.json()


def get_collection_exercises_for_survey(survey_id, collex_url, collex_auth,  live_only=None):
    logger.info('Retrieving collection exercises for survey', survey_id=survey_id)

    if live_only is True:
        url = f"{collex_url}/collectionexercises/survey/{survey_id}?liveOnly=true"
    else:
        url = f"{collex_url}/collectionexercises/survey/{survey_id}"

    response = requests.get(url, auth=collex_auth)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error('Failed to retrieve collection exercises for survey', survey_id=survey_id)
        raise ApiError(logger, response)

    logger.info("Successfully retrieved collection exercises for survey", survey_id=survey_id)
    collection_exercises = response.json()

    for collection_exercise in collection_exercises:
        if collection_exercise['events']:
            collection_exercise['events'] = convert_events_to_new_format(collection_exercise['events'])

    return collection_exercises


def get_live_collection_exercises_for_survey(survey_id, collex_url, collex_auth):
    return get_collection_exercises_for_survey(survey_id, collex_url, collex_auth, True)


def convert_events_to_new_format(events):
    formatted_events = {}
    for event in events:
        try:
            date_time = parse_date(event['timestamp'])
        except ParseError:
            raise ParseError

        formatted_events[event['tag']] = {
            "date": date_time.strftime('%d %b %Y'),
            "month": date_time.strftime('%m'),
            "is_in_future": date_time > parse_date(datetime.now().isoformat())
        }
    return formatted_events
