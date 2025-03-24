import io
import json
import unittest
from unittest.mock import patch

import responses
from werkzeug.datastructures import FileStorage

from config import TestingConfig
from frontstage import app
from frontstage.controllers import collection_instrument_controller
from frontstage.exceptions.exceptions import ApiError, CiUploadError
from tests.integration.mocked_services import (
    business_party,
    case,
    collection_exercise,
    collection_instrument_seft,
    party,
    survey,
    url_download_ci,
    url_get_ci,
    url_get_collection_exercise,
)


class TestCollectionInstrumentController(unittest.TestCase):
    def setUp(self):
        app_config = TestingConfig()
        app.config.from_object(app_config)
        self.app = app.test_client()
        self.app_config = self.app.application.config
        self.survey_file = FileStorage(io.BytesIO(b"my file contents"), "testfile.xlsx")

    @patch("frontstage.controllers.case_controller.post_case_event")
    def test_download_collection_instrument_success(self, _):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_download_ci, json=collection_instrument_seft, status=200)
            with app.app_context():
                downloaded_ci = json.loads(
                    collection_instrument_controller.download_collection_instrument(
                        collection_instrument_seft["id"], case["id"], business_party["id"]
                    )[0]
                )

                self.assertEqual(downloaded_ci["id"], collection_instrument_seft["id"])

    @patch("frontstage.controllers.case_controller.post_case_event")
    def test_download_collection_instrument_access_control_header_set(self, _):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_download_ci, json=collection_instrument_seft, status=200)
            with app.app_context():
                _, headers = collection_instrument_controller.download_collection_instrument(
                    collection_instrument_seft["id"], case["id"], business_party["id"]
                )

                acao = dict(headers)["Access-Control-Allow-Origin"]
                self.assertEqual("http://localhost", acao)

    @patch("frontstage.controllers.case_controller.post_case_event")
    def test_download_collection_instrument_fail(self, _):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_download_ci, status=400)
            with app.app_context():
                with self.assertRaises(ApiError):
                    collection_instrument_controller.download_collection_instrument(
                        collection_instrument_seft["id"], case["id"], business_party["id"]
                    )

    def test_collection_instrument_success(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_ci, json=collection_instrument_seft, status=200)
            with app.app_context():
                returned_ci = collection_instrument_controller.get_collection_instrument(
                    collection_instrument_seft["id"],
                    self.app_config["COLLECTION_INSTRUMENT_URL"],
                    self.app_config["BASIC_AUTH"],
                )

                self.assertEqual(collection_instrument_seft["id"], returned_ci["id"])

    def test_collection_instrument_fail(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_ci, status=400)
            with app.app_context():
                with self.assertRaises(ApiError):
                    collection_instrument_controller.get_collection_instrument(
                        collection_instrument_seft["id"],
                        self.app_config["COLLECTION_INSTRUMENT_URL"],
                        self.app_config["BASIC_AUTH"],
                    )

    @patch("frontstage.controllers.case_controller.post_case_event")
    @patch("frontstage.controllers.gcp_survey_response.GcpSurveyResponse.upload_seft_survey_response")
    def test_upload_collection_instrument_success(self, *_):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_collection_exercise, json=collection_exercise, status=200)

            with app.app_context():
                try:
                    collection_instrument_controller.upload_collection_instrument(
                        self.survey_file, case, business_party, party["id"], survey
                    )
                except (ApiError, CiUploadError):
                    self.fail("Unexpected error thrown when uploading collection instrument")

    @patch("frontstage.controllers.case_controller.post_case_event")
    def test_upload_collection_instrument_ci_missing_filename(self, _):
        file = FileStorage(io.BytesIO(b"my file contents"))
        with app.app_context():
            error_message = collection_instrument_controller.upload_collection_instrument(
                file, case, business_party, party["id"], survey
            )
            self.assertEqual(error_message, "The upload must have valid case_id and a file attached")

    @patch("frontstage.controllers.case_controller.post_case_event")
    def test_upload_collection_instrument_missing_business_party(self, _):
        FileStorage(filename="testfile.xlsx")
        with app.app_context():
            with self.assertRaises(CiUploadError) as e:
                collection_instrument_controller.upload_collection_instrument(
                    self.survey_file, case, None, party["id"], survey
                )
        self.assertEqual(e.exception.error_message, "Data needed to create the file name is missing")
