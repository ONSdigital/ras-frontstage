import unittest

from werkzeug.datastructures import ImmutableMultiDict

from frontstage import app
from frontstage.models import LoginForm, ForgotPasswordForm, RegistrationForm


invalid_emails = ['email@123.123.123.123',
                  'email@[123.123.123.123]',
                  'plainaddress',
                  '@no-local-part.com',
                  'Outlook Contact <outlook-contact@domain.com>',
                  'no-at.domain.com',
                  'no-tld@domain',
                  ';beginning-semicolon@domain.co.uk',
                  'middle-semicolon@domain.co;uk',
                  'trailing-semicolon@domain.com;',
                  '"email+leading-quotes@domain.com',
                  'email+middle"-quotes@domain.com',
                  '"quoted-local-part"@domain.com',
                  '"quoted@domain.com"',
                  'lots-of-dots@domain..gov..uk',
                  'two-dots..in-local@domain.com',
                  'multiple@domains@domain.com',
                  'spaces in local@domain.com',
                  'spaces-in-domain@dom ain.com',
                  'underscores-in-domain@dom_ain.com',
                  'pipe-in-domain@example.com|gov.uk',
                  'comma,in-local@gov.uk',
                  'comma-in-domain@domain,gov.uk',
                  'pound-sign-in-local£@domain.com',
                  'local-with-’-apostrophe@domain.com',
                  'local-with-”-quotes@domain.com',
                  'domain-starts-with-a-dot@.domain.com',
                  'brackets(in)local@domain.com']


class TestModels(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    def test_invalid_email_addresses_on_login(self):
        with app.app_context():
            for email in invalid_emails:
                form = LoginForm(ImmutableMultiDict([('username', email), ('password', 'password')]))
                form.validate()

                self.assertEqual(form.errors['username'][0], 'Invalid email address')

    def test_invalid_email_addresses_on_forget_password(self):
        with app.app_context():
            for email in invalid_emails:
                form = ForgotPasswordForm(ImmutableMultiDict([('email_address', email)]))
                form.validate()

                self.assertEqual(form.errors['email_address'][0], 'Invalid email address')

    def test_invalid_email_addresses_on_registration(self):
        with app.app_context():
            for email in invalid_emails:
                form = RegistrationForm(ImmutableMultiDict([('first_name', 'Stephen'), ('last_name', 'Avery'),
                                                            ('email_address', email), ('password', 'password'),
                                                            ('password_confirm', 'password'),
                                                            ('phone_number', '01792 911911')]))
                form.validate()

                self.assertEqual(form.errors['email_address'][0], 'Invalid email address')
