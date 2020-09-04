import unittest

from config import TestingConfig
from frontstage import app
from frontstage.controllers.notify_controller import NotifyGateway
from frontstage.exceptions.exceptions import RasNotifyError


class TestNotifyController(unittest.TestCase):
    '''
    Tests that the notify controller is working as expected
    '''

    def setUp(self):
        app.testing = True
        app_config = TestingConfig()
        app.config.from_object(app_config)
        self.app = app.test_client()
        self.app_config = self.app.application.config
        self.email_form = {"email_address": "test@email.com"}

    def test_request_to_notify_with_pubsub_no_personalisation(self):
        """Tests what is sent to pubsub when no personalisation is added"""
        publisher = unittest.mock.MagicMock()
        publisher.topic_path.return_value = 'projects/test-project-id/topics/ras-rm-notify-test'
        # Given a mocked notify gateway
        notify = NotifyGateway(self.app_config)
        notify.publisher = publisher
        result = notify.request_to_notify('test@email.com')
        data = b'{"notify": {"email_address": "test@email.com", ' \
               b'"template_id": "request_password_change_id"}}'

        publisher.publish.assert_called()
        publisher.publish.assert_called_with('projects/test-project-id/topics/ras-rm-notify-test', data=data)
        self.assertIsNone(result)

    def test_a_successful_send_with_personalisation(self):
        """Tests what is sent to pubsub when personalisation is added"""
        publisher = unittest.mock.MagicMock()
        publisher.topic_path.return_value = 'projects/test-project-id/topics/ras-rm-notify-test'
        # Given a mocked notify gateway
        notify = NotifyGateway(self.app_config)
        notify.publisher = publisher
        personalisation = {"first_name": "testy", "last_name": "surname"}
        result = notify.request_to_notify('test@email.com', personalisation)
        data = b'{"notify": {"email_address": "test@email.com", "template_id": "request_password_change_id",' \
               b' "personalisation": {"first_name": "testy", "last_name": "surname"}}}'
        publisher.publish.assert_called()
        publisher.publish.assert_called_with('projects/test-project-id/topics/ras-rm-notify-test', data=data)
        self.assertIsNone(result)

    def test_request_to_notify_with_pubsub_timeout_error(self):
        """Tests if the future.result() raises a TimeoutError then the function raises a RasNotifyError"""
        future = unittest.mock.MagicMock()
        future.result.side_effect = TimeoutError("bad")
        publisher = unittest.mock.MagicMock()
        publisher.publish.return_value = future

        # Given a mocked notify gateway
        notify = NotifyGateway(self.app_config)
        notify.publisher = publisher
        with self.assertRaises(RasNotifyError):
            notify.request_to_notify('test@email.com')
