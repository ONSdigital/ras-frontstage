import os

import requests_mock
import unittest

from frontstage import app

token = 'test_token'
url_password_change_request = app.config['RAS_PARTY_RESET_PASSWORD_REQUEST'].format(app.config['RAS_PARTY_SERVICE'])
url_verify_token = app.config['RAS_PARTY_VERIFY_PASSWORD_TOKEN'].format(app.config['RAS_PARTY_SERVICE'], token)
url_password_change = app.config['RAS_PARTY_CHANGE_PASSWORD'].format(app.config['RAS_PARTY_SERVICE'], token)


class TestPasswords(unittest.TestCase):

    def setUp(self):
        app.testing = True
        self.app = app.test_client()
        self.email_form = {"email_address": "test@email.com"}
        self.password_form = {"password": "Gizmo007!", "password_confirm": "Gizmo007!"}

    def test_forgot_password_get(self):
        response = self.app.get("passwords/forgot-password", follow_redirects=True)

        self.assertEquals(response.status_code, 200)
        self.assertTrue('reset your password'.encode() in response.data)

    @requests_mock.mock()
    def test_forgot_password_post_success(self, mock_object):
        mock_object.post(url_password_change_request, status_code=200)

        response = self.app.post("passwords/forgot-password", data=self.email_form, follow_redirects=True)

        self.assertEquals(response.status_code, 200)
        self.assertTrue('Check your email'.encode() in response.data)

    def test_forgot_password_post_no_email(self):
        self.email_form['email_address'] = ""

        response = self.app.post("passwords/forgot-password", data=self.email_form, follow_redirects=True)

        self.assertEquals(response.status_code, 200)
        self.assertTrue('Invalid email'.encode() in response.data)

    def test_forgot_password_post_invalid_email(self):
        self.email_form['email_address'] = "aaaaa"

        response = self.app.post("passwords/forgot-password", data=self.email_form, follow_redirects=True)

        self.assertEquals(response.status_code, 200)
        self.assertTrue('Invalid email'.encode() in response.data)

    @requests_mock.mock()
    def test_forgot_password_post_unrecognised_email(self, mock_object):
        mock_object.post(url_password_change_request, status_code=404)

        response = self.app.post("passwords/forgot-password", data=self.email_form, follow_redirects=True)

        self.assertEquals(response.status_code, 200)
        self.assertTrue('Invalid email'.encode() in response.data)

    @requests_mock.mock()
    def test_forgot_password_post_party_fail(self, mock_object):
        mock_object.post(url_password_change_request, status_code=500)

        response = self.app.post("passwords/forgot-password", data=self.email_form, follow_redirects=True)

        self.assertEquals(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    def test_check_email(self):
        response = self.app.post("passwords/forgot-password/check-email", follow_redirects=True)

        self.assertEquals(response.status_code, 200)
        self.assertTrue('Check your email'.encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_get_success(self, mock_object):
        mock_object.get(url_verify_token, status_code=200)

        response = self.app.get("passwords/reset-password/{}".format(token), follow_redirects=True)

        self.assertEquals(response.status_code, 200)
        self.assertTrue('Reset your password'.encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_get_expired_token(self, mock_object):
        mock_object.get(url_verify_token, status_code=409)

        response = self.app.post("passwords/reset-password/{}".format(token), follow_redirects=True)

        self.assertEquals(response.status_code, 200)
        self.assertTrue('Your link has expired'.encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_get_invalid_token(self, mock_object):
        mock_object.get(url_verify_token, status_code=404)

        response = self.app.post("passwords/reset-password/{}".format(token), follow_redirects=True)

        self.assertEquals(response.status_code, 404)
        self.assertTrue('Page not found'.encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_get_party_fail(self, mock_object):
        mock_object.get(url_verify_token, status_code=500)

        response = self.app.post("passwords/reset-password/{}".format(token), follow_redirects=True)

        self.assertEquals(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_post_success(self, mock_object):
        mock_object.get(url_verify_token, status_code=200)
        mock_object.put(url_password_change, status_code=200)
        password_form = {"password": "Gizmo007!", "password_confirm": "Gizmo007!"}

        response = self.app.post("passwords/reset-password/{}".format(token), data=password_form, follow_redirects=True)

        self.assertEquals(response.status_code, 200)
        self.assertTrue('Your password has been changed'.encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_post_different_passwords(self, mock_object):
        mock_object.get(url_verify_token, status_code=200)
        mock_object.put(url_password_change, status_code=200)
        password_form = {"password": "Gizmo008!", "password_confirm": "Gizmo007!"}

        response = self.app.post("passwords/reset-password/{}".format(token), data=password_form, follow_redirects=True)

        self.assertEquals(response.status_code, 200)
        self.assertTrue('Your passwords do not match'.encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_post_requirements_fail(self, mock_object):
        mock_object.get(url_verify_token, status_code=200)
        mock_object.put(url_password_change, status_code=200)
        password_form = {"password": "Gizmo007a", "password_confirm": "Gizmo007a"}

        response = self.app.post("passwords/reset-password/{}".format(token), data=password_form, follow_redirects=True)

        self.assertEquals(response.status_code, 200)
        self.assertTrue("Your password doesn&#39;t meet the requirements".encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_no_password(self, mock_object):
        mock_object.get(url_verify_token, status_code=200)
        mock_object.put(url_password_change, status_code=200)
        password_form = {}

        response = self.app.post("passwords/reset-password/{}".format(token), data=password_form, follow_redirects=True)

        self.assertEquals(response.status_code, 200)
        self.assertTrue("Password is required".encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_put_party_service_fail(self, mock_object):
        mock_object.get(url_verify_token, status_code=200)
        mock_object.put(url_password_change, status_code=500)
        password_form = {"password": "Gizmo007!", "password_confirm": "Gizmo007!"}

        response = self.app.post("passwords/reset-password/{}".format(token), data=password_form, follow_redirects=True)

        self.assertEquals(response.status_code, 500)
        self.assertTrue("Server error".encode() in response.data)

    def test_reset_password_confirmation(self):
        response = self.app.post("passwords/reset-password/confirmation", follow_redirects=True)

        self.assertEquals(response.status_code, 200)
        self.assertTrue('Your password has been changed'.encode() in response.data)
