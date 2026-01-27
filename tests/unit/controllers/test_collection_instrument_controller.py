import io
import json
import unittest
from unittest.mock import patch

import responses
from werkzeug.datastructures import FileStorage

from config import TestingConfig
from frontstage import app
from frontstage.controllers.collection_instrument_controller import (
    MISSING_FILE_ERROR,
    download_collection_instrument,
    get_collection_instrument,
    upload_collection_instrument,
)
from frontstage.controllers.gcp_survey_response import SurveyResponseError
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
        self.survey_file_size = 50000

    @patch("frontstage.controllers.case_controller.post_case_event")
    def test_download_collection_instrument_success(self, _):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_download_ci, json=collection_instrument_seft, status=200)
            with app.app_context():
                downloaded_ci = json.loads(
                    download_collection_instrument(collection_instrument_seft["id"], case["id"], business_party["id"])[
                        0
                    ]
                )

                self.assertEqual(downloaded_ci["id"], collection_instrument_seft["id"])

    @patch("frontstage.controllers.case_controller.post_case_event")
    def test_download_collection_instrument_access_control_header_set(self, _):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_download_ci, json=collection_instrument_seft, status=200)
            with app.app_context():
                _, headers = download_collection_instrument(
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
                    download_collection_instrument(collection_instrument_seft["id"], case["id"], business_party["id"])

    def test_collection_instrument_success(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_ci, json=collection_instrument_seft, status=200)
            with app.app_context():
                returned_ci = get_collection_instrument(
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
                    get_collection_instrument(
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
                    upload_collection_instrument(
                        self.survey_file, self.survey_file_size, case, business_party, party["id"], survey
                    )
                except (ApiError, CiUploadError):
                    self.fail("Unexpected error thrown when uploading collection instrument")

    @patch("frontstage.controllers.case_controller.post_case_event")
    def test_upload_collection_instrument_success_1(self, *_):
        validation_errors = upload_collection_instrument(
            None, self.survey_file_size, case, business_party, party["id"], survey
        )
        self.assertEqual(validation_errors, [MISSING_FILE_ERROR])

    @patch("frontstage.controllers.case_controller.post_case_event")
    @patch("frontstage.controllers.gcp_survey_response.GcpSurveyResponse.validate_file")
    def test_upload_collection_instrument_validation_error(self, validate_file, _):
        validate_file.return_value = ["error"]
        with app.app_context():
            validation_errors = upload_collection_instrument(
                self.survey_file, self.survey_file_size, case, business_party, party["id"], survey
            )
        self.assertEqual(validation_errors, ["error"])

    @patch("frontstage.controllers.case_controller.post_case_event")
    @patch("frontstage.controllers.gcp_survey_response.GcpSurveyResponse.create_file_name_for_upload")
    def test_upload_collection_instrument_create_file_name_error(self, create_file_name_for_upload, _):
        create_file_name_for_upload.return_value = None
        with app.app_context():
            with self.assertRaises(CiUploadError):
                upload_collection_instrument(
                    self.survey_file, self.survey_file_size, case, business_party, party["id"], survey
                )

    @patch("frontstage.controllers.case_controller.post_case_event")
    @patch("frontstage.controllers.gcp_survey_response.GcpSurveyResponse.create_file_name_for_upload")
    @patch("frontstage.controllers.gcp_survey_response.GcpSurveyResponse.upload_seft_survey_response")
    def test_upload_collection_survey_response_error(self, upload_seft_survey_response, *_):
        upload_seft_survey_response.side_effect = SurveyResponseError()
        with app.app_context():
            with self.assertRaises(CiUploadError):
                upload_collection_instrument(
                    self.survey_file, self.survey_file_size, case, business_party, party["id"], survey
                )
