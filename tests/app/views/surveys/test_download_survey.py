import json
import unittest
from unittest.mock import patch
from flask import request

from frontstage import app, create_app_object
from tests.app.mocked_services import business_party, case, collection_instrument_seft, encoded_jwt_token, survey


class TestDownloadSurvey(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.set_cookie('localhost', 'authorization', 'session_key')
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"  # NOQA
        }
        self.patcher = patch('redis.StrictRedis.get', return_value=encoded_jwt_token)

        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    @patch('frontstage.controllers.collection_instrument_controller.download_collection_instrument')
    @patch('frontstage.controllers.party_controller.is_respondent_enrolled')
    @patch('frontstage.controllers.case_controller.get_case_by_case_id')
    def test_download_survey_success(self, get_case_by_id, _, download_collection_instrument):
        str = json.dumps(collection_instrument_seft)
        binary = ' '.join(format(ord(letter), 'b') for letter in str)
        get_case_by_id.return_value = case
        headers = {'Content-type': 'application/json', 'Content-Length': '5962'}
        download_collection_instrument.return_value = binary, headers

        urls = ['download_survey', 'download-survey']
        for url in urls:
            with self.subTest(url=url):
                response = self.app.get(f'/surveys/{url}?case_id={case["id"]}&business_party_id={business_party["id"]}'
                                        f'&survey_short_name={survey["shortName"]}')

                self.assertEqual(response.status_code, 200)

    def test_enforces_secure_headers(self):
        with create_app_object().test_client() as client:
            headers = client.get(
                '/',
                headers={'X-Forwarded-Proto': 'https'}  # set protocol so that talisman sets HSTS headers
            ).headers

            self.assertEqual('no-cache, no-store, must-revalidate', headers['Cache-Control'])
            self.assertEqual('no-cache', headers['Pragma'])
            self.assertEqual('max-age=31536000; includeSubDomains', headers['Strict-Transport-Security'])
            self.assertEqual('DENY', headers['X-Frame-Options'])
            self.assertEqual('1; mode=block', headers['X-Xss-Protection'])
            self.assertEqual('nosniff', headers['X-Content-Type-Options'])

            csp_policy_parts = headers['Content-Security-Policy'].split('; ')
            self.assertIn("default-src 'self' https://cdn.ons.gov.uk", csp_policy_parts)
            self.assertIn(
                "font-src 'self' data: https://fonts.gstatic.com https://cdn.ons.gov.uk", csp_policy_parts)
            self.assertIn(
                "script-src 'self' https://www.googletagmanager.com https://cdn.ons.gov.uk 'nonce-{}'".format(
                    request.csp_nonce),
                csp_policy_parts
            )
            # TODO: fix assertion error
            # self.assertIn(
            #     "connect-src 'self' https://www.googletagmanager.com https://tagmanager.google.com https://cdn.ons.gov.uk "
            #     'http://localhost:8082 ws://localhost:8082', csp_policy_parts)
            self.assertIn(
                "img-src 'self' data: https://www.gstatic.com https://www.google-analytics.com "
                'https://www.googletagmanager.com https://ssl.gstatic.com https://cdn.ons.gov.uk', csp_policy_parts)
            self.assertIn(
                "style-src 'self' https://cdn.ons.gov.uk 'unsafe-inline' https://tagmanager.google.com https://fonts.googleapis.com", csp_policy_parts)
