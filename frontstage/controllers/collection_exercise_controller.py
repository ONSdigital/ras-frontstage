import logging
from datetime import datetime, timedelta

import requests
from flask import current_app as app
from iso8601 import parse_date, ParseError
from structlog import wrap_logger

from frontstage.exceptions.exceptions import ApiError

logger = wrap_logger(logging.getLogger(__name__))

date_format = '%d %b %Y'


def get_collection_exercise(collection_exercise_id):
    logger.info('Attempting to retrieve collection exercise', collection_exercise_id=collection_exercise_id)
    url = f"{app.config['COLLECTION_EXERCISE_URL']}/collectionexercises/{collection_exercise_id}"

    response = requests.get(url, auth=app.config['BASIC_AUTH'])

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

    response = requests.get(url, auth=app.config['BASIC_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error('Failed to retrieve collection exercise events', collection_exercise_id=collection_exercise_id)
        raise ApiError(logger, response)

    logger.info('Successfully retrieved collection exercise events', collection_exercise_id=collection_exercise_id)
    return response.json()


def get_collection_exercises_for_survey(survey_id, collex_url, collex_auth, live_only=None):
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
            "date": date_time.strftime(date_format),
            "month": date_time.strftime('%m'),
            "is_in_future": date_time > parse_date(datetime.now().isoformat()),
            "formatted_date": custom_date('{S} %B %Y, %H:%M', date_time),
            "due_time": due_date(date_time)
        }
    return formatted_events


def suffix(d):
    return 'th' if 11 <= d <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th')


def custom_date(day, t):
    return t.strftime(day).replace('{S}', str(t.day) + suffix(t.day))


def due_date(date: datetime):
    now = datetime.now()
    event_day = datetime(date.year, date.month, date.day)
    today = return_date_time(now)
    tomorrow = return_date_time(now + timedelta(days=1))
    day_after = return_date_time(now + timedelta(days=2))
    a_month = return_date_time(now + timedelta(days=29))
    two_months = return_date_time(now + timedelta(days=60))
    three_months = return_date_time(now + timedelta(days=90))
    four_months = return_date_time(now + timedelta(days=120))
    if event_day == today:
        return 'Due today'
    if event_day == tomorrow:
        return 'Due tomorrow'
    if day_after <= event_day < a_month:
        delta = date.replace(tzinfo=None) - now.replace(tzinfo=None)
        return f'Due in {delta.days} days'
    if a_month <= event_day < two_months:
        return 'Due in a month'
    if two_months <= event_day < three_months:
        return 'Due in 2 months'
    if three_months <= event_day < four_months:
        return 'Due in 3 months'
    if four_months <= event_day:
        return 'Due in over 3 months'


def return_date_time(now: datetime):
    return datetime(now.year, now.month, now.day)


def number_of_day_diff(day):
    today = datetime.strptime(date_format, datetime.now())
    delta = today - day
    return delta.days
