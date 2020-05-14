import unittest

import responses

from config import TestingConfig
from frontstage import app
from frontstage.controllers import survey_controller
from frontstage.exceptions.exceptions import ApiError
from tests.integration.mocked_services import survey, url_get_survey, url_get_survey_by_short_name


class TestSurveyController(unittest.TestCase):

    def setUp(self):
        app_config = TestingConfig()
        app.config.from_object(app_config)
        self.app = app.test_client()
        self.app_config = self.app.application.config

    def test_get_survey_by_id_success(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_survey, json=survey, status=200, content_type='application/json')
            with app.app_context():
                get_survey = survey_controller.get_survey(self.app_config['SURVEY_URL'], self.app_config['BASIC_AUTH'],
                                                          survey['id'])

                self.assertIn('Bricks', get_survey['shortName'], 'Bricks short name is not in the returned survey')

    def test_get_survey_by_id_fail(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_survey, status=400)
            with app.app_context():
                with self.assertRaises(ApiError):
                    survey_controller.get_survey(self.app_config['SURVEY_URL'], self.app_config['BASIC_AUTH'],
                                                 survey['id'])

    def test_get_survey_by_short_name_success(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_survey_by_short_name, json=survey, status=200, content_type='application/json')
            with app.app_context():
                get_survey = survey_controller.get_survey_by_short_name(survey['shortName'])

                self.assertIn("Bricks", get_survey['shortName'])

    def test_get_survey_by_short_name_fail(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_survey_by_short_name, status=400)
            with app.app_context():
                with self.assertRaises(ApiError):
                    survey_controller.get_survey_by_short_name(survey['shortName'])
