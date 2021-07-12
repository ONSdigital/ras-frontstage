import unittest

from frontstage.filters.subject_filter import subject_filter


class TestFilters(unittest.TestCase):
    def test_subject_is_none(self):
        subject = subject_filter(None)

        self.assertEqual(subject, "[no subject]")

    def test_subject_is_empty(self):
        subject = subject_filter("")

        self.assertEqual(subject, "[no subject]")

    def test_subject_is_white_spaces(self):
        subject = subject_filter("  ")

        self.assertEqual(subject, "[no subject]")

    def test_subject_is_valid(self):
        subject = subject_filter("valid subject")

        self.assertEqual(subject, "valid subject")
