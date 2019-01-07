import copy
import unittest
from frontstage.views.secure_messaging.message_get import get_msg_to


class TestMessageGet(unittest.TestCase):

    def test_get_msg_to_returns_group_if_no_internal_user(self):
        msg = {'something': 'somethings'}
        conversation = [msg, copy.deepcopy(msg), copy.deepcopy(msg)]

        to = get_msg_to(conversation)

        self.assertEqual(to, ['GROUP'])

    def test_get_msg_to_returns_newest_internal_user_if_known(self):
        msg = {'something': 'somethings'}
        first_message_with_user = {'internal_user': 'user1', 'from_internal': True}
        second_message_with_user = {'internal_user': 'user2', 'from_internal': True}

        conversation = [msg, first_message_with_user, second_message_with_user, copy.deepcopy(msg)]

        to = get_msg_to(conversation)

        self.assertEqual(to, ['user2'])
