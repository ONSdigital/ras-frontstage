import unittest
from unittest.mock import patch

import responses

from config import TestingConfig
from frontstage import app
from frontstage.controllers import party_controller
from frontstage.exceptions.exceptions import ApiError
from tests.app.mocked_services import (business_party, case, case_list, collection_exercise, collection_exercise_by_survey,
                                       collection_instrument_seft, respondent_party, survey, url_get_business_party, url_get_respondent_email,
                                       url_get_respondent_party, url_post_add_survey)
from frontstage.common.mappers import convert_events_to_new_format


registration_data = {
                'emailAddress': respondent_party['emailAddress'],
                'firstName': respondent_party['firstName'],
                'lastName': respondent_party['lastName'],
                'password': 'apples',
                'telephone': respondent_party['telephone'],
                'enrolmentCode': case['iac'],
                'status': 'CREATED'
            }


class TestPartyController(unittest.TestCase):

    def setUp(self):
        app_config = TestingConfig()
        app.config.from_object(app_config)
        self.app = app.test_client()

    def test_get_respondent_by_party_id_success(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_respondent_party, json=respondent_party, status=200)

            with app.app_context():
                party = party_controller.get_respondent_party_by_id(respondent_party['id'])

                self.assertEqual(party['id'], respondent_party['id'])
                self.assertEqual(party['emailAddress'], respondent_party['emailAddress'])

    def test_get_respondent_by_party_id_fail(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_respondent_party, status=500)
            with app.app_context():
                with self.assertRaises(ApiError):
                    party_controller.get_respondent_party_by_id(respondent_party['id'])

    def test_get_respondent_by_party_id_not_found(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_respondent_party, status=404)
            with app.app_context():
                party = party_controller.get_respondent_party_by_id(respondent_party['id'])

                self.assertTrue(party is None)

    def test_add_survey_success(self):
        with responses.RequestsMock() as rsps:
            request_json = {
                "party_id": respondent_party['id'],
                "enrolment_code": case['iac']
            }

            rsps.add(rsps.POST, url_post_add_survey, json=request_json, status=200)
            with app.app_context():
                try:
                    party_controller.add_survey(respondent_party['id'], case['iac'])
                except ApiError:
                    self.fail("Unexpected ApiError when adding a survey")

    def test_add_survey_fail(self):
        with responses.RequestsMock() as rsps:
            request_json = {
                "party_id": respondent_party['id'],
                "enrolment_code": case['iac']
            }

            rsps.add(rsps.POST, url_post_add_survey, json=request_json, status=400)
            with app.app_context():
                with self.assertRaises(ApiError):
                    party_controller.add_survey(respondent_party['id'], case['iac'])

    def test_get_party_by_business_id_success_without_collection_exercise_id(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_business_party, json=business_party, status=200)
            with app.app_context():
                business = party_controller.get_party_by_business_id(business_party['id'])

                self.assertEqual(business['id'], business_party['id'])
                self.assertEqual(business['name'], business_party['name'])

    def test_get_party_by_business_id_success_with_collection_exercise_id(self):
        with responses.RequestsMock() as rsps:
            url = f"{url_get_business_party}?collection_exercise_id={collection_exercise['id']}"
            rsps.add(rsps.GET, url, json=business_party, status=200)
            with app.app_context():
                business = party_controller.get_party_by_business_id(business_party['id'], collection_exercise['id'])

                self.assertEqual(business['id'], business_party['id'])
                self.assertEqual(business['name'], business_party['name'])

    def test_get_party_by_business_id_fail(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_business_party, status=400)
            with app.app_context():
                with self.assertRaises(ApiError):
                    party_controller.get_party_by_business_id(business_party['id'])

    def test_get_respondent_by_email_success(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_respondent_email, json=respondent_party, status=200)
            with app.app_context():
                respondent = party_controller.get_respondent_by_email(respondent_party['emailAddress'])

                self.assertEqual(respondent['emailAddress'], respondent_party['emailAddress'])
                self.assertEqual(respondent['firstName'], respondent_party['firstName'])

    def test_get_respondent_by_email_not_found(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_respondent_email, status=404)
            with app.app_context():
                respondent = party_controller.get_respondent_by_email(respondent_party['emailAddress'])

                self.assertTrue(respondent is None)

    def test_get_respondent_by_email_fail(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_respondent_email, status=500)
            with app.app_context():
                with self.assertRaises(ApiError):
                    party_controller.get_respondent_by_email(respondent_party['emailAddress'])

    @patch('frontstage.controllers.case_controller.calculate_case_status')
    @patch('frontstage.controllers.collection_instrument_controller.get_collection_instrument')
    @patch('frontstage.controllers.collection_exercise_controller.get_collection_exercises_for_survey')
    @patch('frontstage.controllers.survey_controller.get_survey')
    @patch('frontstage.controllers.case_controller.get_cases_for_list_type_by_party_id')
    @patch('frontstage.controllers.party_controller.get_party_by_business_id')
    @patch('frontstage.controllers.party_controller.get_respondent_party_by_id')
    def test_get_party_enabled_enrolments_details_with_associations(self, get_respondent_by_party_id,
                                                                    get_business_by_party_id,
                                                                    get_case_list, get_survey_by_id,
                                                                    get_ce_for_survey, get_collection_instrument,
                                                                    calculate_case_status):

        for exercise in collection_exercise_by_survey:
            exercise['events'] = convert_events_to_new_format(exercise['events'])
        get_respondent_by_party_id.return_value = respondent_party
        get_business_by_party_id.return_value = business_party
        get_case_list.return_value = case_list
        get_survey_by_id.return_value = survey
        get_ce_for_survey.return_value = collection_exercise_by_survey
        get_collection_instrument.return_value = collection_instrument_seft
        calculate_case_status.return_value = 'Not Started'
        with app.app_context():
            survey_list = party_controller.get_party_enabled_enrolments_details(respondent_party['id'], 'todo')

            self.assertTrue(survey_list is not None)
            for survey_entry in survey_list:
                self.assertEqual(survey_entry['status'], 'Not Started')
