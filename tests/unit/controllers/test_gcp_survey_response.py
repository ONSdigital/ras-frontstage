import json
from unittest import TestCase
from unittest.mock import MagicMock

import responses

from config import TestingConfig
from frontstage import app
from frontstage.controllers.gcp_survey_response import (
    FILE_EXTENSION_ERROR,
    FILE_NAME_LENGTH_ERROR,
    MAX_FILE_SIZE_ERROR,
    MIN_FILE_SIZE_ERROR,
    GcpSurveyResponse,
    SurveyResponseError,
)
from frontstage.exceptions.exceptions import ApiError
from tests.integration.mocked_services import (
    business_party,
    case,
    case_without_case_group,
    collection_exercise,
    survey,
    url_get_collection_exercise,
)


class TestGcpSurveyResponse(TestCase):
    """Survey response unit tests"""

    file_name = "file_name"
    tx_id = "abb3edd9-21d7-4389-886a-587e4c186a99"
    survey_ref = "066"
    exercise_ref = "25907972-535f-467f-92de-e9fe88fbdd20"
    ru = "11110000001"

    bucket_content = {
        "filename": file_name,
        "file": "file_as_string",
        "case_id": "87daf1b0-c1ae-437e-bddf-dc893eb1059a",
        "survey_id": survey_ref,
    }

    pubsub_payload = {
        "filename": file_name,
        "tx_id": tx_id,
        "survey_id": survey_ref,
        "period": exercise_ref,
        "ru_ref": ru,
        "md5sum": "md5hash",
        "sizeBytes": "1234",
    }

    config = {
        "SEFT_UPLOAD_BUCKET_NAME": "test-bucket",
        "SEFT_UPLOAD_PROJECT": "test-project",
        "SEFT_UPLOAD_PUBSUB_TOPIC": "test-topic",
    }

    url_get_case_by_id = f"{app.config['CASE_URL']}/cases/{bucket_content['case_id']}"

    def setUp(self):
        app_config = TestingConfig()
        app.config.from_object(app_config)
        self.app = app.test_client()
        self.app_config = self.app.application.config

    @responses.activate
    def test_failed_api_call_raises_http_exception(self):
        responses.add(responses.GET, url_get_collection_exercise, status=500)
        with app.app_context():
            survey_response = GcpSurveyResponse(self.config)
            with self.assertRaises(ApiError):
                survey_response.create_pubsub_payload(
                    case,
                    self.pubsub_payload["md5sum"],
                    self.bucket_content,
                    "filename",
                    self.tx_id,
                )

    def test_missing_data_raises_survey_response_error(self):
        with app.app_context():
            survey_response = GcpSurveyResponse(self.config)
            with self.assertRaises(SurveyResponseError) as e:
                survey_response.create_pubsub_payload(
                    case_without_case_group,
                    self.pubsub_payload["md5sum"],
                    self.bucket_content,
                    "filename",
                    self.tx_id,
                )

            self.assertEqual(e.exception.args[0], "Case group not found")

    def test_missing_filename_raises_key_error(self):
        survey_response = GcpSurveyResponse(self.config)
        test_file_contents = "test file contents"
        survey_response.storage_client = MagicMock()
        filename = ""
        with app.app_context():
            with self.assertRaises(ValueError):
                survey_response.put_file_into_gcp_bucket(test_file_contents, filename)

    def test_successful_send_to_pub_sub(self):
        with app.app_context():
            publisher = MagicMock()
            publisher.topic_path.return_value = "projects/test-project/topics/test-topic"
            survey_response = GcpSurveyResponse(self.config)
            survey_response.publisher = publisher
            result = survey_response.put_message_into_pubsub(self.pubsub_payload, self.tx_id)
            data = json.dumps(self.pubsub_payload).encode()

            publisher.publish.assert_called()
            publisher.publish.assert_called_with("projects/test-project/topics/test-topic", data=data, tx_id=self.tx_id)
            self.assertIsNone(result)

    @responses.activate
    def test_create_file_name_success(self):
        responses.add(responses.GET, url_get_collection_exercise, json=collection_exercise, status=200)
        expected_ru_with_checkletter = "49900000001F"
        expected_exercise_ref = "204901"
        expected_survey_ref = "074"
        expected_file_extension = "xlsx"
        with app.app_context():
            survey_response = GcpSurveyResponse(self.config)
            output = survey_response.create_file_name_for_upload(case, business_party, ".xlsx", survey["surveyRef"])

            # Output looks like '49900000001F_204901_074_20220223125323.xlsx' but because of the timestamp always
            # changing, we'll test each bit
            split_filename = output.split("_")
            split_on_dot = split_filename[3].split(".")
            self.assertEqual(split_filename[0], expected_ru_with_checkletter)
            self.assertEqual(split_filename[1], expected_exercise_ref)
            self.assertEqual(split_filename[2], expected_survey_ref)

            # Tests the timestamp format instead of the value as it is always changing
            self.assertTrue(split_on_dot[0].isdigit())
            self.assertTrue(len(split_on_dot[0]), 14)
            self.assertEqual(split_on_dot[1], expected_file_extension)

    def test_validate_file(self):
        with app.app_context():
            survey_response = GcpSurveyResponse(self.config)
            validation_errors = survey_response.validate_file("valid_file_name", "xls", 50000)
        self.assertEqual(validation_errors, [])

    def test_validate_file_extension_error(self):
        with app.app_context():
            survey_response = GcpSurveyResponse(self.config)
            validation_errors = survey_response.validate_file("valid_file_name", "txt", 50000)
        self.assertEqual(validation_errors, [FILE_EXTENSION_ERROR])

    def test_validate_file_name_length_error(self):
        with app.app_context():
            app.config["MAX_UPLOAD_FILE_NAME_LENGTH"] = 1
            survey_response = GcpSurveyResponse(self.config)
            validation_errors = survey_response.validate_file("invalid_length", "xls", 50000)
        self.assertEqual(validation_errors, [FILE_NAME_LENGTH_ERROR])

    def test_validate_file_max_file_size_error(self):
        with app.app_context():
            survey_response = GcpSurveyResponse(self.config)
            validation_errors = survey_response.validate_file(
                "valid_file_name", "xls", app.config["MAX_UPLOAD_LENGTH"] + 1
            )
        self.assertEqual(validation_errors, [MAX_FILE_SIZE_ERROR])

    def test_validate_file_min_file_size_error(self):
        with app.app_context():
            survey_response = GcpSurveyResponse(self.config)
            validation_errors = survey_response.validate_file(
                "valid_file_name", "xls", app.config["MIN_UPLOAD_LENGTH"] - 1
            )
        self.assertEqual(validation_errors, [MIN_FILE_SIZE_ERROR])

    def test_validate_file_multiple(self):
        with app.app_context():
            survey_response = GcpSurveyResponse(self.config)
            validation_errors = survey_response.validate_file(
                "valid_file_name", "txt", app.config["MAX_UPLOAD_LENGTH"] + 1
            )
        self.assertEqual(validation_errors, [FILE_EXTENSION_ERROR, MAX_FILE_SIZE_ERROR])
