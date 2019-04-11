import unittest

from frontstage.common.validators import remove_required, InputRequired, DataRequired


class TestRemoveRequiredFunction(unittest.TestCase):
    """
    remove_required function tests
    """

    def test_should_remove_a_required_member_if_there_is_one(self):
        test_tuple = ('required', 'other', 'somethingelse')
        output = remove_required(test_tuple)

        self.assertFalse('required' in output)

    def test_should_remove_a_required_if_its_the_only_item_in_list(self):
        test_tuple = ('required')
        output = remove_required(test_tuple)

        self.assertFalse('required' in output)

    def test_should_remove_a_required_member_if_its_in_the_middle_of_the_list(self):
        test_tuple = ('otheritem', 'required', 'other', 'somethingelse')
        output = remove_required(test_tuple)

        self.assertFalse('required' in output)

    def test_should_remove_a_required_member_if_its_the_last_item_in_the_list(self):
        test_tuple = ('item', 'otheritem', 'required')
        output = remove_required(test_tuple)

        self.assertFalse('required' in output)

    def test_should_leave_tuple_unaffected_if_there_is_no_required_entry(self):
        test_tuple = ('foo', 'other', 'somethingelse')
        output = remove_required(test_tuple)

        self.assertEqual(output, test_tuple)


class TestInputRequired(unittest.TestCase):
    """
    Tests for the InputRequired class
    """

    def test_instantiated_field_should_have_no_required_attribute(self):
        inputReq = InputRequired()
        self.assertFalse('required' in inputReq.field_flags)


class TestDataRequired(unittest.TestCase):
    """
    Tests for the DataRequired class
    """

    def test_instantiated_field_should_have_no_required_attribute(self):
        inputReq = DataRequired()
        self.assertFalse('required' in inputReq.field_flags)
