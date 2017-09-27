import requests

from behave import given, when, then
from flask import json
from tests.behavioural.features.steps.common import is_element_present_by_id, step_impl_body_too_long, step_impl_subject_too_long, \
    step_impl_subject_empty, step_impl_body_empty


@given('I go to the secure-message page')
def step_impl_go_to_secure_message_create_page(context):
    context.browser.visit('/secure-message/messages/')


@when('I click create message')
def step_impl_click_create_message(context):
    context.browser.find_by_link_text('Create a message').click()


@then('The create message page will open')
def step_impl_open_create_message_page(context):
    assert is_element_present_by_id(context, 'submit-btn')


@given('I am on the create message page')
def step_impl_visit_create_message_page(context):
    context.browser.visit('/secure-message/create-message/')


@given('I have a message to send')
def step_impl_add_text_to_subject_and_body(context):
    context.browser.find_by_id('secure-message-subject').send_keys('Test Subject')
    context.browser.find_by_id('secure-message-body').send_keys('Test Body')


@given('I have a message with non alpha characters')
def step_impl_add_non_alpha_text_to_subject_and_body(context):
    context.browser.find_by_id('secure-message-subject').send_keys('[]!@%^&*()')
    context.browser.find_by_id('secure-message-body').send_keys('"?><:}{+_')


@given('I have a message with empty fields')
def step_impl_empty_subject_and_body(context):
    step_impl_subject_empty(context)
    step_impl_body_empty(context)


@given('I have a message with an empty subject')
def step_impl_create_msg_with_empty_subject(context):
    step_impl_subject_empty(context)
    context.browser.find_by_id('secure-message-body').send_keys('Subject empty')


@given('I have a message with an empty body')
def step_impl_create_msg_empty_body(context):
    context.browser.find_by_id('secure-message-subject').send_keys('Test body empty')
    step_impl_body_empty(context)


@given('I have a message with subject too long')
def step_impl_add_text_to_subject_too_long(context):
    step_impl_subject_too_long(context)
    context.browser.find_by_id('secure-message-body').send_keys('Test')


# The subject textarea in frontstage has an auto limit of 100 characters
@given('I click send with subject too long')
def step_impl_subject_too_long_send(context):
    length = context.browser.find_by_id('subject').length()
    assert length < 101
    context.browser.find_by_id('send-message').click()


@given('I have a message with body too long')
def step_impl_add_text_to_body_too_long(context):
    context.browser.find_by_id('secure-message-subject').send_keys('Test')
    step_impl_body_too_long(context)


@given('I have a message with subject and body too long')
def step_impl_add_text_to_body_too_long(context):
    step_impl_subject_too_long(context)
    step_impl_body_too_long(context)


@when('I send a message')
def step_impl_send_a_message(context):
    context.browser.find_by_id('submit-btn').click()


@then('The confirmation sent page opens')
def step_impl_open_confirmation_page(context):
    assert is_element_present_by_id(context, 'message-sent')


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


@then('The draft saved text should appear')
def step_impl_draft_saved_text_appears(context):
    assert is_element_present_by_id(context, 'message-sent')
