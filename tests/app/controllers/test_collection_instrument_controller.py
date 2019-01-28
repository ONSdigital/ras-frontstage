import io
import json
import unittest
from unittest.mock import patch

import responses

from config import TestingConfig
from frontstage import app
from frontstage.controllers import collection_instrument_controller
from frontstage.exceptions.exceptions import ApiError, CiUploadError
from tests.app.mocked_services import (case, collection_instrument_seft, business_party,
                                       url_download_ci, url_get_ci, url_upload_ci)


class TestCollectionInstrumentController(unittest.TestCase):

    def setUp(self):
        app_config = TestingConfig()
        app.config.from_object(app_config)
        self.app = app.test_client()
        self.app_config = self.app.application.config
        self.survey_file = dict(file=(io.BytesIO(b'my file contents'), "testfile.xlsx"))

    @patch('frontstage.controllers.case_controller.post_case_event')
    def test_download_collection_instrument_success(self, _):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_download_ci, json=collection_instrument_seft, status=200)
            with app.app_context():
                downloaded_ci = json.loads(collection_instrument_controller.download_collection_instrument(collection_instrument_seft['id'],
                                                                                                           case['id'], business_party['id'])[0])

                self.assertEqual(downloaded_ci['id'], collection_instrument_seft['id'])

    @patch('frontstage.controllers.case_controller.post_case_event')
    def test_download_collection_instrument_fail(self, _):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_download_ci, status=400)
            with app.app_context():
                with self.assertRaises(ApiError):
                    collection_instrument_controller.download_collection_instrument(collection_instrument_seft['id'], case['id'],
                                                                                    business_party['id'])

    def test_collection_instrument_success(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_ci, json=collection_instrument_seft, status=200)
            with app.app_context():
                returned_ci = collection_instrument_controller.\
                    get_collection_instrument(self.app_config['COLLECTION_INSTRUMENT_URL'],
                                              self.app_config['COLLECTION_INSTRUMENT_AUTH'],
                                              collection_instrument_seft['id'])

                self.assertEqual(collection_instrument_seft['id'], returned_ci['id'])

    def test_collection_instrument_fail(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_ci, status=400)
            with app.app_context():
                with self.assertRaises(ApiError):
                    collection_instrument_controller.get_collection_instrument(self.app_config[
                                                                                   'COLLECTION_INSTRUMENT_URL'],
                                                                               self.app_config[
                                                                                   'COLLECTION_INSTRUMENT_AUTH'],
                                                                               collection_instrument_seft['id'])

    @patch('frontstage.controllers.case_controller.post_case_event')
    def test_upload_collection_instrument_success(self, _):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.POST, url_upload_ci, status=200)
            with app.app_context():
                try:
                    collection_instrument_controller.upload_collection_instrument(self.survey_file, case['id'],
                                                                                  business_party['id'])
                except (ApiError, CiUploadError):
                    self.fail("Unexpected error thrown when uploading collection instrument")

    @patch('frontstage.controllers.case_controller.post_case_event')
    def test_upload_collection_instrument_ci_upload_error(self, _):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.POST, url_upload_ci, status=400)
            with app.app_context():
                with self.assertRaises(CiUploadError):
                    collection_instrument_controller.upload_collection_instrument(self.survey_file, case['id'], business_party['id'])

    @patch('frontstage.controllers.case_controller.post_case_event')
    def test_upload_collection_instrument_api_error(self, _):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.POST, url_upload_ci, status=500)
            with app.app_context():
                with self.assertRaises(ApiError):
                    collection_instrument_controller.upload_collection_instrument(self.survey_file, case['id'], business_party['id'])
