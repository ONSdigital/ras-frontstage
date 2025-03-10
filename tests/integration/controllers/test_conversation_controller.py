import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

import requests_mock
import responses
from requests import ConnectionError, Timeout
from werkzeug.datastructures import ImmutableMultiDict

from config import TestingConfig
from frontstage import app, jwt, redis
from frontstage.common.session import Session
from frontstage.controllers.conversation_controller import (
    IncorrectAccountAccessError,
    InvalidSecureMessagingForm,
    get_message_count_from_api,
    secure_message_enrolment_options,
    secure_message_organisation_options,
    send_secure_message,
    try_message_count_from_session,
)
from frontstage.exceptions.exceptions import ApiError, ServiceUnavailableException
from frontstage.models import SecureMessagingForm
from tests.integration.mocked_services import (
    message_count,
    url_get_conversation_count,
    url_send_message,
    url_send_message_v2_messages,
    url_send_message_v2_threads,
)

PARTY_ID = "db01929d-128c-4790-a563-8915c95931e1"
SURVEY_ID = "1e928626-14f0-4036-8922-d17baa5442da"
BUSINESS_ID = "d2da6666-58b9-4714-bcdd-4e4f023b7034"
CE_ID = "2bf53fd0-f3af-45c1-b269-c5b01c623c95"
MSG_ID = "bd4923d5-573f-4aec-a68d-5847b7b567d3"


class TestConversationController(unittest.TestCase):
    def setUp(self):
        app_config = TestingConfig()
        app.config.from_object(app_config)
        self.app = app.test_client()
        self.app_config = self.app.application.config
        self.redis = redis
        self.redis.flushall()
        with app.app_context():
            self.sm_form = SecureMessagingForm(ImmutableMultiDict([("body", "message"), ("send", "")]))
            self.sm_form.body = "message"
            self.sm_form.party_id = PARTY_ID
            self.sm_form.subject.data = "Help with my survey"
            self.sm_form.category = "SURVEY"
            self.sm_form.business_id.data = BUSINESS_ID
            self.sm_form.survey_id.data = SURVEY_ID

    @patch("frontstage.controllers.conversation_controller._create_get_conversation_headers")
    def test_get_message_count_from_api(self, headers):
        headers.return_value = {"Authorization": "token"}
        session = Session.from_party_id("id")
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                url_get_conversation_count,
                json=message_count,
                status=200,
                headers={"Authorisation": "token"},
                content_type="application/json",
            )
            with app.app_context():
                count = get_message_count_from_api(session)

                self.assertEqual(3, count)

    def test_get_message_count_from_session(self):
        session = Session.from_party_id("id")
        session.set_unread_message_total(3)
        with app.app_context():
            count = try_message_count_from_session(session)

            self.assertEqual(3, count)

    def test_get_message_count_from_session_if_persisted_by_api(self):
        session = Session.from_party_id("id")
        session.set_unread_message_total(1)

        session_key = session.session_key

        session_under_test = Session.from_session_key(session_key)
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                url_get_conversation_count,
                json=message_count,
                status=200,
                headers={"Authorisation": "token"},
                content_type="application/json",
            )
            with app.app_context():
                count = get_message_count_from_api(session_under_test)

                self.assertEqual(3, session_under_test.get_unread_message_count())
                self.assertEqual(3, count)

    @patch("frontstage.controllers.conversation_controller._create_get_conversation_headers")
    def test_get_message_count_from_api_when_expired(self, headers):
        headers.return_value = {"Authorization": "token"}
        session = Session.from_party_id("id")
        decoded = session.get_decoded_jwt()
        decoded["unread_message_count"]["refresh_in"] = (
            datetime.fromtimestamp(decoded["unread_message_count"]["refresh_in"]) - timedelta(seconds=301)
        ).timestamp()
        encoded = jwt.encode(decoded)
        session.encoded_jwt_token = encoded
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                url_get_conversation_count,
                json=message_count,
                status=200,
                headers={"Authorisation": "token"},
                content_type="application/json",
            )
            with app.app_context():
                count = try_message_count_from_session(session)

                self.assertEqual(3, count)

    @patch("frontstage.controllers.conversation_controller._create_get_conversation_headers")
    def test_get_message_count_unauthorized(self, headers):
        headers.return_value = {"Authorization": "token"}
        session = Session.from_party_id("id")
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_conversation_count, status=403)
            with app.app_context():
                with self.assertRaises(IncorrectAccountAccessError):
                    get_message_count_from_api(session)

    @patch("frontstage.controllers.conversation_controller._create_get_conversation_headers")
    def test_get_message_count_other_error_returns_0(self, headers):
        headers.return_value = {"Authorization": "token"}
        session = Session.from_party_id("id")
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_conversation_count, status=400)
            with app.app_context():
                count = get_message_count_from_api(session)

                self.assertEqual(0, count)

    @patch("frontstage.controllers.conversation_controller._create_send_message_headers")
    @requests_mock.Mocker()
    def test_send_message_v1(self, headers, request_mock):
        headers.return_value = {"Authorization": "token"}
        request_mock.post(url_send_message, json={"msg_id": MSG_ID})

        with app.app_context():
            app.config["SECURE_MESSAGE_VERSION"] = "v1"
            msg_id = send_secure_message(self.sm_form)

        self.assertEqual(msg_id, MSG_ID)

    @patch("frontstage.controllers.conversation_controller._create_send_message_headers")
    @requests_mock.Mocker()
    def test_send_message_v2(self, headers, request_mock):
        headers.return_value = {"Authorization": "token"}
        app.config["SECURE_MESSAGE_VERSION"] = "v2"
        request_mock.post(url_send_message_v2_threads, json={"id": "4bd2eb4d-8788-476a-824b-8caf826a70cd"})
        request_mock.post(url_send_message_v2_messages, json={"id": "287e264d-e330-476c-9c39-3b39eef090ae"})

        with app.app_context():
            msg_id = send_secure_message(self.sm_form)

        self.assertEqual(msg_id, "287e264d-e330-476c-9c39-3b39eef090ae")

    @patch("frontstage.controllers.conversation_controller._create_send_message_headers")
    @requests_mock.Mocker()
    def test_send_message_both(self, headers, request_mock):
        headers.return_value = {"Authorization": "token"}
        app.config["SECURE_MESSAGE_VERSION"] = "both"
        request_mock.post(url_send_message, json={"msg_id": MSG_ID})
        request_mock.post(url_send_message_v2_threads, json={"id": "4bd2eb4d-8788-476a-824b-8caf826a70cd"})
        request_mock.post(url_send_message_v2_messages, json={"id": "287e264d-e330-476c-9c39-3b39eef090ae"})

        with app.app_context():
            msg_id = send_secure_message(self.sm_form)

        self.assertEqual(msg_id, MSG_ID)

    @patch("frontstage.controllers.conversation_controller._create_send_message_headers")
    @requests_mock.Mocker()
    def test_send_message_v2_threads_timeout(self, headers, request_mock):
        headers.return_value = {"Authorization": "token"}
        app.config["SECURE_MESSAGE_VERSION"] = "v2"
        request_mock.post(url_send_message_v2_threads, exc=Timeout)

        with app.app_context():
            with self.assertRaises(ServiceUnavailableException):
                send_secure_message(self.sm_form)

    @patch("frontstage.controllers.conversation_controller._create_send_message_headers")
    @requests_mock.Mocker()
    def test_send_message_v2_threads_connection_error(self, headers, request_mock):
        headers.return_value = {"Authorization": "token"}
        app.config["SECURE_MESSAGE_VERSION"] = "v2"
        request_mock.post(url_send_message_v2_threads, exc=ConnectionError)

        with app.app_context():
            with self.assertRaises(ServiceUnavailableException):
                send_secure_message(self.sm_form)

    @patch("frontstage.controllers.conversation_controller._create_send_message_headers")
    def test_send_message_v2_threads_http_error(self, headers):
        headers.return_value = {"Authorization": "token"}
        app.config["SECURE_MESSAGE_VERSION"] = "v2"
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.POST, url_send_message_v2_threads, status=404)

            with app.app_context():
                app.config["SECURE_MESSAGE_VERSION"] = "v2"
                with self.assertRaises(ApiError):
                    send_secure_message(self.sm_form)

    @patch("frontstage.controllers.conversation_controller._create_send_message_headers")
    @requests_mock.Mocker()
    def test_send_message_v2_messages_timeout(self, headers, request_mock):
        headers.return_value = {"Authorization": "token"}
        app.config["SECURE_MESSAGE_VERSION"] = "v2"
        request_mock.post(url_send_message_v2_threads, json={"id": "4bd2eb4d-8788-476a-824b-8caf826a70cd"})
        request_mock.post(url_send_message_v2_messages, exc=Timeout)

        with app.app_context():
            with self.assertRaises(ServiceUnavailableException):
                send_secure_message(self.sm_form)

    @patch("frontstage.controllers.conversation_controller._create_send_message_headers")
    @requests_mock.Mocker()
    def test_send_message_v2_messages_connection_error(self, headers, request_mock):
        headers.return_value = {"Authorization": "token"}
        app.config["SECURE_MESSAGE_VERSION"] = "v2"
        request_mock.post(url_send_message_v2_threads, json={"id": "4bd2eb4d-8788-476a-824b-8caf826a70cd"})
        request_mock.post(url_send_message_v2_messages, exc=ConnectionError)

        with app.app_context():
            with self.assertRaises(ServiceUnavailableException):
                send_secure_message(self.sm_form)

    @patch("frontstage.controllers.conversation_controller._create_send_message_headers")
    def test_send_message_v2_messages_http_error(self, headers):
        headers.return_value = {"Authorization": "token"}
        app.config["SECURE_MESSAGE_VERSION"] = "v2"
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.POST,
                url_send_message_v2_threads,
                json={"id": "4bd2eb4d-8788-476a-824b-8caf826a70cd"},
                status=200,
                headers={"Authorisation": "token"},
                content_type="application/json",
            )
            rsps.add(rsps.POST, url_send_message_v2_messages, status=404)

            with app.app_context():
                app.config["SECURE_MESSAGE_VERSION"] = "v2"
                with self.assertRaises(ApiError):
                    send_secure_message(
                        self.sm_form,
                    )

    @patch("frontstage.controllers.conversation_controller._create_send_message_headers")
    def test_send_message_invalid_secure_message_form(self, headers):
        headers.return_value = {"Authorization": "token"}
        self.sm_form.survey_id.data = ""
        with app.app_context():

            with self.assertRaises(InvalidSecureMessagingForm):
                send_secure_message(self.sm_form)

    @patch("frontstage.controllers.conversation_controller._create_send_message_headers")
    def test_send_message_api_error(self, headers):
        headers.return_value = {"Authorization": "token"}
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.POST, url_send_message, json={"msg_id": MSG_ID}, status=500)
            with app.app_context():

                with self.assertRaises(ApiError):
                    send_secure_message(self.sm_form)

    def test_secure_message(self):
        options = secure_message_enrolment_options(self._respondent_enrolments()[0], self.sm_form)
        self.assertEqual(options, self._expected_options())

    def test_secure_message_subject_not_selected(self):
        self.sm_form.subject.data = ""
        options = secure_message_enrolment_options(self._respondent_enrolments()[0], self.sm_form)

        expected_options = self._expected_options()
        expected_options["subject"][0]["selected"] = True
        expected_options["subject"][4].pop("selected")

        self.assertEqual(options, expected_options)

    def test_secure_message_business_ordered_selection(self):
        # Given respondent enrolments
        enrolments = self._respondent_enrolments()

        # When another business is added in second spot of the list
        enrolments.append(
            {
                "business_id": "bebee450-46da-4f8b-a7a6-d4632087f2a4",
                "business_name": "Aardvark Enterprises",
                "ru_ref": "49910000015",
                "trading_as": "Trading as Aardvark Enterprises",
                "survey_details": [
                    {
                        "id": "41320b22-b425-4fba-a90e-718898f718ce",
                        "short_name": "AIFDI",
                        "long_name": "Annual Inward Foreign Direct Investment Survey",
                        "ref": "062",
                        "enrolment_status": "ENABLED",
                    }
                ],
            }
        )
        options = secure_message_organisation_options(enrolments)

        # Then the correct list of options is returned, and ordered appropriately
        self.assertEqual(
            options,
            [
                {"value": "Choose an organisation", "text": "Choose an organisation", "disabled": True, "selected": True},
                {"value": "bebee450-46da-4f8b-a7a6-d4632087f2a4", "text": "Aardvark Enterprises"},
                {"value": "bebee450-46da-4f8b-a7a6-d4632087f2a3", "text": "Test Business 1"},
            ],
        )

    @staticmethod
    def _respondent_enrolments():
        return [
            {
                "business_id": "bebee450-46da-4f8b-a7a6-d4632087f2a3",
                "business_name": "Test Business 1",
                "ru_ref": "49910000014",
                "trading_as": "Trading as Test Business 1",
                "survey_details": [
                    {
                        "id": "41320b22-b425-4fba-a90e-718898f718ce",
                        "short_name": "AIFDI",
                        "long_name": "Annual Inward Foreign Direct Investment Survey",
                        "ref": "062",
                        "enrolment_status": "ENABLED",
                    }
                ],
            }
        ]

    @staticmethod
    def _expected_options():
        return {
            "survey": [
                {"value": "Choose a survey", "text": "Choose a survey", "disabled": True},
                {
                    "value": "41320b22-b425-4fba-a90e-718898f718ce",
                    "text": "Annual Inward Foreign Direct Investment Survey",
                },
                {"value": "Not survey related", "text": "Not survey related"},
            ],
            "subject": [
                {"value": "Choose a subject", "text": "Choose a subject", "disabled": True},
                {"value": "Change business address", "text": "Change business address"},
                {"value": "Feedback", "text": "Feedback"},
                {
                    "value": "Help transferring or sharing access to a survey",
                    "text": "Help transferring or sharing access to a survey",
                },
                {"value": "Help with my survey", "text": "Help with my survey", "selected": True},
                {"value": "Something else", "text": "Something else"},
                {"value": "Technical difficulties", "text": "Technical difficulties"},
            ],
        }
