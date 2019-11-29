import unittest
import responses

from config import TestingConfig
from frontstage import app
from frontstage.controllers.notify_controller import NotifyGateway
from frontstage.exceptions.exceptions import RasNotifyError

url_send_notify = f'{TestingConfig().RAS_NOTIFY_SERVICE_URL}{TestingConfig().RAS_NOTIFY_REQUEST_PASSWORD_CHANGE_TEMPLATE}'


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
        # self.oauth2_response = {
        #     'id': 1,
        #     'access_token': '99a81f9c-e827-448b-8fa7-d563b76137ca',
        #     'expires_in': 3600,
        #     'token_type': 'Bearer',
        #     'scope': '',
        #     'refresh_token': 'a74fd471-6981-4503-9f59-00d45d339a15'
        # }
        # self.password_form = {"password": "Gizmo007!", "password_confirm": "Gizmo007!"}

    def test_an_invalid_template_id(self):
        with app.app_context():
            with self.assertRaises(KeyError):
                NotifyGateway(self.app_config).request_to_notify(email='test@test.test',
                                                                 template_name='fake-template-name')

    def test_a_successful_send(self):
        with responses.RequestsMock() as rsps:
            with app.app_context():
                rsps.add(rsps.POST, url_send_notify, json={'emailAddress': 'test@test.test', 'id': '1234'}, status=201)
                try:
                    NotifyGateway(self.app_config).request_to_notify(email='test@test.test',
                                                                     template_name='request_password_change')
                except RasNotifyError:
                    self.fail('NotifyController didnt properly handle a 201')
                except KeyError:
                    self.fail('NotifyController couldnt find the template ID request_password_change')
            assert rsps.assert_all_requests_are_fired
            assert rsps.calls[0].request.url == 'http://notify-gateway-service/emails/request_password_change_id'

    def test_an_unsuccessful_send(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.POST, url_send_notify, json={'emailAddress': 'test@test.test'}, status=500)
            with app.app_context():
                with self.assertRaises(RasNotifyError):
                    NotifyGateway(self.app_config).request_to_notify(email='test@test.test',
                                                      template_name='request_password_change')
