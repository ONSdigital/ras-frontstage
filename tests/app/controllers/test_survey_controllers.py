import json
import unittest

import responses

from config import TestingConfig
from frontstage import app
from frontstage.controllers import survey_controller
from frontstage.exceptions.exceptions import ApiError

with open('tests/test_data/survey/bricks_survey.json') as fp:
    survey = json.load(fp)

url_survey_by_id = f'{app.config["SURVEY_URL"]}/surveys/{survey["id"]}'
url_survey_by_shortname = f'{app.config["SURVEY_URL"]}/surveys/shortname/{survey["shortName"]}'


class TestSurveyController(unittest.TestCase):

    def setUp(self):
        app_config = TestingConfig()
        app.config.from_object(app_config)
        self.app = app.test_client()

    def test_get_survey_by_id_success(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_survey_by_id, json=survey, status=200, content_type='application/json')
            with app.app_context():
                get_survey = survey_controller.get_survey(survey['id'])

                self.assertIn('Bricks', get_survey['shortName'], 'Bricks short name is not in the returned survey')

    def test_get_survey_by_id_fail(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_survey_by_id, status=400)
            with app.app_context():
                with self.assertRaises(ApiError):
                        survey_controller.get_survey(survey['id'])

    def test_get_survey_by_short_name_success(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_survey_by_shortname, json=survey, status=200, content_type='application/json')
            with app.app_context():
                get_survey = survey_controller.get_survey_by_short_name(survey['shortName'])

                self.assertIn("Bricks", get_survey['shortName'])

    def test_get_survey_by_short_name_fail(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_survey_by_shortname, status=400)
            with app.app_context():
                with self.assertRaises(ApiError):
                    survey_controller.get_survey_by_short_name(survey['shortName'])
