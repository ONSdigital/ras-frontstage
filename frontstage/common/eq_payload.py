import logging
import time
import uuid

import iso8601
from flask import current_app
from structlog import wrap_logger

from frontstage.controllers import (
    collection_exercise_controller,
    collection_instrument_controller,
    party_controller,
)
from frontstage.exceptions.exceptions import InvalidEqPayLoad

logger = wrap_logger(logging.getLogger(__name__))


class EqPayload(object):
    def create_payload(self, case, ce, party_id: str, business_party_id: str, survey) -> dict:
        """
        Creates the payload needed to communicate with EQ, built from the Case, Collection Exercise, Party,
        Survey and Collection Instrument services
        :param case: A dict containing information about the case
        :param ce: A dict containing information about the collection exercise
        :param party_id: The uuid of the respondent
        :param business_party_id: The uuid of the reporting unit
        :param survey: A dict containing information about the survey
        :returns: Payload for EQ
        """
        tx_id = str(uuid.uuid4())
        logger.info("Creating payload for JWT", case_id=case["id"], tx_id=tx_id)

        ci_id = case["collectionInstrumentId"]
        ci = collection_instrument_controller.get_collection_instrument(
            ci_id, current_app.config["COLLECTION_INSTRUMENT_URL"], current_app.config["BASIC_AUTH"]
        )
        if ci["type"] != "EQ":
            raise InvalidEqPayLoad(f"Collection instrument {ci_id} type is not EQ")

        classifiers = ci["classifiers"]
        if not classifiers or not classifiers.get("eq_id") or not classifiers.get("form_type"):
            raise InvalidEqPayLoad(f"Collection instrument {ci_id} classifiers are incorrect or missing")

        eq_id = ci["classifiers"]["eq_id"]
        form_type = ci["classifiers"]["form_type"]
        ce_id = ce["id"]
        party = party_controller.get_party_by_business_id(
            business_party_id,
            current_app.config["PARTY_URL"],
            current_app.config["BASIC_AUTH"],
            collection_exercise_id=ce_id,
        )
        ce_events = collection_exercise_controller.get_collection_exercise_events(ce_id)
        ru_ref = f"{party['sampleUnitRef'] + party['checkletter']}"
        int_time = int(time.time())

        payload = {
            "exp": int_time + 300,
            "iat": int_time,
            "jti": str(uuid.uuid4()),
            "tx_id": tx_id,
            "version": "v2",
            "account_service_url": current_app.config["ACCOUNT_SERVICE_URL"],
            "case_id": case["id"],
            "collection_exercise_sid": ce_id,
            "response_id": f"{ru_ref}{ce_id}{eq_id}{form_type}",
            "response_expires_at": self._find_event_date_by_tag("exercise_end", ce_events, ce_id),
            "schema_name": f"{eq_id}_{form_type}",
            "survey_metadata": {
                "data": {
                    "case_ref": case["caseRef"],
                    "form_type": form_type,
                    "period_id": ce["exerciseRef"],
                    "period_str": ce["userDescription"],
                    "ref_p_end_date": self._find_event_date_by_tag("ref_period_end", ce_events, ce_id),
                    "ref_p_start_date": self._find_event_date_by_tag("ref_period_start", ce_events, ce_id),
                    "ru_name": party["name"],
                    "ru_ref": ru_ref,
                    "trad_as": f"{party['tradstyle1']} {party['tradstyle2']} {party['tradstyle3']}",
                    "user_id": party_id,
                    "survey_id": survey["surveyRef"],
                }
            },
        }

        if employment_date := self._find_event_date_by_tag("employment", ce_events, ce_id, False):
            payload["survey_metadata"]["data"]["employment_date"] = employment_date

        return payload

    def _find_event_date_by_tag(self, search_param, collex_events, collex_id, mandatory=True):
        """
        Finds the required date from the list of all the events
        :param search_param: the string name of the date searching for
        :param collex_events: All the Collection Exercise dates
        :param mandatory: Specifies if the event date being searched for is mandatory
        :return exercise
        :raises InvalidEqPayLoad if a mandatory event tag is not found in the collectionexercise events
        """

        for event in collex_events:
            if event["tag"] == search_param and event.get("timestamp"):
                # Adding this as iso full timestamp is required only for response_expires_at
                if search_param != "exercise_end":
                    return self._format_string_long_date_time_to_short_date(event["timestamp"])
                else:
                    return self._format_string_long_date_time_to_iso_format(event["timestamp"])

        if mandatory:
            raise InvalidEqPayLoad(
                f"Mandatory event not found for collection {collex_id} for search param {search_param}"
            )

    @staticmethod
    def _format_string_long_date_time_to_short_date(string_date):
        """
        Formats the date from a string to %Y-%m-%d eg 2018-01-20
        :param string_date: The date string
        :return formatted date
        """

        try:
            return iso8601.parse_date(string_date).astimezone().strftime("%Y-%m-%d")
        except (ValueError, iso8601.iso8601.ParseError):
            raise InvalidEqPayLoad(f"Unable to format {string_date}")

    @staticmethod
    def _format_string_long_date_time_to_iso_format(string_date):
        """
        Formats the date from a string to iso format
        :param string_date: The date string
        :return formatted date
        """

        try:
            return iso8601.parse_date(string_date).astimezone().isoformat()
        except (ValueError, iso8601.iso8601.ParseError):
            raise InvalidEqPayLoad(f"Unable to format {string_date}")
