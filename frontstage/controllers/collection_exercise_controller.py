import logging
from datetime import datetime, timedelta

import requests
from flask import current_app as app
from iso8601 import ParseError, parse_date
from structlog import wrap_logger

from frontstage.exceptions.exceptions import ApiError

logger = wrap_logger(logging.getLogger(__name__))

date_format = "%d %b %Y"


def get_collection_exercise(collection_exercise_id):
    logger.info("Attempting to retrieve collection exercise", collection_exercise_id=collection_exercise_id)
    url = f"{app.config['COLLECTION_EXERCISE_URL']}/collectionexercises/{collection_exercise_id}"

    response = requests.get(url, auth=app.config["BASIC_AUTH"])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error("Failed to retrieve collection exercise", collection_exercise_id=collection_exercise_id)
        raise ApiError(logger, response)

    logger.info("Successfully retrieved collection exercise", collection_exercise_id=collection_exercise_id)
    collection_exercise = response.json()

    if collection_exercise["events"]:
        collection_exercise["events"] = convert_events_to_new_format(collection_exercise["events"])

    return collection_exercise


def get_collection_exercise_events(collection_exercise_id):
    logger.info("Attempting to retrieve collection exercise events", collection_exercise_id=collection_exercise_id)
    url = f"{app.config['COLLECTION_EXERCISE_URL']}/collectionexercises/{collection_exercise_id}/events"

    response = requests.get(url, auth=app.config["BASIC_AUTH"])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error("Failed to retrieve collection exercise events", collection_exercise_id=collection_exercise_id)
        raise ApiError(logger, response)

    logger.info("Successfully retrieved collection exercise events", collection_exercise_id=collection_exercise_id)
    return response.json()


def get_collection_exercises_for_surveys(survey_ids, collex_url, collex_auth, live_only=None):
    logger.info("Retrieving collection exercises for surveys", survey_ids=survey_ids)
    params = {"surveyIds": survey_ids, "liveOnly": live_only}

    response = requests.get(f"{collex_url}/collectionexercises/surveys", params=params, auth=collex_auth)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error("Failed to retrieve collection exercises for surveys", survey_ids=survey_ids)
        raise ApiError(logger, response)

    if response.status_code == 204:
        logger.info("No live exercises found for surveys", survey_ids=survey_ids)
        return []
    logger.info("Successfully retrieved collection exercises", survey_ids=survey_ids)
    surveys_with_collection_exercises = response.json()

    print()
    print()
    print(surveys_with_collection_exercises)
    print()
    print()

    for collection_exercises in surveys_with_collection_exercises.values():
        for collection_exercise in collection_exercises:
            if collection_exercise["events"]:
                collection_exercise["events"] = convert_events_to_new_format(collection_exercise["events"])

    return surveys_with_collection_exercises


def get_live_collection_exercises_for_surveys(survey_ids, collex_url, collex_auth):
    return get_collection_exercises_for_surveys(survey_ids, collex_url, collex_auth, True)


def convert_events_to_new_format(events):
    formatted_events = {}
    for event in events:
        try:
            date_time = parse_date(event["timestamp"])
        except ParseError:
            raise ParseError

        formatted_events[event["tag"]] = {
            "date": date_time.strftime(date_format),
            "month": date_time.strftime("%m"),
            "is_in_future": date_time > parse_date(datetime.now().isoformat()),
            "formatted_date": ordinal_date_formatter("{S} %B %Y", date_time),
            "due_time": due_date_converter(date_time),
        }
    return formatted_events


def suffix(day: int):
    """
    This function creates the ordinal suffix

    :param: day of the date time object
    :return: ordinal suffix
    """
    return "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")


def ordinal_date_formatter(date_format_required: str, date_to_be_formatted: datetime):
    """
    This function takes the required output format and date to be formatted and returns the ordinal date in required
    format.

    :param: date_format_required: output format in which date should be returned
    :param: date_to_be_formatted: the datetime object which needs ordinal date
    :return: formatted date
    """
    return date_to_be_formatted.strftime(date_format_required).replace(
        "{S}", str(date_to_be_formatted.day) + suffix(date_to_be_formatted.day)
    )


def due_date_converter(date: datetime) -> str:
    """
    This function provides the custom due date based on the difference between now and the date passed.
    The logic for the due date is based on the following.
    Due date is today - Due today
    Due date is tomorrow - Due tomorrow
    Due date is 2-28 days - Due in X days
    Due date is 29-59 days - Due in a month
    Due date is 60-89 days - Due in 2 months
    Due date is 90-119 days - Due in 3 months
    Due date is 120+ days - Due in over 3 months

    :param: date: the datetime date for which due date is to be evaluated.
    :return: due date
    """
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
        return "Due today"
    if event_day == tomorrow:
        return "Due tomorrow"
    if day_after <= event_day < a_month:
        delta = date.replace(tzinfo=None) - now.replace(tzinfo=None)
        return f"Due in {delta.days} days"
    if a_month <= event_day < two_months:
        return "Due in a month"
    if two_months <= event_day < three_months:
        return "Due in 2 months"
    if three_months <= event_day < four_months:
        return "Due in 3 months"
    if four_months <= event_day:
        return "Due in over 3 months"


def return_date_time(timedelta_now: datetime) -> datetime:
    """
    This function is a part of the refactor code to return date  time in the following format
    :timedelta_now: datetime with delta
    :return:datetime
    """
    return datetime(timedelta_now.year, timedelta_now.month, timedelta_now.day)
