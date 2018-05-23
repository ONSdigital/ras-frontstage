import logging
import time
import uuid

import iso8601
from flask import current_app
from structlog import wrap_logger

from frontstage.controllers import (collection_exercise_controller, collection_instrument_controller,
                                    party_controller, survey_controller)
from frontstage.exceptions.exceptions import InvalidEqPayLoad


logger = wrap_logger(logging.getLogger(__name__))


class EqPayload(object):

    def create_payload(self, case):
        """
        Creates the payload needed to communicate with EQ, built from the Case, Collection Exercise, Party,
        Survey and Collection Instrument services
        :case_id: The unique UUID references of a case
        :return Payload for EQ
        """

        tx_id = str(uuid.uuid4())
        logger.info('Creating payload for JWT', case_id=case['id'], tx_id=tx_id)

        # Collection Instrument
        ci_id = case['collectionInstrumentId']
        ci = collection_instrument_controller.get_collection_instrument(ci_id)
        if ci['type'] != 'EQ':
            raise InvalidEqPayLoad(f'Collection instrument {ci_id} type is not EQ')

        classifiers = ci['classifiers']
        if not classifiers or not classifiers.get('eq_id') or not classifiers.get('form_type'):
            raise InvalidEqPayLoad(f'Collection instrument {ci_id} classifiers are incorrect or missing')

        eq_id = ci['classifiers']['eq_id']
        form_type = ci['classifiers']['form_type']

        # Collection Exercise
        collex_id = case["caseGroup"]["collectionExerciseId"]
        collex = collection_exercise_controller.get_collection_exercise(collex_id)
        collex_event_dates = self._get_collex_event_dates(collex_id)

        # Party
        party_id = case['caseGroup']['partyId']
        party = party_controller.get_party_by_business_id(party_id, collection_exercise_id=collex_id)

        # Survey
        survey_id = collex['surveyId']
        survey = survey_controller.get_survey(survey_id)

        account_service_url = current_app.config['ACCOUNT_SERVICE_URL']
        iat = time.time()
        exp = time.time() + (5 * 60)

        return {
            'jti': str(uuid.uuid4()),
            'tx_id': tx_id,
            'user_id': case['partyId'],
            'iat': int(iat),
            'exp': int(exp),
            'eq_id': eq_id,
            'period_str': collex['userDescription'],
            'period_id': collex['exerciseRef'],
            'form_type': form_type,
            'collection_exercise_sid': collex['id'],
            'ref_p_start_date': collex_event_dates['ref_p_start_date'],
            'ref_p_end_date': collex_event_dates['ref_p_end_date'],
            'ru_ref': party['sampleUnitRef'] + party['checkletter'],
            'ru_name': party['name'],
            'return_by': collex_event_dates['return_by'],
            'survey_id': survey['surveyRef'],
            'case_id': case['id'],
            'case_ref': case['caseRef'],
            'account_service_url': account_service_url,
            'trad_as': f"{party['tradstyle1']} {party['tradstyle2']} {party['tradstyle3']}"
        }

    def _get_collex_event_dates(self, collex_id):
        """
        Maps the required collection exercise dates to a dic
        :param collex_id: The unique UUID references of a collection exercise
        :return A dict of event dates associate with the Exercise
        """

        collex_events = collection_exercise_controller.get_collection_exercise_events(collex_id)
        return {
             "ref_p_start_date": self._find_event_date_by_tag('ref_period_start', collex_events, collex_id),
             "ref_p_end_date": self._find_event_date_by_tag('exercise_end', collex_events, collex_id),
             "return_by": self._find_event_date_by_tag('return_by', collex_events, collex_id)
        }

    def _find_event_date_by_tag(self, search_param, collex_events, collex_id):
        """
        Finds the required date from the list of all the events
        :param search_param: the string name of the date searching for
        :param collex_events: All the Collection Exercise dates
        :return exercise
        """

        for event in collex_events:
            if event['tag'] == search_param and event.get('timestamp'):
                return self._format_string_long_date_time_to_short_date(event['timestamp'])
        raise InvalidEqPayLoad(f'Event not found for collection {collex_id} for search param {search_param}')

    @staticmethod
    def _format_string_long_date_time_to_short_date(string_date):
        """
        Formats the date from a string to %Y-%m-%d eg 2018-01-20
        :param string_date: The date string
        :return formatted date
        """

        try:
            return iso8601.parse_date(string_date).strftime('%Y-%m-%d')
        except (ValueError, iso8601.iso8601.ParseError):
            raise InvalidEqPayLoad(f'Unable to format {string_date}')
