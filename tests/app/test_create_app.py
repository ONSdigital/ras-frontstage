import os
import unittest

from frontstage import app
from frontstage.create_app import create_app_object


class TestCreateApp(unittest.TestCase):

    def setUp(self):
        app.testing = True
        self.app = app.test_client()
        os.environ['APP_SETTINGS'] = 'TestingConfig'

    # Check that we can initialise app and access it's config
    def test_create_app(self):
        test_app = create_app_object()

        self.assertEqual(test_app.config['REDIS_HOST'], 'localhost')

    def test_create_app_missing_environment_variable(self):
        os.environ['APP_SETTINGS'] = 'Config'

        with self.assertRaises(SystemExit):
            create_app_object()
