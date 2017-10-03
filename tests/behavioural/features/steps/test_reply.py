import requests

from flask import json
from behave import given, when, then
from tests.behavioural.features.steps.common import maxtext10000, is_element_present_by_id


@given('I have received a message from BRES')
def step_impl_received_message_from_bres(context):
    url = 'http://localhost:5050/message/send'
    # This authorization needs to be valid for the user or the test will not work
    headers = {
        'Authorization': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJyZWZyZXNoX3Rva2VuIjoiNGE3NThlZTUtNDQ2My00ZWZjLTk4MGItOTcyYjcxMjIyN2U5IiwiYW' \
        'NjZXNzX3Rva2VuIjoiNWZhNmZkYTgtYzQ1Zi00YTE5LWEzZDYtNGMzYWUzMTI0NjMxIiwiZXhwaXJlc19hdCI6MTUwNjA3NjY1OC40ODk1OTYsInJvb' \
        'GUiOiJpbnRlcm5hbCIsInBhcnR5X2lkIjoiQlJFUyJ9.gBqxH_HgK7TRUxBtpgiI97QsHBPhfzbNdHyC8Nm8caw',
        'Content-Type': 'application/json'
    }
    message = {
        "msg_to": ["a0e833fe-8a2d-4293-903b-4b826732e079"],
        "msg_from": "BRES",
        "subject": "Test internal message",
        "body": "Test internal message",
        "thread_id": "",
        "ru_id": "f1a5e99c-8edf-489a-9c72-6cabe6c387fc",
        "collection_case": "ACollectionCase",
        "survey": "BRES"
    }
    requests.post(url, data=json.dumps(message), headers=headers)


@then('I should see a reply message')
def step_impl_see_message_from_bres(context):
    assert is_element_present_by_id(context, 'secure-message-subject')
    assert is_element_present_by_id(context, 'secure-message-body')


@then('I reply to a BRES message')
def step_impl_reply_to_bres_message(context):
    context.browser.find_by_id('secure-message-body').send_keys('I am replying to BRES')
    context.browser.find_by_id('submit-btn').click()


@then('I send an empty reply')
def step_impl_reply_to_bres_message(context):
    context.browser.find_by_id('secure-message-body').send_keys()
    context.browser.find_by_id('submit-btn').click()


@then('I should receive an empty reply error')
def step_impl_subject_and_body_error(context):
    context.browser.find_by_link_text('Please enter a message')


@then('I send a reply that\'s too long')
def step_impl_reply_to_bres_message(context):
    context.browser.find_by_id('secure-message-body').send_keys(maxtext10000)
    context.browser.find_by_id('submit-btn').click()


@then('I should receive a reply too long error')
def step_impl_subject_and_body_error(context):
    context.browser.find_by_link_text('Body field length must not be greater than 10000')
