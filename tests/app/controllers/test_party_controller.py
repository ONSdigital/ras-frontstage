import unittest
from unittest.mock import patch

import responses

from config import TestingConfig
from frontstage import app
from frontstage.controllers import party_controller
from frontstage.controllers.party_controller import change_respondent_status
from frontstage.exceptions.exceptions import ApiError
from tests.app.mocked_services import (business_party, case, case_list, collection_exercise,
                                       collection_exercise_by_survey,
                                       collection_instrument_seft, respondent_party, survey, url_get_business_party,
                                       url_get_respondent_email, url_get_respondent_party, url_post_add_survey,
                                       url_reset_password_request, url_change_respondent_status)


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

    def test_reset_password_request_fail(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.POST, url_reset_password_request, status=500)
            with app.app_context():
                with self.assertRaises(ApiError):
                    party_controller.reset_password_request(respondent_party['emailAddress'])

    def test_change_respondent_status_success(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.PUT, url_change_respondent_status, status=200)
            with app.app_context():
                try:
                    change_respondent_status(respondent_party['id'], status='ACTIVE')
                except ApiError:
                    self.fail('Change respondent status fail to PUT your request')

    def test_change_respondent_status_fail(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.PUT, url_change_respondent_status, status=400)
            with app.app_context():
                with self.assertRaises(ApiError):
                    party_controller.change_respondent_status(respondent_party['id'], status='ACTIVE')

    @patch('frontstage.controllers.party_controller.get_respondent_party_by_id')
    def test_get_respondent_enrolments(self, get_respondent_party):
        get_respondent_party.return_value = respondent_party

        enrolments = party_controller.get_respondent_enrolments(respondent_party['id'])

        for enrolment in enrolments:
            self.assertTrue(enrolment['business_id'] is not None)
            self.assertTrue(enrolment['survey_id'] is not None)

    @patch('frontstage.controllers.party_controller.get_party_by_business_id')
    @patch('frontstage.controllers.survey_controller.get_survey')
    @patch('frontstage.controllers.case_controller.calculate_case_status')
    @patch('frontstage.controllers.collection_instrument_controller.get_collection_instrument')
    @patch('frontstage.controllers.case_controller.get_cases_for_list_type_by_party_id')
    @patch('frontstage.controllers.collection_exercise_controller.get_live_collection_exercises_for_survey')
    @patch('frontstage.controllers.party_controller.get_respondent_enrolments')
    def test_get_survey_list_details_for_party(self, get_respondent_enrolments, get_collection_exercises, get_cases,
                                               get_collection_instrument, calculate_case_status, get_survey, get_business):
        enrolments = [{
            'business_id': business_party['id'],
            'survey_id': survey['id']
        }]
        get_respondent_enrolments.return_value = enrolments
        get_collection_exercises.return_value = collection_exercise_by_survey
        get_cases.return_value = case_list
        get_collection_instrument.return_value = collection_instrument_seft
        calculate_case_status.return_value = 'In Progress'
        get_survey.return_value = survey
        get_business.return_value = business_party

        survey_list = party_controller.get_survey_list_details_for_party(respondent_party['id'], 'todo', business_party['id'], survey['id'])

        for survey_details in survey_list:
            self.assertTrue(survey_details['case_id'] is not None)
            self.assertTrue(survey_details['status'] is not None)
            self.assertTrue(survey_details['collection_instrument_type'] is not None)
            self.assertTrue(survey_details['survey_id'] is not None)
            self.assertTrue(survey_details['survey_long_name'] is not None)
            self.assertTrue(survey_details['survey_short_name'] is not None)
            self.assertTrue(survey_details['business_party_id'] is not None)
            self.assertTrue(survey_details['collection_exercise_ref'] is not None)
