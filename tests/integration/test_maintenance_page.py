import unittest

from frontstage import app


class TestMaintenancePage(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        app.config["UNDER_MAINTENANCE"] = True

    def tearDown(self):
        app.config["UNDER_MAINTENANCE"] = False

    def test_maintenance_page_redirect(self):
        response = self.app.get("/", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("This site is currently offline for maintenance.".encode() in response.data)
