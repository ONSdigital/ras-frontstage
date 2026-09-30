import io
import logging
import unittest
from unittest.mock import patch

import requests_mock
from structlog import wrap_logger

from frontstage import app
from frontstage.exceptions.exceptions import CiUploadError
from tests.integration.mocked_services import (
    business_party,
    case,
    collection_exercise,
    encoded_jwt_token,
    respondent_party,
    survey,
    survey_eq,
    url_banner_api,
    url_get_business_party,
    url_get_case,
    url_get_collection_exercise,
    url_get_survey_by_short_name,
    url_get_survey_by_short_name_eq,
)

logger = wrap_logger(logging.getLogger(__name__))


@requests_mock.mock()
class TestUploadSurvey(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.set_cookie("authorization", "session_key")
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2Vy"
            + "X3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"
            # NOQA
        }
        self.survey_file = dict(file=(io.BytesIO(b"my file contents"), "testfile.xlsx"))
        self.patcher = patch("redis.StrictRedis.get", return_value=encoded_jwt_token)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    @patch("frontstage.common.authorize_access." "party_controller.is_respondent_enrolled")
    @patch("frontstage.controllers.collection_instrument_controller." "upload_collection_instrument")
    def test_upload_survey_success(
        self,
        mock_request,
        upload_collection_instrument,
        is_respondent_enrolled,
    ):
        is_respondent_enrolled.return_value = True
        upload_collection_instrument.return_value = None

        mock_request.get(
            (f"{url_get_business_party}" f"?collection_exercise_id={collection_exercise['id']}" "&verbose=True"),
            json=business_party,
            status_code=200,
        )
        mock_request.get(
            url_banner_api,
            status_code=404,
        )
        mock_request.get(
            url_get_survey_by_short_name,
            json=survey,
            status_code=200,
        )
        mock_request.get(
            url_get_case,
            json=case,
            status_code=200,
        )
        mock_request.get(
            url_get_collection_exercise,
            json=collection_exercise,
            status_code=200,
        )

        survey_file = {
            "file": (
                io.BytesIO(b"my file contents"),
                "testfile.xlsx",
            )
        }

        response = self.app.post(
            (
                "/surveys/upload-survey"
                f"?case_id={case['id']}"
                f"&business_party_id={business_party['id']}"
                f"&survey_short_name={survey['shortName']}"
            ),
            data=survey_file,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            b"testfile.xlsx",
            response.data,
        )

        is_respondent_enrolled.assert_called_once_with(
            respondent_party["id"],
            business_party["id"],
            survey["id"],
        )

        upload_collection_instrument.assert_called_once()

    @patch("frontstage.views.surveys.upload_survey.authorize_access")
    @patch("frontstage.controllers.collection_instrument_controller." "upload_collection_instrument")
    def test_upload_survey_validation_errors(
        self,
        mock_request,
        upload_collection_instrument,
        mock_authorize_access,
    ):
        mock_authorize_access.return_value = True

        mock_request.get(
            (f"{url_get_business_party}" f"?collection_exercise_id={collection_exercise['id']}" "&verbose=True"),
            json=business_party,
            status_code=200,
        )
        mock_request.get(
            url_banner_api,
            status_code=404,
        )
        mock_request.get(
            url_get_survey_by_short_name,
            json=survey,
            status_code=200,
        )
        mock_request.get(
            url_get_case,
            json=case,
            status_code=200,
        )
        mock_request.get(
            url_get_collection_exercise,
            json=collection_exercise,
            status_code=200,
        )

        validation_errors = [
            "The spreadsheet must be in .xls or .xlsx format",
            ("The file name of your spreadsheet must be " "less than 50 characters long"),
        ]
        upload_collection_instrument.return_value = validation_errors

        survey_file = {
            "file": (
                io.BytesIO(b"my file contents"),
                "testfile.xlsx",
            )
        }

        response = self.app.post(
            (
                "/surveys/upload-survey"
                f"?case_id={case['id']}"
                f"&business_party_id={business_party['id']}"
                f"&survey_short_name={survey['shortName']}"
            ),
            data=survey_file,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            b"There are 2 problems with your answer.",
            response.data,
        )
        self.assertIn(
            b"The spreadsheet must be in .xls or .xlsx format",
            response.data,
        )
        self.assertIn(
            (b"The file name of your spreadsheet must be " b"less than 50 characters long"),
            response.data,
        )

        mock_authorize_access.assert_called_once()
        upload_collection_instrument.assert_called_once()

    def test_upload_survey_missing_required_data(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.post(
            f'/surveys/upload-survey?case_id={case["id"]}' f'&survey_short_name={survey["shortName"]}',
            data=self.survey_file,
        )
        self.assertEqual(response.status_code, 400)

    @patch("frontstage.common.authorize_access." "party_controller.is_respondent_enrolled")
    @patch("frontstage.controllers.collection_instrument_controller." "upload_collection_instrument")
    def test_upload_survey_ci_upload_error(
        self,
        mock_request,
        upload_collection_instrument,
        is_respondent_enrolled,
    ):
        is_respondent_enrolled.return_value = True

        mock_request.get(
            f"{url_get_business_party}" f"?collection_exercise_id={collection_exercise['id']}" "&verbose=True",
            json=business_party,
            status_code=200,
        )

        mock_request.get(
            url_banner_api,
            status_code=404,
        )

        mock_request.get(
            url_get_survey_by_short_name,
            json=survey,
            status_code=200,
        )

        mock_request.get(
            url_get_case,
            json=case,
            status_code=200,
        )

        mock_request.get(
            url_get_collection_exercise,
            json=collection_exercise,
            status_code=200,
        )

        upload_collection_instrument.side_effect = CiUploadError("Upload failed")

        survey_file = {
            "file": (
                io.BytesIO(b"my file contents"),
                "testfile.xlsx",
            )
        }

        response = self.app.post(
            (
                "/surveys/upload-survey"
                f"?case_id={case['id']}"
                f"&business_party_id={business_party['id']}"
                f"&survey_short_name={survey['shortName']}"
            ),
            data=survey_file,
        )

        self.assertEqual(response.status_code, 200)

        self.assertIn(
            b"There is 1 error on this page",
            response.data,
        )

        self.assertIn(
            (b"The selected file could not be uploaded. " b"Please try again."),
            response.data,
        )

    @patch("frontstage.controllers.party_controller.is_respondent_enrolled")
    def test_upload_survey_no_permission(self, mock_request, is_respondent_enrolled):
        is_respondent_enrolled.return_value = False
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_survey_by_short_name, json=survey, status_code=200)
        response = self.app.post(
            f'/surveys/upload-survey?case_id={case["id"]}&business_party_id={business_party["id"]}'
            f'&survey_short_name={survey["shortName"]}'
        )
        self.assertEqual(response.status_code, 500)

    def test_upload_survey_ci_upload_with_mismatched_business_id(
        self,
        mock_request,
    ):
        mismatched_business_party_id = "f956e8ae-6e0f-4414-b0cf-a07c1aa3e37b"

        mock_request.get(
            url_banner_api,
            status_code=404,
        )

        mock_request.get(
            url_get_case,
            json=case,
            status_code=200,
        )

        mock_request.get(
            url_get_collection_exercise,
            json=collection_exercise,
            status_code=200,
        )

        mock_request.get(
            url_get_survey_by_short_name,
            json=survey,
            status_code=200,
        )

        mock_request.get(
            (f"{url_get_business_party}" f"?collection_exercise_id={collection_exercise['id']}" "&verbose=True"),
            json=business_party,
            status_code=200,
        )

        survey_file = {
            "file": (
                io.BytesIO(b"my file contents"),
                "testfile.xlsx",
            )
        }

        response = self.app.post(
            (
                "/surveys/upload-survey"
                f"?case_id={case['id']}"
                f"&business_party_id={mismatched_business_party_id}"
                f"&survey_short_name={survey['shortName']}"
            ),
            data=survey_file,
        )

        self.assertEqual(response.status_code, 400)

    @patch("frontstage.common.authorize_access.party_controller.is_respondent_enrolled")
    def test_upload_survey_ci_upload_with_mismatched_survey_id(
        self,
        mock_request,
        is_respondent_enrolled,
    ):
        is_respondent_enrolled.return_value = True
        mock_request.get(
            url_banner_api,
            status_code=404,
        )

        mock_request.get(
            url_get_case,
            json=case,
            status_code=200,
        )

        mock_request.get(
            url_get_collection_exercise,
            json=collection_exercise,
            status_code=200,
        )

        mock_request.get(
            f"{url_get_business_party}" f"?collection_exercise_id={collection_exercise['id']}" "&verbose=True",
            json=business_party,
            status_code=200,
        )

        mock_request.get(
            url_get_survey_by_short_name_eq,
            json=survey_eq,
            status_code=200,
        )

        survey_file = {
            "file": (
                io.BytesIO(b"my file contents"),
                "testfile.xlsx",
            )
        }

        response = self.app.post(
            (
                "/surveys/upload-survey"
                f"?case_id={case['id']}"
                f"&business_party_id={business_party['id']}"
                "&survey_short_name=QBS"
            ),
            data=survey_file,
        )

        print(response.status_code)
        print(response.location)
        print(response.data.decode())

        self.assertEqual(response.status_code, 400)
